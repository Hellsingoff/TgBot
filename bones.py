from schedule import send_message


class Bones:
    async def start(self, room):
        room.last = 'Кости ещё не брошены.\n'
        counter = 0
        for player in room.players:
            room.waiting[counter] = True
            room.players_last.append('/turn чтобы сделать бросок.')
            room.stats = {'rolls': [], 'sum': 0}
            await send_message(player, room.last + room.players_last[counter])