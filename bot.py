import time
import random
import threading
import ctypes
import bisect
import copy


class NoteEvent:
    def __init__(self, time_ms, event_type, key):
        self.time_ms = time_ms
        self.event_type = event_type
        self.key = key
        self.is_hold = False
        self.note_time = time_ms


VK_MAP = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A, '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33,
    '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38,
    '9': 0x39, 'space': 0x20, 'enter': 0x0D, 'shift': 0xA0,
    'ctrl': 0xA2, 'alt': 0xA4, ';': 0xBA, '=': 0xBB, ',': 0xBC,
    '-': 0xBD, '.': 0xBE, '/': 0xBF, '`': 0xC0, '[': 0xDB,
    '\\': 0xDC, ']': 0xDD, "'": 0xDE
}

user32 = ctypes.windll.user32


def _press_key(key):
    vk = VK_MAP.get(str(key).lower(), 0)
    if not vk:
        return False
    user32.keybd_event(vk, 0, 0, 0)
    return True


def _release_key(key):
    vk = VK_MAP.get(str(key).lower(), 0)
    if not vk:
        return False
    user32.keybd_event(vk, 0, 2, 0)
    return True


class Bot:
    SUPPORTED_KEYS = set(VK_MAP.keys())

    LAYOUTS = {
        1: ['space'],
        2: ['d', 'k'],
        3: ['d', 'space', 'k'],
        4: ['d', 'f', 'j', 'k'],
        5: ['d', 'f', 'space', 'j', 'k'],
        6: ['s', 'd', 'f', 'j', 'k', 'l'],
        7: ['s', 'd', 'f', 'space', 'j', 'k', 'l'],
        8: ['s', 'd', 'f', 'g', 'j', 'k', 'l', ';'],
        9: ['s', 'd', 'f', 'g', 'space', 'h', 'j', 'k', 'l'],
        10: ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';'],
    }

    def __init__(self, logger, sound, config):
        self.logger = logger
        self.sound = sound
        self.config = config
        self.parser = None
        self.map_data = None
        self.keys = 4
        self.playing = False
        self.stop_flag = False
        self.thread = None
        self.offset = config.get('offset', 0)
        self.humanize = config.get('humanize', False)
        self.stddev = config.get('stddev', 10)
        self.tap_duration = config.get('tap_duration', 20)
        self.release_variance = config.get('release_variance', 10)
        self.tap_shortening = config.get('tap_shortening', 20)
        self.events = []
        self._note_times = []
        self._events_ready = False
        try:
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass

    def set_parser(self, parser):
        self.parser = parser

    def load_map(self, filepath):
        if not self.parser:
            self.logger.error("Parser not set")
            return False

        self.stop()
        data = self.parser.parse(filepath)
        if not data:
            return False

        self.map_data = data
        self.keys = data['keys']
        self.config.set('last_map_path', filepath)

        if data.get('special_style', False):
            self.logger.warning(f"N+1 layout: using {self.keys} columns")

        self._build_events()
        self._events_ready = True

        holds = sum(1 for n in data['hit_objects'] if n['is_hold'])
        bpm = data.get('bpm', 0)
        length_sec = data.get('length_seconds', 0)
        length_str = f"{int(length_sec // 60)}:{int(length_sec % 60):02d}"

        self.logger.info(f"Loaded: {data['artist']} - {data['title']} [{data['version']}]")
        self.logger.info(f"Mode: {self.keys}K | BPM: {bpm:.1f} | Length: {length_str}")
        self.logger.info(f"Notes: {len(data['hit_objects'])} ({holds} holds)")
        self.sound.play('load_ok')
        return True

    def _get_keys(self):
        binds = self.config.get('key_binds', {})
        layout = binds.get(str(self.keys))

        if layout and len(layout) == self.keys:
            layout = [str(k).lower() for k in layout]
            unknown = [k for k in layout if k not in self.SUPPORTED_KEYS]
            if unknown:
                self.logger.warning(f"Unknown keys in {self.keys}K binds: {unknown}. Using default layout.")
                return self.LAYOUTS.get(self.keys, self.LAYOUTS[4])
            return layout

        return self.LAYOUTS.get(self.keys, self.LAYOUTS[4])

    def _apply_mods(self, notes):
        mod_dt = self.config.get('mod_dt', False)
        mod_ht = self.config.get('mod_ht', False)
        mod_mirror = self.config.get('mod_mirror', False)
        mod_random = self.config.get('mod_random', False)

        if mod_dt:
            self.logger.info("Mod: Double Time (1.5x speed)")
            for note in notes:
                note['time'] = int(note['time'] / 1.5)
                if note['end_time'] is not None:
                    note['end_time'] = int(note['end_time'] / 1.5)

        if mod_ht:
            self.logger.info("Mod: Half Time (0.75x speed)")
            for note in notes:
                note['time'] = int(note['time'] / 0.75)
                if note['end_time'] is not None:
                    note['end_time'] = int(note['end_time'] / 0.75)

        if mod_mirror:
            self.logger.info("Mod: Mirror")
            for note in notes:
                if 0 <= note['col'] < self.keys:
                    note['col'] = (self.keys - 1) - note['col']
                else:
                    note['col'] = -1

        if mod_random:
            self.logger.info("Mod: Random")
            cols = list(range(self.keys))
            random.shuffle(cols)
            for note in notes:
                if 0 <= note['col'] < self.keys:
                    note['col'] = cols[note['col']]
                else:
                    note['col'] = -1

        return notes

    def get_active_mods_text(self):
        mods = []
        if self.config.get('mod_dt', False): mods.append('DT')
        if self.config.get('mod_ht', False): mods.append('HT')
        if self.config.get('mod_mirror', False): mods.append('Mirror')
        if self.config.get('mod_random', False): mods.append('Random')
        return ' + '.join(mods) if mods else 'None'

    def rebuild_events(self):
        if not self.map_data:
            return
        self.tap_duration = self.config.get('tap_duration', 20)
        self._build_events()
        self._events_ready = True
        self.logger.info(f"Events rebuilt. Active mods: {self.get_active_mods_text()}")

    def _build_events(self):
        self.events = []
        keys = self._get_keys()
        notes = copy.deepcopy(self.map_data['hit_objects'])
        notes = self._apply_mods(notes)

        self._note_times = sorted(n['time'] for n in notes)

        skipped = 0
        for note in notes:
            col = note['col']
            if col < 0 or col >= len(keys):
                skipped += 1
                continue

            key = keys[col]
            is_hold = note['is_hold']

            press_ev = NoteEvent(note['time'], 'press', key)
            press_ev.is_hold = is_hold
            press_ev.note_time = note['time']
            self.events.append(press_ev)

            if is_hold and note['end_time'] is not None:
                rel_ev = NoteEvent(note['end_time'], 'release', key)
                rel_ev.is_hold = True
                rel_ev.note_time = note['end_time']
                self.events.append(rel_ev)
            else:
                rel_time = note['time'] + self.tap_duration
                rel_ev = NoteEvent(rel_time, 'release', key)
                rel_ev.is_hold = False
                rel_ev.note_time = note['time']
                self.events.append(rel_ev)

        if skipped:
            self.logger.warning(f"Skipped {skipped} notes: column out of range ({len(keys)} keys)")

        self.events.sort(key=lambda e: (e.time_ms, 0 if e.event_type == 'press' else 1))

    def start(self):
        if not self.map_data:
            self.logger.error("Load a map first")
            return False
        if self.playing:
            self.logger.warning("Bot already playing")
            return False

        self.humanize = self.config.get('humanize', False)
        self.stddev = self.config.get('stddev', 10)
        self.offset = self.config.get('offset', 0)
        self.release_variance = self.config.get('release_variance', 10)
        self.tap_shortening = self.config.get('tap_shortening', 20)
        self.tap_duration = self.config.get('tap_duration', 20)

        if not self._events_ready:
            self._build_events()
            self._events_ready = True

        self.stop_flag = False
        self.playing = True
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()

        try:
            self.sound.play('start')
        except Exception:
            pass

        self.logger.info("Bot started")
        return True

    def stop(self):
        if not self.playing:
            return
        self.stop_flag = True
        keys = self._get_keys()
        for key in keys:
            try: _release_key(key)
            except: pass
        self.logger.info("Stopping...")
        self.sound.play('stop')

    def _play_loop(self):
        try:
            self._do_play()
        except Exception as e:
            self.logger.error(f"Critical error in play loop: {e}")
        finally:
            self.playing = False
            keys = self._get_keys()
            for key in keys:
                try: _release_key(key)
                except: pass

    def _compute_density(self, current_time_ms, window_ms=500):
        if not self._note_times:
            return 0.0
        half_win = window_ms / 2
        start_t = current_time_ms - half_win
        end_t = current_time_ms + half_win
        left = bisect.bisect_left(self._note_times, start_t)
        right = bisect.bisect_right(self._note_times, end_t)
        count = right - left
        return min(1.0, count / 20.0)

    def _get_humanize_params(self, density):
        current_stddev = self.stddev * (1 + density * 1.5)
        miss_threshold = max(25.0, 5 * self.stddev - density * 15)
        tap_shortening = self.tap_shortening * density * (1 + self.stddev / 20.0)
        return {'stddev': current_stddev, 'miss_threshold': miss_threshold, 'tap_shortening': tap_shortening}

    def _do_play(self):
        events = self.events
        if not events:
            return

        start_real = time.perf_counter()
        first_note_time = events[0].time_ms
        executed = 0
        missed = 0
        active_presses = {}
        unknown_keys = set()

        for event in events:
            if self.stop_flag:
                return

            target_sec = (event.time_ms - first_note_time) / 1000.0 + (self.offset / 1000.0)

            if event.event_type == 'press':
                if self.humanize:
                    density = self._compute_density(event.note_time)
                    params = self._get_humanize_params(density)
                    error = random.gauss(0, params['stddev'])
                    if abs(error) > params['miss_threshold']:
                        missed += 1
                        active_presses[event.key] = None
                        continue
                    target_sec += error / 1000.0
                active_presses[event.key] = target_sec

            elif event.event_type == 'release':
                actual_press_sec = active_presses.get(event.key)
                if actual_press_sec is None:
                    continue
                if self.humanize and not event.is_hold:
                    density = self._compute_density(event.note_time)
                    params = self._get_humanize_params(density)
                    shortened = max(15, self.tap_duration - params['tap_shortening'])
                    final_duration = max(15, shortened + random.gauss(0, 1.5))
                    release_error = random.gauss(0, self.release_variance * 0.3)
                    target_sec = max(actual_press_sec + (final_duration / 1000.0), actual_press_sec + 0.005) + (release_error / 1000.0)
                elif self.humanize and event.is_hold:
                    error = random.gauss(0, 2)
                    target_sec += max(-4, min(4, error)) / 1000.0
                else:
                    if not event.is_hold:
                        target_sec = max(actual_press_sec + (self.tap_duration / 1000.0), actual_press_sec + 0.005)
                active_presses[event.key] = None

            elapsed = time.perf_counter() - start_real
            delay = target_sec - elapsed

            if delay < -0.05:
                if event.event_type == 'press':
                    missed += 1
                    active_presses[event.key] = None
                continue

            if delay > 0:
                time.sleep(delay)

            try:
                if event.event_type == 'press':
                    ok = _press_key(event.key)
                else:
                    ok = _release_key(event.key)

                if ok:
                    executed += 1
                elif event.key not in unknown_keys:
                    self.logger.error(f"UNKNOWN KEY '{event.key}' — not in VK_MAP, skipped")
                    unknown_keys.add(event.key)
            except Exception as e:
                self.logger.error(f"Input error: {e}")

        self.logger.info(f"Map complete! Executed: {executed}, missed: {missed}")
        self.sound.play('complete')

    def cleanup(self):
        try: ctypes.windll.winmm.timeEndPeriod(1)
        except: pass