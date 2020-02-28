from sql import User

# nickname generator
def nickname_generator(nickname):
    counter = 1
    while User.select().where(User.nickname == nickname + str(counter)).exists():
        counter += 1
        if len(nickname + str(counter)) > 16:
            return nickname_generator('Player')
    return nickname + str(counter)