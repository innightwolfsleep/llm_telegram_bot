import sys
from threading import Thread
from telegram_bot_wrapper import TelegramBotWrapper


def run_server(token):
    """initiate telegram bot class

    Args:
        token: bot token. If 0 length string then token searched in telegram token file.

    """
    # create TelegramBotWrapper instance
    # by default, read parameters in telegram_config.cfg
    tg_server = TelegramBotWrapper(config_file_path="configs/telegram_config.json")
    # by default - read token from telegram_token.txt
    tg_server.run_telegram_bot(bot_token=str(token))


def setup(token):
    """setup telegram bot connection

    Args:
        token: bot token. If 0 length string then token searched in telegram token file.

    """
    Thread(target=run_server, args=(token,)).start()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        setup(sys.argv[1])
    else:
        setup("")
