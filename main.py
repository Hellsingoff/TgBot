from os import getenv
from dotenv import load_dotenv
import logging
import signal
from asyncio import sleep, CancelledError

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode

import sql
from schedule import *
from logic import nickname_generator

bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')
game_list = ['bones']


# registration with testing arguments
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    id = message.from_user.id
    text = message.text.split()[1:]  # tmp
    if len(text) > 1 and text[0].isdigit:  # tmp to test db
        id = int(text[0])
    reply = ''
    user = sql.User.select().where(sql.User.id == id)
    if user.exists():
        await send_message(message.from_user.id, f'{user.get().nickname}, ' +
                           'you are already exist!')
    else:
        if len(text) > 1:  # tmp to test db
            nickname = ''.join(text[1:])[:16]
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
        await send_message(message.from_user.id, reply + f'Hello, {nickname}!')


# change nickname in db.
@dp.message_handler(commands=['rename'])
async def rename(message: types.Message):
    args = message.text.split()[1:]
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status != 'menu':
        await send_message(user.id, 'You can change name only in menu.')
    elif len(args) < 1:
        await send_message(user.id, 'Usage: /rename newname.')
    else:
        new_nickname = ''.join(args)[:16]
        check_name = sql.User.select().where(sql.User.nickname == new_nickname)
        if check_name.exists() or new_nickname == '':
            await send_message(user.id,
                               f'"{new_nickname}" has already been taken.')
        else:
            user.nickname = new_nickname
            user.save()
            await send_message(user.id,
                               f'OK, now we will call you {new_nickname}')


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
    for d in sql.Door.select():
        text += f'`{d.id:16} {d.game:8} {str(d.players)}/{str(d.max_players)}'
        if d.key is not None:
            text += ' pass: yes`\n'
        else:
            text += ' pass: no`\n'
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


# test remove from db
@dp.message_handler(commands=['remove'])
async def db_remove(message: types.Message):
    try:
        id_list = [int(i) for i in message.text.split()[1:]]
        for id in id_list:
            user = sql.User.select().where(sql.User.id == id)
            if user.exists():
                user.get().delete_instance()
    except ValueError:
        await message.answer('Error!')
    await print_users(message)


# create new door
@dp.message_handler(commands=['create'])
async def new_door(message: types.Message):
    args = message.text.split()[1:]
    key = None
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status != 'menu':
        await send_message(user.id, 'You are already in another game.')
        return
    elif (len_args := len(args)) < 2 or not args[0].isdigit():
        await send_message(user.id,
                           'Usage: /create maxplayers game name key(optional)')
        return
    elif (int(args[0]) < 2 or args[1] not in game_list or len(args[2]) > 16 or
          (len(args) > 3 and len(args[3]) > 16)):
        await send_message(user.id,
                           'Error!\nMax players must be more than 1.\nName ' +
                           'and key must be no more than 16 characters.')
        return
    if len_args > 3:
        key = args[3]
    if sql.Door.select().where(sql.Door.id == args[1]).exists() or \
            sql.Room.select().where(sql.Room.id == args[1]).exists():
        await send_message(user.id, 'Door\'s name has already been taken.')
    else:
        sql.Door.create(max_players=int(args[0]), game=args[1], id=args[2],
                        key=key, players=1, player_list=[user.id])
        user.status = 'door'
        user.game = args[2]
        user.save()
        text = f'/open {args[2]}'
        if key is not None:
            text += f' {key}'
        text += '\nEntrance to this room.'
        await send_message(user.id, text)


# entr in door
@dp.message_handler(commands=['open'])
async def door_open(message: types.Message):
    args = message.text.splitlines()[0].split()[1:]
    user = sql.User.get(sql.User.id == message.from_user.id)
    if len(args) == 0:
        await send_message(user.id, 'Usage: /open door key.')
    elif not sql.Door.select().where(sql.Door.id == args[0]).exists():
        await send_message(user.id, 'The door does not exist.')
    else:
        if user.status != 'menu':
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
    # else: exit game method must be here


# chat
@dp.message_handler(lambda message: len(message.text) > 0 and
                                    message.text[0] != '/' and sql.User.get(
    sql.User.id == message.from_user.id).status != 'menu')
async def chat(message: types.Message):
    user = sql.User.get(sql.User.id == message.from_user.id)
    text = f'{user.nickname}: {message.text}'
    if user.status == 'door':
        await sql.Door.get(sql.Door.id == user.game).chat(user.id, text)
    elif user.status == 'room':
        await sql.Room.get(sql.Room.id == user.game).chat(user.id, text)


# chat sticker
@dp.message_handler(content_types=['sticker'])
async def sticker(message: types.Message):
    user = sql.User.get(sql.User.id == message.from_user.id)
    if user.status == 'door':
        await sql.Door.get(sql.Door.id == user.game
                           ).sticker(user.id,
                                     user.nickname,
                                     message.sticker.file_id)
    elif user.status == 'room':
        await sql.Room.get(sql.Door.id == user.game
                           ).sticker(user.id,
                                     user.nickname,
                                     message.sticker.file_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)


# unknown command
@dp.message_handler(lambda message: len(message.text) > 0 and
                    message.text[0] == '/')
async def wut(message: types.Message):
    await message.answer('WUT?')


# delete messages
@dp.message_handler()
async def trash(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id)


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
        await send_message(84381379, 'Reboot!')  # tmp 4 test
        dp.stop_polling()
        await sleep(15)
        exit()


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
    try:
        executor.start_polling(dp)
    finally:
        log.warning('Reboot!')
        await send_message(84381379, 'Reboot!')  # tmp 4 test
        dp.stop_polling()
        await sleep(15)
        exit()