import winsound
import threading


class SoundManager:
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('sound_enabled', True)

    def play(self, event):
        if not self.enabled:
            return
        t = threading.Thread(target=self._play, args=(event,), daemon=True)
        t.start()

    def _play(self, event):
        try:
            if event == 'start':
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif event == 'stop':
                winsound.MessageBeep(winsound.MB_OK)
            elif event == 'complete':
                self._complete_sound()
            elif event == 'error':
                winsound.MessageBeep(winsound.MB_ICONHAND)
            elif event == 'load_ok':
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def _complete_sound(self):
        import time
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            time.sleep(0.15)
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            time.sleep(0.15)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass