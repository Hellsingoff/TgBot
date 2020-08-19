from random import randint


# roll
async def roll(a, b, rolls=1):
    result = []
    for n in range(rolls):
        result.append(randint(a, b))
    return result
