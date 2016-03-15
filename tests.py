import db
from datetime import datetime
from stat import S_IFREG
time = datetime.now()
now = time.hour * 3600 + time.minute * 60 + time.second
db.File().create(path='/some_file2', dir=False, st_mode=33204, st_nlink=1,
                         st_size=0, st_ctime=now, st_mtime=now,
                         st_atime=now, contents="some contents")
