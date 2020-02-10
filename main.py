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
database.autocommit = True

def main():
    global update_id
    global bot = telegram.Bot(getenv('TG_TOKEN'))

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
                '/db': print_db,
                '/dbremove': db_remove,
                '/whisper': whisper}
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        if update.message and update.message.text != None:
            if update.message.text.split()[0] in commands:
                commands.get(update.message.text.split()[0])(update.message)
            else:
                update.message.reply_text(update.message.text)


def start(message):
    id = message.from_user.id
    if len(message.text.split()) > 2: # tmp to test db
        try:
            id = int(message.text.split()[1])
        except:
            message.reply_text('Error!')
            return
    reply = ''
    sql = database.cursor()
    sql.execute("SELECT nickname FROM users WHERE id = %s;", [id])
    nickname = sql.fetchone()
    if nickname != None:
        message.reply_text(f'{nickname[0]}, you are already exist in db!')
    else:
        if len(message.text.split()) > 2: # tmp to test db
            try:
                nickname = ''.join(message.text.split()[2:])[:16]
            except:
                nickname = nickname_generator(sql, 'Player')
        elif type(message.from_user.username) is str:
            nickname = message.from_user.username[:16]
        elif type(message.from_user.first_name) is str:
            nickname = message.from_user.first_name[:16]
        elif type(message.from_user.last_name) is str:
            nickname = message.from_user.last_name[:16]
        else:
            nickname = nickname_generator(sql, 'Player')
        sql.execute("SELECT nickname FROM users " +
                    "WHERE nickname = %s;", [nickname])
        if sql.fetchone() != None:
            reply += f'{nickname}, your name has already been taken.\n'
            nickname = nickname_generator(sql, nickname)
            reply += f'We will call you {nickname}.\n'
        sql.execute("INSERT INTO users (id, nickname) " +
                    "VALUES(%s, %s);", (id, nickname))
        message.reply_text(reply + f'Hello, {nickname}!')
    sql.close()


def whisper(message):
    input_text = message.text.split()[1:]
    sql = database.cursor()
    sql.execute("SELECT id FROM users " +
                "WHERE nickname = %s;", [input_text[0]])
    target = sql.fetchone()[0]
    sql.close()
    try:
        bot.send_message(chat_id=target, text=' '.join(input_text[1:]))
    except:
        message.reply_text('Error!')


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
    table = sql.fetchall()
    text = ''
    for row in table:
        text += str(row) + '\n'
    message.reply_text(text)
    sql.close()


def db_remove(message):
    sql = database.cursor()
    try:
        sql.execute("DELETE FROM users WHERE id = %s;", [message.text.split()[1]])
    except:
        message.reply_text("Error!")
    sql.close()
    print_db(message)


def nickname_generator(sql, nickname):
    counter = 0
    check_name = nickname
    while check_name != None:
        counter += 1
        if len(nickname + str(counter)) > 16:
            return nickname_generator(sql, 'Player')
        sql.execute("SELECT nickname FROM users " +
                    "WHERE nickname = %s;", [nickname + str(counter)])
        check_name = sql.fetchone()
    return nickname + str(counter)


if __name__ == '__main__':
    main()