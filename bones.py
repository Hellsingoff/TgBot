from schedule import send_message
from logic import roll


async def start(room):
    room.last = 'Кости ещё не брошены.\n/turn чтобы сделать бросок.'
    counter = 0
    for player in room.players:
        room.waiting[counter] = True
        room.players_last.append('')
        room.stats = {'rolls' + str(counter): [], 'sum' + str(counter): 0}
        counter += 1
    room.round += 1
    room.save()
    return 's'


def turn(room, array_num):
    room.waiting[array_num] = False
    new_roll = roll(1, 6)
    room.stats['rolls'+str(array_num)] += new_roll
    room.stats['sum'+str(array_num)] = sum(room.stats['rolls'+str(array_num)])
    room.last = room.names[array_num] + f' выбрасывает 🎲 {new_roll[0]}'
    room.save()
    return room.players_last
