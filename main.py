from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher, executor, types
from asyncio import sleep
import psycopg2 as psql


load_dotenv()
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)
database = psql.connect(getenv('DATABASE_URL'), sslmode='require')
database.autocommit = True


@dp.message_handler(commands=['sleep'])
async def sleeping(message: types.Message):
    for i in range(30, 0, -10):
        message.answer(i)
        await sleep(10)
    message.answer(0)


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
    sql = database.cursor()
    sql.execute("SELECT nickname FROM users WHERE id = %s;", [id])
    nickname = sql.fetchone()
    if nickname != None:
        await message.answer(f'{nickname[0]}, you are already exist in db!')
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
            nickname = await nickname_generator(sql, nickname)
            reply += f'We will call you {nickname}.\n'
        sql.execute("INSERT INTO users (id, nickname) " +
                    "VALUES(%s, %s);", (id, nickname))
        message.answer(reply + f'Hello, {nickname}!')
    sql.close()


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)