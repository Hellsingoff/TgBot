from random import randint
from os import getenv
from dotenv import load_dotenv
import logging
import signal
from asyncio import sleep, CancelledError

from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.types import ParseMode

import sql
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
    user = sql.User.select().where(sql.User.id == id)
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
        user = sql.User.select().where(sql.User.nickname == nickname)
        if user.exists():
            reply += f'{nickname}, your name has already been taken.\n'
            nickname = nickname_generator(nickname)
            reply += f'We will call you {nickname}.\n'
        sql.User.create(id=id, nickname=nickname)
        await send_message(message.from_user.id, reply+ f'Hello, {nickname}!')

# change nickname in db.
@dp.message_handler(commands=['rename'])
async def rename(message: types.Message):
    args = message.text.split()[1:]
    if len(args) < 1:
        await send_message(message.from_user.id, 'Usage: /rename newname.')
    else:
        new_nickname = ''.join(args)[:16]
        check_name = sql.User.select().where(sql.User.nickname == new_nickname)
        if check_name.exists() or new_nickname == '':
            await send_message(message.from_user.id,
                               f'"{new_nickname}" has already been taken.')
        else:
            user = sql.User.get(sql.User.id == message.from_user.id)
            user.nickname = new_nickname
            user.save()
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
        await send_message(message.from_user.id, f'🎲 {str(result)}')
    else:
        await message.answer(f'🎲 {str(randint(1, 6))}')

# test print users function
@dp.message_handler(commands=['users'])
async def print_users(message: types.Message):
    text = ''
    for user in sql.User.select():
        text += f'`{str(user.id):12} {user.nickname:16} {user.status}`\n'
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

# test print doors function
@dp.message_handler(commands=['doors'])
async def print_doors(message: types.Message):
    text = ''
    for door in sql.Door.select():
        text += f'`{door.id:16} {str(door.players)}/{str(door.max_players)}'+\
                                                                    ' pass: '
        if door.key != None:
            text += 'yes`\n'
        else:
            text += ' no`\n'
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

# test remove fron db
@dp.message_handler(commands=['remove'])
async def db_remove(message: types.Message):
    try:
        id_list = [int(i) for i in message.text.split()[1:]]
        for id in id_list:
            user = sql.User.select().where(sql.User.id == id)
            if user.exists():
                user.get().delete_instance()
    except:
        await message.answer('Error!')
    await print_users(message)

# this is test ROM function
@dp.message_handler(commands=['ping'])
async def ping_me(message: types.Message):
    args = message.text.split()[1:3]
    if len(args) > 1 and args[0].isdigit and args[1].isdigit:
        for i in range(int(args[0])):
            await send_message(message.from_user.id, int(args[0]) - i)
            await sleep(int(args[1]))

# create new door
@dp.message_handler(commands=['create'])
async def new_door(message: types.Message):
    args = message.text.split()[1:]
    key = None
    user = sql.User.get(sql.User.id == message.from_user.id)
    if (user.status != 'menu'):
        await send_message(user.id, 'You are already in another game.')
        return
    elif (len_args := len(args)) < 2 or not args[0].isdigit():
        await send_message(user.id, 
                          'Usage: /create maxplayers name password(optional)')
        return
    elif int(args[0]) < 2 or len(args[1]) > 16 or (len(args) > 2 and 
                                                len(args[2]) > 16):
        await send_message(user.id, 'Error!\nMax players must be more ' +
                                    'than 1.\nName and password must ' + 
                                    'be no more than 16 characters.')
        return
    if len_args > 2:
        key = args[2]
    if sql.Door.select().where(sql.Door.id == args[1]).exists():
        await send_message(user.id, 'Door\'s name has already been taken.')
    else:
        sql.Door.create(max_players=int(args[0]), id=args[1], key=key,
                        players=1, player_list=[user.id])
        user.status = 'door'
        user.game = args[1]
        user.save()
        text = f'/open {args[1]}'
        if key != None:
            text += f' {key}'
        text += '\nEntrance to this room.'
        await send_message(user.id, text)

# entr in door
@dp.message_handler(commands=['open'])
async def door_open(message: types.Message):
    args = message.text.splitlines()[0].split()[1:]
    user = sql.User.get(sql.User.id == message.from_user.id)
    if len(args) == 0:
        await send_message(user.id, 'Usage: /open gamename password.')
    elif not sql.Door.select().where(sql.Door.id == args[0]).exists():
        await send_message(user.id, 'The door does not exist.')
    else:
        if (user.status != 'menu'):
            await send_message(user.id, 'You are already in another game.')
        elif len(args) == 1:
            await sql.Door.get(sql.Door.id == args[0]).entry(user)
        else:
            await sql.Door.get(sql.Door.id == args[0]).entry(user, args[1])

# get out
@dp.message_handler(commands=['exit'])
async def user_exit(message: types.Message):
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status == 'menu':
        await send_message(message.from_user.id, 'WUT?')
        return
    elif user.status == 'door':
        await sql.Door.get(sql.Door.id == user.game).exit(user)
        await send_message(message.from_user.id, 'Done.')
    else:
        # exit game method must be here
        a = 0 # dummy

# chat
@dp.message_handler(lambda message: len(message.text) > 0 and 
                        message.text[0] != '/' and sql.User.get(
                        sql.User.id == message.from_user.id).status != 'menu')
async def chat(message: types.Message):
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status == 'door':
        await sql.Door.get(sql.Door.id == user.game).chat(user.id,
                                        f'{user.nickname}: {message.text}')
    else:
        # ingame chat method must be here
        a = 0 # dummy

# chat sticker
@dp.message_handler(lambda message: sql.User.get(
                    sql.User.id == message.from_user.id).status != 'menu',
                    content_types=['sticker'])
async def sticker(message: types.Message):
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status == 'door':
        await sql.Door.get(sql.Door.id == user.game).sticker(user.id, 
                                    user.nickname, message.sticker.file_id)
    else:
        # ingame chat method must be here
        a = 0 # dummy

# unknown command
@dp.message_handler(lambda message: len(message.text) > 0 and 
                                    message.text[0] == '/')
async def wut(message: types.Message):
    await message.answer('WUT?')

# error handler
@dp.errors_handler()
async def error_log(*args):
    log.error(f'Error handler: {args}')


# on shutdown
async def on_shutdown():
    try:
        while True:
            await sleep(120)
    except CancelledError:
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
    '''
    loop = asyncio.get_event_loop()
    waiting_sigterm = asyncio.ensure_future(on_shutdown())
    loop.add_signal_handler(signal.SIGTERM, waiting_sigterm.cancel)
    try:
        loop.run_until_complete(waiting_sigterm)
    finally:
        loop.close()
    '''
    executor.start_polling(dp)