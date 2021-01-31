#!/usr/bin/python
import argparse
import hashlib
import os
import sqlite3

DEFAULT_DB = "~/.local/share/walltag.db"
BUF_SIZE = 1024

COLORS = ["warm", "cool", "greyscale"]
PEOPLE = ["many", "few", "none"]
TIME = ["night", "day", "dawn/dusk"]
CATEGORY_VALUES = {"color": COLORS, "people": PEOPLE, "time": TIME}


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
    if result is None:
        return {}
    # For some reason column descriptions are (column_name, None * 6)
    columns = tuple(name[0] for name in cursor.description)
    cursor.close()
    return {key: value for key, value in zip(columns, result)}


def get_tag(db, key, tag_category):
    tags = get_all_tags(db, key)
    if not tag_category in tags:
        return None
    return tags[tag_category]


def cycle_tag(db, key, tag_category):
    possible_values = CATEGORY_VALUES[tag_category]
    current_value = get_tag(db, key, tag_category)
    if current_value is None or not current_value in possible_values:
        current_value = possible_values[0]
    next_value = possible_values[
        (possible_values.index(current_value) + 1) % len(possible_values)
    ]
    set_tag(db, key, tag_category, next_value)


def init_schema(db):
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wallpapers (
            id TEXT PRIMARY KEY,
            color TEXT DEFAULT warm,
            people TEXT DEFAULT many,
            time TEXT DEFAULT night)
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
    if args.key:
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

    cycle_parser = subparser.add_parser("cycle")
    key_group = cycle_parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--filename", "-f")
    key_group.add_argument("--key", "-k")
    cycle_parser.add_argument("category")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
    else:
        db = sqlite3.connect(os.path.expanduser(args.db))
        init_schema(db)
        key = resolve_key(args)
        if args.subcommand == "set":
            set_tag(db, key, args.category, args.tag)
            print(args.tag)
        elif args.subcommand == "get":
            if args.category == None:
                print(get_all_tags(db, key))
            else:
                print(get_tag(db, key, args.category))
        elif args.subcommand == "cycle":
            cycle_tag(db, key, args.category)
