from random import randint

from sql import User


# nickname generator
def nickname_generator(nickname):
    counter = 1
    while User.select().where(User.nickname == nickname + str(counter)).exists():
        counter += 1
        if len(nickname + str(counter)) > 16:
            return nickname_generator('Player')
    return nickname + str(counter)


# roll
async def roll(a, b, rolls=1):
    result = []
    for n in range(rolls):
        result.append(randint(a, b))
    return result
