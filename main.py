from time import sleep
from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher, executor, types


load_dotenv()
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['sleep'])
async def send_welcome(message: types.Message):
    for i in range(30, 0, -1):
        if i % 10 == 0:
            await message.answer(i)
        sleep(1)
    await message.answer(0)



@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)