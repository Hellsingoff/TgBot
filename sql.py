from peewee import *
from playhouse.db_url import connect
from os import getenv


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
    password = CharField(max_length=16)
    class Meta:
        database = db
        db_table = 'doors'