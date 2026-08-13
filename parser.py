import os


class OsuParser:
    def __init__(self, logger):
        self.logger = logger

    def parse(self, filepath):
        if not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            self.logger.error(f"Cannot open file: {e}")
            return None

        data = {
            'title': '',
            'artist': '',
            'creator': '',
            'version': '',
            'mode': -1,
            'circle_size': 4,
            'keys': 4,
            'special_style': False,
            'bpm': 0,
            'length_seconds': 0,
            'timing_points': [],
            'hit_objects': [],
        }

        current_section = None
        skipped_lines = 0

        try:
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    continue
                if current_section == 'General':
                    self._parse_general(line, data)
                elif current_section == 'Metadata':
                    self._parse_metadata(line, data)
                elif current_section == 'Difficulty':
                    self._parse_difficulty(line, data)
                elif current_section == 'TimingPoints':
                    self._parse_timing_point(line, data)
                elif current_section == 'HitObjects':
                    if not self._parse_hit_object(line, data):
                        skipped_lines += 1
        except Exception as e:
            self.logger.error(f"Error reading file at line {line_num}: {e}")
            return None

        if data['mode'] != 3:
            self.logger.error(f"Not an osu!mania map! Mode: {data['mode']} (need 3). Pick a mania map.")
            return None

        data['keys'] = self._effective_keys(data)
        if data['keys'] not in range(1, 11):
            self.logger.warning(f"Unusual key count: {data['keys']}. Clamping to 1..10.")
            data['keys'] = min(max(data['keys'], 1), 10)

        if data['timing_points']:
            first_tp = data['timing_points'][0]
            if first_tp['beat_length'] > 0:
                data['bpm'] = 60000 / first_tp['beat_length']

        if data['hit_objects']:
            last_note = max(n['time'] for n in data['hit_objects'])
            last_hold = max(
                (n['end_time'] for n in data['hit_objects'] if n['end_time']),
                default=0
            )
            data['length_seconds'] = max(last_note, last_hold) / 1000.0

        data['hit_objects'].sort(key=lambda x: x['time'])

        self.logger.info(f"Parsed: {data['artist']} - {data['title']} [{data['version']}]")
        self.logger.info(f"Mapper: {data['creator']} | {data['keys']}K")
        self.logger.info(f"BPM: {data['bpm']:.1f} | Length: {data['length_seconds']:.1f}s")
        self.logger.info(f"Found {len(data['hit_objects'])} hit objects")
        if skipped_lines > 0:
            self.logger.warning(f"Skipped {skipped_lines} malformed lines in HitObjects")

        return data

    def _effective_keys(self, data):
        keys = int(data['circle_size'])
        if data.get('special_style'):
            keys += 1
        return keys

    def _parse_general(self, line, data):
        if ':' not in line:
            return
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        try:
            if key == 'Mode':
                data['mode'] = int(value)
            elif key == 'SpecialStyle':
                data['special_style'] = (value == '1')
        except ValueError:
            pass

    def _parse_metadata(self, line, data):
        if ':' not in line:
            return
        key, value = line.split(':', 1)
        key = key.strip()
        if key == 'Title':
            data['title'] = value
        elif key == 'Artist':
            data['artist'] = value
        elif key == 'Creator':
            data['creator'] = value
        elif key == 'Version':
            data['version'] = value

    def _parse_difficulty(self, line, data):
        if ':' not in line:
            return
        key, value = line.split(':', 1)
        key = key.strip()
        try:
            if key == 'CircleSize':
                data['circle_size'] = float(value)
        except ValueError:
            pass

    def _parse_timing_point(self, line, data):
        parts = line.split(',')
        if len(parts) < 2:
            return
        try:
            offset = float(parts[0])
            beat_length = float(parts[1])
            if beat_length > 0:
                data['timing_points'].append({
                    'offset': offset,
                    'bpm': 60000 / beat_length,
                    'beat_length': beat_length,
                })
        except ValueError:
            pass

    def _parse_hit_object(self, line, data):
        parts = line.split(',')
        if len(parts) < 4:
            return False
        try:
            x = int(parts[0])
            time_ms = int(parts[2])
            obj_type = int(parts[3])
        except ValueError:
            return False

        if obj_type & 2 or obj_type & 8:
            return True

        keys = self._effective_keys(data)
        col = int(x * keys / 512)
        if col >= keys:
            col = keys - 1
        if col < 0:
            col = 0

        end_time = None
        if obj_type & 128:
            if len(parts) >= 6:
                try:
                    end_param = parts[5].split(':')[0]
                    end_time = int(end_param)
                    if end_time <= time_ms:
                        end_time = None
                except ValueError:
                    pass

        data['hit_objects'].append({
            'time': time_ms,
            'col': col,
            'end_time': end_time,
            'is_hold': end_time is not None,
        })
        return True