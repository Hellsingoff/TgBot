from os import getenv

from peewee import *
from playhouse.db_url import connect
from playhouse.postgres_ext import ArrayField

from schedule import send_message


db = connect(getenv('DATABASE_URL'))


class User(Model):
    id = IntegerField(null=False, unique=True)
    nickname = CharField(null=False, unique=True, max_length=16)
    status = CharField(null=False, max_length=4)
    game = CharField(max_length=16)
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
            if self.players != self.max_players:
                await self.say(f'{user.nickname} joined the game.\n' + 
                                f'{self.players}/{self.max_players}')
                user.status = 'door'
                user.game = self.id
                user.save()
            else:
                await self.say(f'{user.nickname} joined the game.\n' + 
                                'Let\'s play a game...')
                self.delete_instance()
                for user_id in self.player_list:  # tmp
                    player = User.get(User.id == user_id)  # tmp
                    player.status = 'menu'  # tmp
                    player.game = None  # tmp
                    player.save()  # tmp
    
    async def say(self, text):
        for player in self.player_list:
            await send_message(player, text)

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