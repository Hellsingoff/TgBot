from time import sleep
from dotenv import load_dotenv
from os import getenv
from aiogram import Bot, Dispatcher, executor, types


load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=getenv('TG_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['sleep'])
async def send_welcome(message: types.Message):
    for i in range(30, -1, -10):
        await message.reply(i)
        sleep(10)


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp)