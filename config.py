import json
import os


class Config:
    def __init__(self, filename='config.json'):
        self.filename = filename
        self.defaults = {
            'humanize': False,
            'stddev': 10,
            'offset': 0,
            'tap_duration': 20,
            'sound_enabled': True,
            'logs_visible': False,
            'last_map_path': '',
            'recent_maps': [],
            'key_binds': {},
            'mod_dt': False,
            'mod_ht': False,
            'mod_mirror': False,
            'mod_random': False,
            'release_variance': 10,
            'tap_shortening': 20,
            'hotkeys': {
                'start': 'f6',
                'stop': 'f7',
                'humanize': 'f8'
            }
        }
        self.data = self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for key, val in self.defaults.items():
                    if key not in data:
                        data[key] = val
                if isinstance(data.get('hotkeys'), dict):
                    for hk, hv in self.defaults['hotkeys'].items():
                        if hk not in data['hotkeys']:
                            data['hotkeys'][hk] = hv
                    data['hotkeys'].pop('logs', None)
                else:
                    data['hotkeys'] = self.defaults['hotkeys'].copy()
                return data
            except Exception:
                return self.defaults.copy()
        else:
            self.save(self.defaults.copy())
            return self.defaults.copy()

    def save(self, data=None):
        if data is None:
            data = self.data
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()