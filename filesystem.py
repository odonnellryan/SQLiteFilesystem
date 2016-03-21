from __future__ import with_statement
from stat import S_IFDIR, S_IFREG
import sys
import errno
from db import File
from playhouse import shortcuts
from peewee import IntegrityError
from datetime import datetime
from fuse import FUSE, FuseOSError, Operations


class Passthrough(Operations):
    def __init__(self):
        self.fd = 0
        now = self._get_now()
        try:
            # we need to create the db entry for the root
            File().create(path="/", dir=True, st_mode=(S_IFDIR | 0o0755), st_ctime=now,
                          st_mtime=now, st_atime=now, st_nlink=2)
        except IntegrityError:
            pass

    @staticmethod
    def _get_now():
        time = datetime.now()
        return time.hour * 3600 + time.minute * 60 + time.second

    def access(self, path, mode):
        file = File().select().where(File.path == path).first()
        if file is None:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        file = File().select().where(File.path == path).first()
        file.st_mode &= 0o0770000
        file.st_mode |= mode
        file.save()
        return 0

    def chown(self, path, uid, gid):
        file = File().update(st_uid=uid, st_gid=gid).where(File.path == path)
        file.execute()

    def getattr(self, path, fh=None):
        try:
            file = File().select().where(File.path == path).first()
            return shortcuts.model_to_dict(file)
        except AttributeError as e:
            raise FuseOSError(errno.ENOENT)


    def readdir(self, path, fh):
        path_length = len(path)
        directories = File().select().where(File.path != '/', File.path.startswith(path))
        dirents = ['.', '..'] + [x.path[path_length:] for x in directories]
        return dirents

    def readlink(self, path):
        return 0

    def mknod(self, path, mode, dev):
        try:
            now = self._get_now()
            File().create(path=path, dir=False, st_mode=(S_IFREG | mode), st_nlink=1,
                          st_size=0, st_ctime=now, st_mtime=now,
                          st_atime=now)
        except Exception as e:
            print(e)
            raise FuseOSError(errno.ENOENT)

    def rmdir(self, path):
        try:
            file = File().delete().where(File.path == path)
            file.execute()
        except Exception as e:
            print(e)
            return FuseOSError(errno.ENOENT)

    def mkdir(self, path, mode):
        try:
            now = self._get_now()
            File().create(path=path, dir=True, st_mode=(S_IFDIR | 0o0755), st_ctime=now,
                          st_mtime=now, st_atime=now, st_nlink=2)
            # gets the parent path and sets the st_nlink number
            path_parts = path.split("/")
            file = File().update(st_nlink=File.st_nlink + 1).where(File.path == "/".join(path_parts[:-1]))
            file.execute()
        except Exception as e:
            print(e)
            raise FuseOSError(errno.EEXIST)

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def unlink(self, path):
        try:
            file = File().delete().where(File.path == path)
            file.execute()
        except Exception as e:
            print(e)
            raise FuseOSError(errno.EEXIST)

    def symlink(self, name, target):
        try:
            now = self._get_now()
            target = File().select().where(path=target).first()
            File().create(path=name, dir=True, st_mode=(S_IFDIR | 0o0755), st_ctime=now,
                          st_mtime=now, st_atime=now, st_nlink=2, target=target)
        except Exception as e:
            print(e)
            raise FuseOSError(errno.EEXIST)

    def rename(self, old, new):
        try:
            file = File().update(path=new).where(File.path == old)
            file.execute()
        except Exception as e:
            print(e)
            raise FuseOSError(errno.EEXIST)

    def link(self, target, name):
        try:
            now = self._get_now()
            target = File().select().where(path=target).first()
            File().create(path=name, dir=True, st_mode=(S_IFDIR | 0o0755), st_ctime=now,
                          st_mtime=now, st_atime=now, st_nlink=2, target=target)
        except Exception as e:
            print(e)
            raise FuseOSError(errno.EEXIST)

    def utimens(self, path, times=None):
        now = self._get_now()
        atime, mtime = times if times else (now, now)
        file = File().update(st_atime=atime, st_mtime=mtime).where(File.path == path)
        file.execute()

    # File methods
    # ============

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def create(self, path, mode, fi=None):
        now = self._get_now()
        File().create(path=path, dir=False, st_mode=(S_IFREG | mode), st_nlink=1,
                      st_size=0, st_ctime=now, st_mtime=now,
                      st_atime=now)
        self.fd += 1
        return self.fd

    def read(self, path, length, offset, fh):
        file = File().select().where(File.path == path).first()
        if file.contents:
            return (file.contents[offset:offset + length]).encode('utf-8')
        return "".encode('utf-8')

    def write(self, path, buf, offset, fh):
        file = File().select().where(File.path == path).first()
        if file.contents is None:
            contents = buf
            buf_length = len(buf)
        else:
            text = file.contents
            contents = text[:offset] + buf.decode('utf-8')
            buf_length = len(contents)
        file.contents = contents
        file.st_size = buf_length
        file.save()
        return len(buf)

    def truncate(self, path, length, fh=None):
        file = File().select().where(File.path == path).first()
        if fh:
            file.contents = fh
            file.save()
            return 0
        if file.contents:
            file.contents = (file.contents[:length]) if len(file.contents) > length else file.contents
            file.save()
            return 0

    def flush(self, path, fh):
        return 0

    def release(self, path, fh):
        return 0

    def fsync(self, path, fdatasync, fh):
        return 0


def main(mountpoint):
    FUSE(Passthrough(), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    try:
        File().create_table()
    except Exception:
        pass
    main(sys.argv[1])
