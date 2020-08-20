from schedule import send_message
from logic import roll


async def start(room):
    room.last = 'Кости ещё не брошены.\n/turn чтобы сделать бросок.'
    for counter in range(len(room.players)):
        room.waiting[counter] = True
        room.players_last.append('')
        room.stats = {f'rolls{counter}': [], f'sum{counter}': 0}
    room.round += 1
    room.save()
    return 's'


def turn(room, array_num):
    room.waiting[array_num] = False
    new_roll = roll(6)
    room.stats[f'rolls{array_num}'] += new_roll
    room.stats[f'sum{array_num}'] = sum(room.stats[f'rolls{array_num}'])
    room.last = room.names[array_num] + f' выбрасывает 🎲 {new_roll[0]}'
    room.save()
    return room.players_last
