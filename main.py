import logging
import telegram
import random
from telegram.error import NetworkError, Unauthorized
from time import sleep
from dotenv import load_dotenv
from os import getenv

load_dotenv()

update_id = None


def main():
    """Run the bot."""
    global update_id
    # Telegram Bot Authorization Token
    bot = telegram.Bot(getenv('TG_TOKEN'))

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


def echo(bot):
    """Echo the message the user sent."""
    global update_id
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.message:  # your bot can receive updates without messages
            if update.message.text == '/random':
                update.message.reply_text(random.randint(0, 10))
            elif update.message.text == '/whoami':
                update.message.reply_text(str(update.message.from.id) + '\n' + 
                                              update.message.from.username + '\n' +
                                              update.message.from.first_name + '\n' +
                                              update.message.from.last_name)
            else:
                update.message.reply_text(update.message.text)


if __name__ == '__main__':
    main()