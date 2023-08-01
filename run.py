import sys
from threading import Thread
from telegram_bot_wrapper import TelegramBotWrapper


def run_server(token):
    # create TelegramBotWrapper instance
    # by default, read parameters in telegram_config.cfg
    tg_server = TelegramBotWrapper()
    # by default - read token from telegram_token.txt
    tg_server.run_telegram_bot(bot_token=str(token))


def setup(token):
    Thread(target=run_server, args=(token,)).start()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) > 1:
        setup(sys.argv[1])
    else:
        setup("")
