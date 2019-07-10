#!/usr/bin/python
import sqlite3
import argparse
import hashlib

DEFAULT_DB = "~/.local/share/walltag.db"


def set_tag(db, key, tag_category, tag):
    cursor = db.cursor()
    query = """
        INSERT INTO wallpapers (id, {0})
            VALUES (:key, :tag)
            ON CONFLICT(id)
                DO UPDATE SET {0} = :tag""".format(
        tag_category
    )
    cursor.execute(query, {"key": key, "tag": tag})
    cursor.close()
    db.commit()


def get_all_tags(db, key):
    cursor = db.cursor()
    query = """SELECT * FROM wallpapers WHERE ID = :key"""
    cursor.execute(query, {"key": key})
    result = cursor.fetchone()
    # For some reason column descriptions are (column_name, None * 6)
    columns = tuple(name[0] for name in cursor.description)
    cursor.close()
    return (result, columns)


def get_tag(cursor, key, tag_category):
    cursor = db.cursor()


def init_schema(db):
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wallpapers (
            id TEXT PRIMARY KEY,
            color TEXT,
            people TEXT)
        """
    )
    cursor.close()


def get_file_hash(filename):
    checksum = hashlib.md5()
    with open(filename, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            checksum.update(data)
    return checksum.hexdigest()


def resolve_key(args):
    if "key" in args:
        return args.key
    else:
        return get_file_hash(args.filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track tags for wallpapers")
    parser.add_argument("--db", default=DEFAULT_DB)
    subparser = parser.add_subparsers(prog="subcommand", dest="subcommand")

    set_parser = subparser.add_parser("set")
    key_group = set_parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--filename", "-f")
    key_group.add_argument("--key", "-k")
    set_parser.add_argument("category")
    set_parser.add_argument("tag")

    get_parser = subparser.add_parser("get")
    key_group = get_parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--filename", "-f")
    key_group.add_argument("--key", "-k")
    get_parser.add_argument("--category", default=None)

    args = parser.parse_args()
    if not "subcommand" in args:
        parser.print_help()
    else:
        db = sqlite3.connect(args.db)
        init_schema(db)
        key = resolve_key(args)
        if args.subcommand == "set":
            print(args)
            set_tag(db, key, args.category, args.tag)
            print(args.tag)
        elif args.subcommand == "get":
            print(get_all_tags(db, key))
