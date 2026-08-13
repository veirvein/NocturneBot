import sys
import traceback


def main():
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        from config import Config
        from logger import Logger
        from sound import SoundManager
        from parser import OsuParser
        from bot import Bot
        from gui import App

        config = Config()
        logger = Logger()
        sound = SoundManager(config)

        bot = Bot(logger, sound, config)
        bot.set_parser(OsuParser(logger))

        app = QApplication(sys.argv)
        window = App(config, logger, bot, sound)
        logger.set_callback(window.append_log)

        logger.info("Nocturne! bot started")
        window.show()

        exit_code = app.exec()
        bot.cleanup()
        sys.exit(exit_code)
    except Exception as e:
        with open('crash.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        print(f"Critical error! Details in crash.log:\n{e}")
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()