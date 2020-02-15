from random import randint
from os import getenv
from dotenv import load_dotenv
import logging
from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook
from asyncio import sleep
from peewee import *
from playhouse.db_url import connect


WEBHOOK_HOST = 'https://epicspellwars.herokuapp.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_HOST = 'localhost'
WEBAPP_PORT = getenv('PORT') 
load_dotenv()
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)
db = connect(getenv('DATABASE_URL'))
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')
msg_counter = 0
MSG_PER_SECOND = 28


class User(Model):
    id = IntegerField(null=False, unique=True, primary_key=True)
    nickname = CharField(null=False, unique=True, max_length=16)
    class Meta:
        database = db
        db_table = 'users'

# run on startup
async def on_startup(dp):
    log.warning('startup')
    await bot.set_webhook(WEBHOOK_URL)
    log.warning('end of startup')

# run on shutdown
async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()

# reset msg_counter every second
async def msg_counter_reset():
    global msg_counter
    while True:
        await sleep(1)
        msg_counter = 0

# safe sending mesage function
async def send_message(user_id: int, text: str):
    global msg_counter
    while msg_counter > MSG_PER_SECOND:
        log.warning('Too many msgs!')
        await sleep(0.1)
    msg_counter += 1
    try:
        await bot.send_message(user_id, text)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded." +
                                        "Sleep {e.timeout} seconds.")
        await sleep(e.timeout)
        return await send_message(user_id, text)
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.MessageIsTooLong:
        log.error(f"Target [ID:{user_id}]: msg len {len(text)}")
        start_char = 0
        while start_char <= len(text):
            await send_message(user_id, text[start_char:start_char + 4096])
            start_char += 4096
    except exceptions.NetworkError:
        log.exception(f"Target [ID:{user_id}]: NetworkError")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        return True
    return False

# registration with testing arguments
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    id = message.from_user.id
    if len(message.text.split()) > 2: # tmp to test db
        try:
            id = int(message.text.split()[1])
        except:
            message.answer('Error!')
            return
    reply = ''
    user = User.select().where(User.id == id)
    if user.exists():
        await send_message(message.from_user.id, f'{user.get().nickname}, ' +
                                             'you are already exist in db!')
    else:
        if len(message.text.split()) > 2: # tmp to test db
            try:
                nickname = ''.join(message.text.split()[2:])[:16]
            except:
                nickname = nickname_generator('Player') # end test
        elif type(message.from_user.username) is str:
            nickname = message.from_user.username[:16]
        elif type(message.from_user.first_name) is str:
            nickname = message.from_user.first_name.replace(' ', '')[:16]
        elif type(message.from_user.last_name) is str:
            nickname = message.from_user.last_name.replace(' ', '')[:16]
        else:
            nickname = nickname_generator('Player')
        user = User.select().where(User.nickname == nickname)
        if user.exists() or nickname == '':
            reply += f'{nickname}, your name has already been taken.\n'
            nickname = nickname_generator(nickname)
            reply += f'We will call you {nickname}.\n'
        User.create(id=id, nickname=nickname)
        await send_message(message.from_user.id, reply+ f'Hello, {nickname}!')

# change nickname in db.  TO DO!!!
@dp.message_handler(commands=['rename'])
async def rename(message: types.Message):
    new_name = ''.join(message.text.split()[1:])[:16]

# rework to return
@dp.message_handler(commands=['roll'])
async def roll(message: types.Message):
    await message.answer('🎲 ' + str(randint(1, 6)))

# test print SQL function
@dp.message_handler(commands=['db'])
async def print_db(message: types.Message):
    text = ''
    for user in User.select():
        text += str(user.id) + ' ' + user.nickname + '\n'
    await message.answer(text)

# test remove fron db
@dp.message_handler(commands=['remove'])
async def db_remove(message: types.Message):
    try:
        id_list = [int(i) for i in message.text.split()[1:]]
        for id in id_list:
            user = User.select().where(User.id == id)
            if user.exists():
                user.get().delete_instance()
    except:
        await message.answer('Error!')
    await print_db(message)

# echo. Test?
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)

# nickname generator
def nickname_generator(nickname):
    counter = 1
    check_name = User.select().where(User.nickname == nickname + str(counter))
    while check_name.exists():
        counter += 1
        if len(nickname + str(counter)) > 16:
            return nickname_generator('Player')
        check_name = User.select().where(User.nickname == nickname
                                                        + str(counter))
    return nickname + str(counter)


if __name__ == '__main__':
    log.warning('Main start')
    #dp.loop.create_task(msg_counter_reset())
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=False,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT)
    log.warning('Main end')