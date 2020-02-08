import logging
import telegram
import random
from telegram.error import NetworkError, Unauthorized
from time import sleep
from dotenv import load_dotenv
from os import getenv
import psycopg2 as psql

load_dotenv()
update_id = None
database = psql.connect(getenv('DATABASE_URL'), sslmode='require')

def main():
    global update_id
    bot = telegram.Bot(getenv('TG_TOKEN'))

    # get the first pending update_id, this is so we can skip over it
    # in case we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - ' \
                               '%(levelname)s - %(message)s')

    while True:
        try:
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


def echo(bot):
    global update_id
    commands = {'/start': start,
                '/rename': rename,
                '/random': random_num,
                '/whoami': whoami,
                '/db': print_db}
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        if update.message:  # bot can receive updates without messages
            if update.message.text in commands:
                commands.get(update.message.text)(update.message)
            else:
                update.message.reply_text(update.message.text)


def start(message):
    id = message.from_user.id
    sql = database.cursor()
    if sql.execute("SELECT nickname FROM users WHERE id = %s;", id) != None:
        nick = sql.execute("SELECT nickname FROM users WHERE id = %s;", id)
        message.reply_text('%s allready exists in db!', nick)
    else:
        if type(message.from_user.username) is str:
            nickname = message.from_user.username
        elif type(message.from_user.first_name) is str:
            nickname = message.from_user.first_name
        elif type(message.from_user.last_name) is str:
            nickname = message.from_user.last_name
        else:
            nickname = str(message.from_user.id)
        sql.execute("INSERT INTO users (id, nickname)" +
                    " VALUES(%s, %s);", (id, nickname))
        message.reply_text('Hello, %s!', nickname)
    sql.close()


def rename(message):
    message.reply_text('WIP...') # TO DO


def random_num(message):
    message.reply_text(random.randint(0, 10))


def whoami(message):
    userinfo = 'id: ' + str(message.from_user.id)
    if type(message.from_user.username) is str:
        userinfo += '\n' + 'Nickname: ' + message.from_user.username
    if type(message.from_user.first_name) is str:
        userinfo += '\n' + 'F.Name: ' + message.from_user.first_name
    if type(message.from_user.last_name) is str:
        userinfo += '\n' + 'L.Name: ' + message.from_user.last_name
    message.reply_text(userinfo)


def print_db(message):
    sql = database.cursor()
    sql.execute("SELECT * FROM users;")
    message.reply_text(str(sql.fetchone()))
    sql.close()


if __name__ == '__main__':
    main()