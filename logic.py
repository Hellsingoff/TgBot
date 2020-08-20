from random import randint


# roll
def roll(edges, rolls=1):
    result = []
    for _ in range(rolls):
        result.append(randint(1, edges))
    return result
