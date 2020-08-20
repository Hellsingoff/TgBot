from os import getenv

import urllib.parse as urlparse
from peewee import *
from playhouse.postgres_ext import ArrayField, PostgresqlExtDatabase, HStoreField

from schedule import send_message, bot
import bones

urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(getenv("DATABASE_URL"))
db = PostgresqlExtDatabase(database=url.path[1:],
                           user=url.username,
                           password=url.password,
                           host=url.hostname,
                           port=url.port,
                           register_hstore=True)
games = {'bones': bones}


class User(Model):
    id = IntegerField(null=False, unique=True)
    nickname = CharField(null=False, unique=True, max_length=16)
    status = CharField(null=False, max_length=4, default='menu')
    game = CharField(max_length=16)

    class Meta:
        database = db
        db_table = 'users'


class Door(Model):
    id = CharField(null=False, unique=True, max_length=16)
    game = CharField(null=False, max_length=8)
    players = SmallIntegerField(null=False, default=0)
    max_players = SmallIntegerField(null=False)
    key = CharField(max_length=16)
    player_list = ArrayField(IntegerField)

    class Meta:
        database = db
        db_table = 'doors'

    async def entry(self, user, key=None):
        if self.players == self.max_players:
            await send_message(user.id, 'It\'s full.')
        elif user.id in self.player_list:
            await send_message(user.id, 'You are already in this room!')
        elif key != self.key:
            await send_message(user.id, 'The key did not fit.')
        else:
            self.players += 1
            self.player_list.append(user.id)
            self.save()
            if self.players < self.max_players:
                await self.say(f'{user.nickname} joined the game.\n' +
                               f'{self.players}/{self.max_players}')
                user.status = 'door'
                user.game = self.id
                user.save()
            else:
                await self.say(f'{user.nickname} joined the game.\n' +
                               'Let\'s play a game...')
                names = []
                waiting = []
                for user_id in self.player_list:
                    player = User.get(User.id == user_id)
                    player.status = 'room'
                    player.game = self.id
                    player.save()
                    names.append(player.nickname)
                    waiting.append(False)
                new_game = Room.create(id=self.id,
                                       game=self.game,
                                       players=self.player_list,
                                       names=names,
                                       waiting=waiting)
                self.delete_instance()
                await new_game.start()

    async def say(self, text):
        for player in self.player_list:
            await send_message(player, text)

    async def chat(self, id, text):
        for player in self.player_list:
            if player != id:
                await send_message(player, text)

    async def sticker(self, id, nickname, sticker):
        for player in self.player_list:
            if player != id:
                await send_message(player, f'{nickname}:')
                await bot.send_sticker(player, sticker)

    async def exit(self, user):
        self.player_list.remove(user.id)
        self.players -= 1
        self.save()
        await self.say(f'{user.nickname} left the game.\n' +
                       f'{self.players}/{self.max_players}')
        user.status = 'menu'
        user.game = None
        user.save()
        if self.players == 0:
            self.delete_instance()


class Room(Model):
    id = CharField(null=False, unique=True, max_length=16)
    game = CharField(null=False, max_length=8)
    round = SmallIntegerField(null=False, default=0)
    players = ArrayField(IntegerField)
    names = ArrayField(CharField)
    stats = HStoreField()
    waiting = ArrayField(BooleanField)
    last = TextField()
    players_last = ArrayField(TextField)

    class Meta:
        database = db
        db_table = 'rooms'

    async def start(self):
        game = games[self.game]
        verb = await game.start(self)  # Room.get(Room.id == self.id)
        if 's' in verb:            # fix this
            await self.say()       # fix this
        if 'w' in verb:            # fix this
            await self.whisper_all()  # fix this

    async def turn(self, id):
        game = games[self.game]
        game.turn(self, id)
        if True not in self.waiting:
            game.round()  # working now

    async def say(self, text=last):
        for player in self.players:
            await send_message(player, text)

    async def whisper_all(self, text=last):         #fix
        for player in self.players:         #fix
            await send_message(player, text)         #fix

    async def chat(self, id, text):
        for player in self.players:
            if player != id:
                await send_message(player, text)

    async def sticker(self, id, nickname, sticker):
        for player in self.player_list:
            if player != id:
                await send_message(player, f'{nickname}:')
                await bot.send_sticker(player, sticker)
