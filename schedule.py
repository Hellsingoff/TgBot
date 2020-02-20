# reset msg_counter every second
async def msg_counter_reset():
    global msg_counter
    while True:
        await sleep(1)
        msg_counter = 0

# check mail
async def check_mail():
    await send_message(84381379, 'It\'s alive!') # tmp 4 test
    while True:
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
        await sleep(60)