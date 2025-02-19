from utils.reflected import ReflectedEntryTable
from sqlalchemy import delete, create_engine, or_, text
import argparse
from pathlib import Path

def parse():
    parser = argparse.ArgumentParser(description="Data analyzer program")
    parser.add_argument("--db", help="DB to be scanned")
    parser.add_argument("--remove-non-bookmarked", action="store_true", help="remove non bookmarked")
    parser.add_argument("--remove-votes-threshold", type=int, help="remove entries below threshold")
    parser.add_argument("--integrity", action="store_true", help="update other tables")
    parser.add_argument("--truncate", help="truncates table")

    parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignores case")
    parser.add_argument("-v", "--verbosity", help="Verbosity level")
    parser.add_argument("-s", "--summary", help="Print summary")
    
    args = parser.parse_args()

    return parser, args


def main():
    parser, args = parse()

    if not Path(args.db).exists():
        print("File does not exist")
        return

    engine = create_engine("sqlite:///" + args.db)

    if args.remove_votes_threshold:
        r = ReflectedEntryTable(engine)
        table = r.get_table("linkdatamodel")

        delete_query = delete(table).where(
                or_(table.c.page_rating_votes < args.remove_votes_threshold, table.c.page_rating_votes.is_(None))
            )
        print(delete_query.compile(engine, compile_kwargs={"literal_binds": True}))

        with engine.connect() as connection:
            connection.execute(delete_query)
            connection.commit()
        r.close()

    if args.remove_non_bookmarked:
        r = ReflectedEntryTable(engine)
        table = r.get_table("linkdatamodel")

        delete_query = delete(table).where(
                or_(table.c.bookmarked == False, table.c.bookmarked.is_(None))
        )
        print(delete_query.compile(engine, compile_kwargs={"literal_binds": True}))

        with engine.connect() as connection:
            connection.execute(delete_query)
            connection.commit()

        r.close()

    if args.truncate:
        r = ReflectedEntryTable(engine)
        r.truncate_table(args.truncate)
        r.close()

    if args.integrity:
        pass

    if args.summary:
        r = ReflectedEntryTable(engine)
        r.print_summary()


main()
