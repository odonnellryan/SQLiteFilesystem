# SQLiteFilesystem

This is a small wrapper using FUSE to basically use a SQLite database as a filesystem.

Reason this exists:

1) I wanted to try out FUSE
2) I needed something that I could write config files to, for apps such as Nginx (nothing production, just some internal management)
without writing to directories.

