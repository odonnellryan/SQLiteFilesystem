from peewee import Model, TextField, SqliteDatabase, DateTimeField, IntegerField, TimeField, FloatField, BooleanField, \
    ForeignKeyField
import datetime
import pwd
import os

database = SqliteDatabase('files.db', threadlocals=True)


class File(Model):

    class Meta:
        database = database

    path = TextField(null=False, unique=True)
    target = ForeignKeyField('self', null=True)
    dir = BooleanField(null=False)
    attrs = TextField(null=False, default="{}")
    contents = TextField(null=True, unique=False)
    created = DateTimeField(null=False, default=datetime.datetime.now())
    st_mode = IntegerField(null=True)
    st_nlink = IntegerField(null=True)
    st_size = IntegerField(null=False, default=0)
    st_ctime = FloatField(null=True)
    st_mtime = FloatField(null=True)
    st_atime = FloatField(null=True)
    st_uid = IntegerField(null=False, default=os.getuid())
    st_gid = IntegerField(null=False, default=pwd.getpwnam(pwd.getpwuid(os.getuid())[0]).pw_gid)

    def is_dir(self):
        return self.dir