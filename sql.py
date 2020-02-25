from peewee import *
from playhouse.db_url import connect
from playhouse.postgres_ext import ArrayField
from os import getenv
from schedule import send_message


db = connect(getenv('DATABASE_URL'))


class User(Model):
    id = IntegerField(null=False, unique=True)
    nickname = CharField(null=False, unique=True, max_length=16)
    class Meta:
        database = db
        db_table = 'users'


class Door(Model):
    id = CharField(null=False, unique=True, max_length=16)
    players = SmallIntegerField(null=False, default=0)
    max_players = SmallIntegerField(null=False)
    key = CharField(max_length=16)
    player_list = ArrayField(IntegerField)
    class Meta:
        database = db
        db_table = 'doors'
    
    async def entry(self, id, key=None):
        if self.players == self.max_players:
            await send_message(id, 'It\'s full.')
        elif id in self.player_list:
            await send_message(id, 'You are already in this room!')
        elif key != self.key:
            await send_message(id, 'The key did not fit.')
        else:
            self.players += 1
            self.player_list.append(id)
            self.save()
            player = User.get(User.id == id).nickname
            await self.say(f'{player} joined the game. ' + 
                           f'{self.players}/{self.max_players}')
    
    async def say(self, text):
        for player in self.player_list:
            await send_message(player, text)