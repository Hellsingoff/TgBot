from random import randint
from os import getenv
from dotenv import load_dotenv
import logging
import signal

from aiogram import Bot, Dispatcher, executor, types, exceptions

from sql import User
from schedule import *
from logic import nickname_generator


bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')


# registration with testing arguments
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    id = message.from_user.id
    text = message.text.split()[1:] # tmp
    if len(text) > 1: # tmp to test db
        try:
            id = int(text[0])
        except:
            message.answer('Error!')
            return
    reply = ''
    user = User.select().where(User.id == id)
    if user.exists():
        await send_message(message.from_user.id, f'{user.get().nickname}, ' +
                                             'you are already exist in db!')
    else:
        if len(text) > 1: # tmp to test db
            try:
                nickname = ''.join(text[1:])[:16]
            except:
                nickname = nickname_generator('Player') # end test
        elif type(username := message.from_user.username) is str:
            nickname = username[:16]
        elif type(f_name := message.from_user.first_name) is str:
            nickname = f_name[:16]
        elif type(l_name := message.from_user.last_name) is str:
            nickname = l_name[:16]
        else:
            nickname = nickname_generator('Player')
        user = User.select().where(User.nickname == nickname)
        if user.exists():
            reply += f'{nickname}, your name has already been taken.\n'
            nickname = nickname_generator(nickname)
            reply += f'We will call you {nickname}.\n'
        User.create(id=id, nickname=nickname)
        await send_message(message.from_user.id, reply+ f'Hello, {nickname}!')

# change nickname in db.
@dp.message_handler(commands=['rename'])
async def rename(message: types.Message):
    args = message.text.split()[1:]
    if len(args) < 1:
        await send_message(message.from_user.id, 'Usage: /rename newname.')
    else:
        new_nickname = ''.join(args)[:16]
        check_name = User.select().where(User.nickname == new_nickname)
        if check_name.exists() or new_nickname == '':
            await send_message(message.from_user.id,
                               f'"{new_nickname}" is taken.')
        else:
            row = User.get(User.id == message.from_user.id)
            row.nickname = new_nickname
            row.save()
            await send_message(message.from_user.id, 
                               f'OK, now we will call you {new_nickname}')

# rework to return
@dp.message_handler(commands=['roll'])
async def roll(message: types.Message):
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit:
        result = [0, 0, 0, 0, 0, 0]
        args[1] = int(args[1])
        while args[1] > 0:
            result[randint(0, 5)] += 1 
            args[1] -= 1
        await send_message(message.from_user.id, '🎲 '+ str(result))
    else:
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

# this test ROM function
@dp.message_handler(commands=['ping'])
async def ping_me(message: types.Message):
    args = message.text.split()[1:3]
    if args[0].isdigit and args[1].isdigit:
        for i in range(int(args[0])):
            await send_message(message.from_user.id, int(args[0]) - i)
            await sleep(int(args[1]))

# test
@dp.message_handler(lambda message: User.get(
                        User.id == message.from_user.id).nickname == 'Tomato')
async def echo(message: types.Message):
    await send_message(message.from_user.id, 'TOMATO!')

# echo
@dp.message_handler()
async def echo(message: types.Message):
    await send_message(message.from_user.id, 
                       f'{message.text}? What does "{message.text}" mean?')

# error handler
@dp.errors_handler()
async def error_log(*args):
    log.error(f'Error handler: {args}')


# on shutdown
async def shutdown():
    log.warning('Reboot!')
    await send_message(84381379, 'Reboot!') # tmp 4 test
    dp.stop_polling()
    await sleep(15)
    exit


if __name__ == '__main__':
    log.info('Start.')
    load_dotenv()
    dp.loop.create_task(check_mail(dp))
    dp.loop.create_task(msg_counter_reset())
    dp.loop.add_signal_handler(signal.SIGTERM, shutdown)
    executor.start_polling(dp)