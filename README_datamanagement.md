This document provides information how data can be backed up, and restored.

To backup, and restore data use backup.py script. It can do both

# Backup

To backup using postgreSQL custom format (fastest option).

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -b -f custom
```

To backup using postgreSQL sqlite format.

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -b -f sqlite
```

Can be performed for individual workspace

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -b -f sqlite -w rsshistory

```

# Restore

Fastest option - use custom format

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -r -f custom -w rsshistory
```

Can be done with sqlite table.

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -r -f sqlite -w rsshistory
```

Append switch can be supplied to not clean table at start

```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> -r -f sqlite --append -w rsshistory
```

# Test connection
```
psql -U <db_user> -d <database_name> -p <password> -h 127.0.0.1
```

# Tools

Tables can be reindexed
```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> --reindex
```

Squences on ids can be reset
```
poetry run python backup.py -U <db_user> -d <database_name> -p <password> --sequence-update
```
