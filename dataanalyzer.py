"""
usage: dataanalyzer.py [-h] [--dir DIR] [--count] [--summary] [--find-tag find_tag] [--find find] [--find-tags] [-i]
                       [-v VERBOSITY]

Data analyzer program

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR             Directory path
  --count               Counts entries
  --summary             Displays summary
  --daily               Displays daily
  --find-tag find_tag   Find entries with a specific tag
  --find find           Find entries with text
  --show-tags           Find all available tags
  -i, --ignore-case     Ignores case
  -v VERBOSITY, --verbosity VERBOSITY
                        Verbosity level

TODO
 - datanalayze --source-url hackernews = search from particular source
 - Output formats? (md)?
 - Maybe it could produce a chart?

Scenario of operation:
 - What was said about Musk, daily
  $ --find "Musk" --title --daily

 - 2023-10-26 was DOJ hearing in which he participated, I would like see news
  $ --find "Musk" --title --date 2023-10-26
"""
import argparse
import time
from dateutil import parser
import os
import json
from rsshistory.omnisearch import SingleSymbolEvaluator, EquationEvaluator, OmniSearch
from sqlalchemy import and_, or_, not_

from sqlmodel import SqlModel


class DirReader(object):

    def __init__(self, source_files_directory, accepted_extensions = None):
        self.dir = source_files_directory
        if accepted_extensions is None:
            self.accepted_extensions = [".json"]

    def get_files(self):
        file_list = []
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                file_split = os.path.splitext(file)
                if file_split[1] in self.accepted_extensions:
                    file_list.append(os.path.join(root, file))

        file_list = sorted(file_list)
        return file_list


class EntrySymbolEvaluator(SingleSymbolEvaluator):
    """
    return 1 if true
    """

    def __init__(self, entry = None):
        self.entry = entry

    def evaluate_complex_symbol(self, symbol, condition_data):
        if condition_data[0] not in self.entry:
            print("evaluate_complex_symbol: symbol {} not in entry".format(condition_data[0]))
            return

        entry_field_value = self.entry[condition_data[0]]

        if condition_data[1] == "==":
            return entry_field_value == condition_data[2]

        if condition_data[1] == "!=":
            return entry_field_value != condition_data[2]

        if condition_data[1] == ">":
            return entry_field_value > condition_data[2]

        if condition_data[1] == "<":
            return entry_field_value < condition_data[2]

        if condition_data[1] == ">=":
            return entry_field_value >= condition_data[2]

        if condition_data[1] == "<=":
            return entry_field_value <= condition_data[2]

        if condition_data[1] == "=":
            return entry_field_value.find(condition_data[2]) >= 0

        raise IOError("Unsupported operator")

    def evaluate_simple_symbol(self, symbol):
        """
        TODO we could check by default if entry link == symbol, or sth
        """
        link = ""
        title = ""
        description = ""

        if "link" in self.entry:
            link = self.entry["link"]
        if "title" in self.entry:
            title = self.entry["title"]
        if "description" in self.entry:
            description = self.entry["description"]

        if link and link.find(symbol) >= 0:
            return True
        if title and title.find(symbol) >= 0:
            return True
        if description and description.find(symbol) >= 0:
            return True

        return False


class AlchemySymbolEvaluator(SingleSymbolEvaluator):
    """
    return 1 if true
    """

    def __init__(self, table):
        self.table = table

    def evaluate_complex_symbol(self, symbol, condition_data):
        if condition_data[0] not in self.entry:
            print("evaluate_complex_symbol: symbol {} not in entry".format(condition_data[0]))
            return

        if condition_data[1] == "==":
            return self.table.c[condition_data[0]] == condition_data[2]

        if condition_data[1] == "!=":
            return self.table.c[condition_data[0]] != condition_data[2]

        if condition_data[1] == ">":
            return self.table.c[condition_data[0]] > condition_data[2]

        if condition_data[1] == "<":
            return self.table.c[condition_data[0]] < condition_data[2]

        if condition_data[1] == ">=":
            return self.table.c[condition_data[0]] >= condition_data[2]

        if condition_data[1] == "<=":
            return self.table.c[condition_data[0]] <= condition_data[2]

        # TODO below

        if condition_data[1] == "=":
            return entry_field_value.find(condition_data[2]) >= 0

        raise IOError("Unsupported operator")

    def evaluate_simple_symbol(self, symbol):
        """
        TODO we could check by default if entry link == symbol, or sth
        """
        return or_(self.table.c["link"].like(f"%{symbol}%"),
            self.table.c["title"].like(f"%{symbol}%"),
            self.table.c["description"].like(f"%{symbol}%"))


class AlchemyEquationEvaluator(EquationEvaluator):

    def evaluate_function(self, operation_symbol, function, args0, args1):
        if function == "And":  # & sign
            return and_(args0, args1)
        elif function == "Or":  # | sign
            return or_(args0, args1)
        elif function == "Not":  # ~ sign
            return not_(args0)
        else:
            raise NotImplementedError("Not implemented function: {}".format(function))


def read_file_contents(file_path):
    with open(file_path, "r") as f:
        return f.read()

def date_from_string(string_input):
    return parser.parse(string_input)


class SearchInterface(object):

    def __init__(self, parser=None):
        self.parser = parser
        self.start_time = time.time()

        if self.parser.dir:
            reader = DirReader(self.parser.dir)
            self.files = reader.get_files()
        else:
            self.files = []

    def print_entry(self, entry):
        level = "1"
        if self.parser.args.verbosity:
            level = self.parser.args.verbosity

        if level == "1":
            print("{}".format(entry["link"]))
        elif level == "2":
            description = ""
            if "description" in entry:
                description = entry["description"]
            print("{}\n{}".format(entry["link"], description))
        elif level == "0":
            pass
        else:
            print("{}".format(entry["link"]))

    def read_file(self, afile):
        text = read_file_contents(afile)

        try:
            j = json.loads(text)

            if "links" in j:
                return j["links"]
            if "sources" in j:
                return j["sources"]

            return j
        except Exception as E:
            print("Could not read file: {}".format(afile))

    def get_time_diff(self):
        return time.time() - self.start_time

    def print_time_diff(self):
        elapsed_time_seconds = time.time() - self.start_time
        elapsed_minutes = int(elapsed_time_seconds // 60)
        elapsed_seconds = int(elapsed_time_seconds % 60)
        print(f"Time: {elapsed_minutes}:{elapsed_seconds}")


class OmniDirSearcher(SearchInterface):

    def process(self):
        self.omni = OmniSearch(self.parser.args.search, EntrySymbolEvaluator())

        reader = DirReader(source_files_directory = self.parser.dir)
        files = reader.get_files()

        for afile in files:
            entries = self.read_file(afile)
            if not entries:
                continue

            for entry in entries:
                if self.is_omni_match(entry):
                    self.print_entry(entry)

    def is_omni_match(self, entry):
        self.omni.set_symbol_evaluator(EntrySymbolEvaluator(entry))
        search = self.omni.reevaluate()
        return self.omni.get_query_result()


class StdDirSearcher(SearchInterface):

    def process(self):
        raise NotImplementedError("No condition to search")

    def print_daily_summary(self, entry, date, daily_counter):
        print("{};{}".format(date, daily_counter))

    def get_next_entry(self):
        """
        Generator
        """
        for afile in self.files:
            if not afile.endswith(".json"):
                continue

            entries = self.read_file(afile)
            if not entries:
                continue

            for entry in entries:
                if self.is_entry_found(entry):
                    yield entry

    def is_entry_found(self, entry):
        text = None

        if self.parser.args.find:
            text = self.parser.args.find
        elif self.parser.args.find_tag:
            text = self.parser.args.find_tag

        elements = []
        if self.parser.args.find:
            elements.extend(self.get_searchable_fields())
        elif self.parser.args.find_tag:
            eleemnts.append("tags")
        else:
            print("Cannot find condition to find")
            return

        ignore_case = False
        if self.parser.args.ignore_case:
            ignore_case = self.parser.args.ignore_case

        for element in elements:
            if element == "tags":
                if "tags" in entry and text in entry["tags"]:
                    if "link" in entry:
                        return entry
            if element == "title" or element == "description" or element == "link":
                if element in entry:
                    entry_text = entry[element]

                    if not entry_text:
                        continue

                    if ignore_case:
                        if entry_text.lower().find(text.lower()) >= 0:
                            if "link" in entry:
                                return entry
                    else:
                        if entry_text.find(text) >= 0:
                            if "link" in entry:
                                return entry


    def get_searchable_fields(self):
        if self.parser.args.title:
            return ["title"]

        if self.parser.args.description:
            return ["description"]

        return [
                "title",
                "link",
                "description",
                "tags",
                ]


class IndividualDirSearcher(StdDirSearcher):
    def process(self):
        total_count = 0

        if self.parser.args.summary:
            print("Entering dir:{}".format(self.parser.dir))

        for entry in self.get_next_entry():
            self.print_entry(entry)
            total_count += 1

        if self.parser.args.summary:
            print("Leaving dir:{}".format(self.parser.dir))

        if self.parser.args.summary:
            print("Finished with count:{}".format(count))


class DailyDirSearcher(StdDirSearcher):
    """
    Same as individual searcher, but provides daily summary of search
    """

    def process(self):
        if self.parser.args.summary:
            print("Entering dir:{}".format(self.parser.dir))

        total_count = 0

        current_date = None
        daily_counter = 0
        for entry in self.get_next_entry():
            date_published = date_from_string(entry["date_published"]).date()
            if date_published != current_date:
                if not (current_date == None and daily_counter == 0):
                    self.print_daily_summary(entry, current_date, daily_counter)

                current_date = date_published
                daily_counter = 0

            daily_counter += 1
            total_count += 1

        if self.parser.args.summary:
            print("Leaving dir:{}".format(self.parser.dir))

        if self.parser.args.summary:
            print("Finished with count:{}".format(total_count))



class TagsSearcher(SearchInterface):

    def process(self):
        tags = {}
        for afile in self.files:
            if not afile.endswith(".json"):
                continue

            items = self.read_file(afile)
            if not items:
                continue

            for item in items:
                if "tags" in item and len(item["tags"]) > 0:
                    for tag in item["tags"]:
                        if tag in tags:
                            tags[tag] += 1
                        else:
                            tags[tag] = 1

        for tag in tags:
            print("Tag:{} Count:{}".format(tag, tags[tag]))


class SqlLiteSearcher(SearchInterface):
    def process(self):
        model = SqlModel(self.parser.args.db)

        search_term = self.parser.args.search
        symbol_evaluator = AlchemySymbolEvaluator(model.entries)
        equation_evaluator = AlchemyEquationEvaluator(search_term, symbol_evaluator)

        search = OmniSearch(self.parser.args.search, equation_evaluator = equation_evaluator)
        combined_query_conditions = search.get_combined_query()

        rows = model.select_conditions(combined_query_conditions)
        for row in rows:
            print(row.link)


class DataAnalyzer(object):
    def __init__(self, parser):
        self.parser = parser
        self.result = None

    def process(self):
        if self.is_db_scan():
            searcher = SqlLiteSearcher(self.parser)
            searcher.process()
            searcher.print_time_diff()
        elif self.is_omni_search():
            searcher = OmniDirSearcher(self.parser)
            searcher.process()
            searcher.print_time_diff()
        elif self.parser.args.show_tags:
            tags = TagsSearcher(self.parser)
            count = tags.process()
            searcher.print_time_diff()
        elif self.is_individual_entry_search():
            searcher = IndividualDirSearcher(self.parser)
            count = searcher.process()
            searcher.print_time_diff()
        elif self.is_daily_entry_search():
            searcher = DailyDirSearcher(self.parser)
            searcher.process()
            searcher.print_time_diff()
        else:
            print("No condition to search")

    def is_omni_search(self):
        if self.parser.args.search:
            return True

    def is_individual_entry_search(self):
        if not self.parser.args.daily:
            return True
        return False

    def is_daily_entry_search(self):
        if self.parser.args.daily:
            return True
        return False

    def is_db_scan(self):
        if self.parser.args.db:
            return True

        return False


class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--dir", help="Directory to be scanned")
        self.parser.add_argument("--db", help="DB to be scanned")
        self.parser.add_argument("--search", help="Search, with syntax same as the main program / site. Slower")

        self.parser.add_argument("--find", metavar="find", help="Find entries with specified text")
        self.parser.add_argument("--summary", action="store_true", help="Displays summary at the end")
        self.parser.add_argument("--daily", action="store_true", help="Displays daily summary at the end")
        self.parser.add_argument("--find-tag", metavar="find_tag", help="Find entries with a specific tag")
        self.parser.add_argument("--show-tags", action="store_true", help="Find all available tags")

        self.parser.add_argument("--title", action="store_true", help="Find in title") # TODO change that from value-less to value?
        self.parser.add_argument("--description", action="store_true", help="Find in description")# TODO change that from value-less to value?

        self.parser.add_argument("--date", help="Specifies date in which we should search") # TODO implement
        self.parser.add_argument("--date-from", help="Specifies date in which we should search") # TODO implement
        self.parser.add_argument("--date-to", help="Specifies date in which we should search") # TODO implement

        self.parser.add_argument("--relative", action="store_true", help="All counters are against the number of all links") # TODO implement this below
        self.parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignores case")
        self.parser.add_argument("-v", "--verbosity", help="Verbosity level")
        
        self.args = self.parser.parse_args()

        if self.args.dir:
            self.dir = self.args.dir
        else:
            self.dir = None


def main():
    p = Parser()
    p.parse()

    m = DataAnalyzer(p)
    m.process()


if __name__ == "__main__":
    main()
