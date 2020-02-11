from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher, executor, types
from asyncio import sleep


load_dotenv()
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['sleep'])
async def sleeping(message: types.Message):
    for i in range(30, 0, -10):
        await message.answer(i)
        await sleep(10)
    await message.answer(0)


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)