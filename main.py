from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher, executor, types
from asyncio import sleep
from peewee import *
from playhouse.db_url import connect


load_dotenv()
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)
db = connect(getenv('DATABASE_URL'))


class User(Model):
    id = IntegerField(null=False, unique=True, primary_key=True)
    nickname = CharField(null=False, unique=True, primary_key=True,
                         max_length=16)
    class Meta:
        database = db
        db_table = users


@dp.message_handler(commands=['sleep'])
async def sleeping(message: types.Message):
    for i in range(30, 0, -10):
        await message.answer(i)
        await sleep(10)
    await message.answer(0)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    id = message.from_user.id
    if len(message.text.split()) > 2: # tmp to test db
        try:
            id = int(message.text.split()[1])
        except:
            message.reply('Error!')
            return
    reply = ''
    nickname = User.get(User.id == id).nickname
    if nickname != None:
        await message.answer(f'{nickname[0]}, you are already exist in db!')
    else:
        if len(message.text.split()) > 2: # tmp to test db
            try:
                nickname = ''.join(message.text.split()[2:])[:16]
            except:
                nickname = nickname_generator('Player')
        elif type(message.from_user.username) is str:
            nickname = message.from_user.username[:16]
        elif type(message.from_user.first_name) is str:
            nickname = message.from_user.first_name[:16]
        elif type(message.from_user.last_name) is str:
            nickname = message.from_user.last_name[:16]
        else:
            nickname = nickname_generator('Player')
        if User.get(User.nickname == nickname) != None:
            reply += f'{nickname}, your name has already been taken.\n'
            nickname = await nickname_generator(nickname)
            reply += f'We will call you {nickname}.\n'
        User.create(id=id, nickname=nickname)
        await message.answer(reply + f'Hello, {nickname}!')


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


def nickname_generator(nickname):
    counter = 0
    check_name = nickname
    while check_name != None:
        counter += 1
        if len(nickname + str(counter)) > 16:
            return nickname_generator('Player')
        check_name = User.get(User.nickname == nickname).nickname
    return nickname + str(counter)


if __name__ == '__main__':
    executor.start_polling(dp)