# NocturneBot - Osu! Mania Auto-play Bot

Automated bot for Osu! Mania with auto-play features, humanization, and support for various mods.

## ⚠️ Important Warning

**Using this software may result in a ban of your Osu! account.** Use at your own risk. It is recommended to use it on secondary accounts or for educational purposes only.

This bot was designed **exclusively for video showcases and demonstrations**. It was **never intended to be used as a cheat** in actual gameplay. The developers assume no responsibility for any consequences arising from the misuse of this software. By using this bot, you acknowledge that all liability rests solely with you.

Please review the official [Osu! Rules](https://osu.ppy.sh/wiki/en/Rules) before proceeding.

## 🎯 Features

- **Auto-play**: Automatic map completion in Osu! Mania mode
- **Humanization**: Simulates human play with adjustable delays and variability
- **Mod Support**: HD, HR, EZ, and other mods
- **GUI Interface**: User-friendly graphical interface for control
- **Logging**: Detailed logs for debugging
- **EXE Build**: Capability to create a standalone executable file

## 📋 Requirements

- **OS**: Windows 10/11 (Linux/Mac not supported)
- **Python**: 3.8 or higher
- **Osu!**: Installed Osu! game with Mania mode

### Python Dependencies

```bash
pip install pyautogui pillow numpy pyinstaller
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/veirvein/NocturneBot.git
cd NocturneBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python main.py
```

## ⚙️ Configuration

Settings are located in the `config.json` file (created automatically on first launch):

```json
{
    "delay_min": 10,
    "delay_max": 30,
    "humanize": true,
    "auto_play": true,
    "mods": ["HD"],
    "log_level": "INFO"
}
```

### Configuration Parameters

| Parameter | Description | Default |
|----------|----------|--------------|
| `delay_min` | Minimum delay between key presses (ms) | 10 |
| `delay_max` | Maximum delay between key presses (ms) | 30 |
| `humanize` | Enable humanization (human simulation) | true |
| `auto_play` | Enable auto-play | true |
| `mods` | List of mods to use | ["HD"] |
| `log_level` | Logging level | "INFO" |

## 🎮 Usage

1. Launch Osu! and switch to Mania mode
2. Start the bot: `python main.py`
3. Select a map to play
4. The bot will automatically start playing

### Hotkeys

- **F1**: Start/Stop auto-play
- **F2**: Toggle humanization mode
- **F3**: Emergency stop

## 📦 Building EXE

To create a Windows executable file:

```bash
pyinstaller --onefile --windowed main.py --name NocturneBot
```

Or use the ready-made spec file:
```bash
pyinstaller osu_mania_bot.spec
```

The built file will appear in the `dist/` folder.

## 🗂️ Project Structure

```
NocturneBot/
├── main.py              # Application entry point. Initializes and launches the GUI and main bot loop.
├── bot.py               # Core bot logic. Handles screen analysis, note detection, and input simulation (key presses).
├── gui.py               # Graphical User Interface. Renders the control panel, settings, and status display.
├── config.py            # Configuration management. Loads, saves, and validates settings from config.json.
├── parser.py            # Game state parser. Analyzes the game screen to identify notes, timing, and score.
├── sound.py             # Sound effects module. Plays audio cues for events like hits or errors.
├── logger.py            # Logging system. Records application events, errors, and debug information to files.
├── fonts/               # Directory containing font files (.ttf) used by the GUI for text rendering.
├── config.json          # Configuration file storing user preferences and bot settings.
├── requirements.txt     # List of Python package dependencies required to run the project.
└── README.md            # Project documentation file (this file).
```

## 🔧 Troubleshooting

### High Latency
- Close unnecessary applications
- Reduce graphics settings in Osu!
- Check `delay_min` and `delay_max` in the config

### EXE Build Errors
- Ensure all dependencies are installed
- Verify all project files are present
- Try rebuilding with the `--clean` flag

---
**Remember**: Use this software responsibly and respect the Osu! community rules.