import os
import datetime


class Logger:
    def __init__(self, logs_dir='logs'):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self.callback = None
        self.current_file = None
        self._cleanup_old_logs()
        self._open_file()

    def _open_file(self):
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.current_file = os.path.join(self.logs_dir, f'nocturne_{date_str}.log')

    def _cleanup_old_logs(self, max_age_days=14):
        try:
            now = datetime.datetime.now()
            for fname in os.listdir(self.logs_dir):
                if not fname.endswith('.log'):
                    continue
                fpath = os.path.join(self.logs_dir, fname)
                try:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
                    if (now - mtime).days > max_age_days:
                        os.remove(fpath)
                except Exception:
                    pass
        except Exception:
            pass

    def set_callback(self, callback):
        self.callback = callback

    def log(self, level, msg):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] {level.upper():5} → {msg}"
        try:
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(formatted + '\n')
        except Exception:
            pass
        if self.callback:
            try:
                self.callback(formatted)
            except Exception:
                pass

    def info(self, msg):
        self.log('INFO', msg)

    def debug(self, msg):
        self.log('DEBUG', msg)

    def warning(self, msg):
        self.log('WARNING', msg)

    def error(self, msg):
        self.log('ERROR', msg)