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