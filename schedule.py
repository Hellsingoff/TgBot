import email
import poplib
from os import getenv
import logging

from asyncio import sleep
from aiogram import exceptions


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')
mailbox = getenv('MAILBOX')
password = getenv('PASSWORD')
msg_counter = 0
MSG_PER_SECOND = 28
default_bot = 0

def schedule_init(bot):
    global default_bot
    default_bot = bot

# reset msg_counter every second
async def msg_counter_reset():
    global msg_counter
    while True:
        await sleep(1)
        msg_counter = 0


# check mail
async def check_mail(dp):
    await send_message(84381379, 'It\'s alive!') # tmp 4 test
    while True:
        try:
            pop3server = poplib.POP3_SSL('pop.gmail.com')
            pop3server.user(mailbox)
            pop3server.pass_(password)
            pop3info = pop3server.stat()
            mailcount = pop3info[0]
            text = ''
            for i in range(mailcount):
                for message in pop3server.retr(i+1)[1]:
                    msg = email.message_from_bytes(message)
                    text += msg.get_payload() + '\n'
            if text.find('DATABASE_URL on epicspellwars requires maintenance')>-1:
                log.warning('Maintenance!')
                await send_message(84381379, 'Maintenance!') # tmp 4 test
                dp.stop_polling()
            pop3server.quit()
        except:
            log.error('Mail error')
        await sleep(61)


# safe sending mesage function
async def send_message(user_id: int, text: str, bot=default_bot):
    global msg_counter
    while msg_counter > MSG_PER_SECOND:
        log.warning('Too many msgs!')
        await sleep(0.1)
    msg_counter += 1
    try:
        await bot.send_message(user_id, text)
    except exceptions.BotBlocked:
        log.exception(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.exception(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.exception(f"Target [ID:{user_id}]: Flood limit is exceeded." +
                                        "Sleep {e.timeout} seconds.")
        await sleep(e.timeout)
        return await send_message(user_id, text)
    except exceptions.UserDeactivated:
        log.exception(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.MessageIsTooLong:
        log.exception(f"Target [ID:{user_id}]: msg len {len(text)}")
        start_char = 0
        while start_char <= len(text):
            await send_message(user_id, text[start_char:start_char + 4096])
            start_char += 4096
    except exceptions.NetworkError:
        log.exception(f"Target [ID:{user_id}]: NetworkError")
        await sleep(1)
        return await send_message(user_id, text[:4096])
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        return True
    return False