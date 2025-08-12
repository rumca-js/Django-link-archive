from sqlalchemy import and_, or_, not_, func, MetaData, Table, select

from .omnisearch import (
    SingleSymbolEvaluator,
    EquationEvaluator,
    OmniSearch,
)


class AlchemySymbolEvaluator(SingleSymbolEvaluator):
    """
    return 1 if true
    """

    def __init__(self, table, ignore_case = False):
        self.table = table
        self.ignore_case = ignore_case

    def evaluate_complex_symbol(self, symbol, condition_data):
        # TODO make todo check if symbol exists in table?
        if condition_data[1] == "==":
            if self.ignore_case:
                column = self.table.c[condition_data[0]]
                return func.lower(column) == condition_data[2].lower()
            else:
                return self.table.c[condition_data[0]] == condition_data[2]

        if condition_data[1] == "!=":
            if self.ignore_case:
                column = self.table.c[condition_data[0]]
                return func.lower(column) != condition_data[2].lower()
            else:
                return self.table.c[condition_data[0]] != condition_data[2]

        if condition_data[1] == ">":
            return self.table.c[condition_data[0]] > condition_data[2]

        if condition_data[1] == "<":
            return self.table.c[condition_data[0]] < condition_data[2]

        if condition_data[1] == ">=":
            return self.table.c[condition_data[0]] >= condition_data[2]

        if condition_data[1] == "<=":
            return self.table.c[condition_data[0]] <= condition_data[2]

        if condition_data[1] == "=":
            symbol = condition_data[2]
            symbol = symbol.replace("*", "%")

            print(condition_data[0])
            print(symbol)

            if self.ignore_case:
                return self.table.c[condition_data[0]].ilike(symbol)
            else:
                return self.table.c[condition_data[0]].like(symbol)

        raise IOError("Unsupported operator")

    def evaluate_simple_symbol(self, symbol):
        """
        TODO we could check by default if entry link == symbol, or sth
        """
        if self.ignore_case:
            symbol = symbol.replace("*", "%")
            return or_(
                self.table.c["link"].ilike(symbol),
                self.table.c["title"].ilike(symbol),
                self.table.c["description"].ilike(symbol),
            )
        else:
            symbol = symbol.replace("*", "%")
            return or_(
                self.table.c["link"].like(symbol),
                self.table.c["title"].like(symbol),
                self.table.c["description"].like(symbol),
            )


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


class AlchemyRowHandler(object):
    def handle_row(self, row):
        pass


class AlchemySearch(object):
    def __init__(self, db, search_term, row_handler=None, table=None, rows_per_page=None, page=None, ignore_case=True, order_by=None, init_conditions=None):
        self.db = db
        self.search_term = search_term

        self.alchemy_row_handler = row_handler

        self.rows_per_page = rows_per_page
        self.page = page

        self.table = table
        self.ignore_case = ignore_case
        self.order_by = order_by
        self.init_conditions = init_conditions

        self.get_destination_table()

    def search(self):
        rows = self.get_filtered_objects()

        for row in rows:
            self.alchemy_row_handler.handle_row(row)

    def get_destination_table(self):
        destination_metadata = MetaData()

        if self.table:
            self.destination_table = Table(self.table, destination_metadata, autoload_with=self.db)
        else:
            self.destination_table = Table("linkdatamodel", destination_metadata, autoload_with=self.db)

    def get_query_conditions(self):
        symbol_evaluator = AlchemySymbolEvaluator(self.destination_table, self.ignore_case)
        equation_evaluator = AlchemyEquationEvaluator(self.search_term, symbol_evaluator)

        search = OmniSearch(self.search_term, equation_evaluator=equation_evaluator)
        combined_query_conditions = search.get_combined_query()

        return combined_query_conditions

    def get_filtered_objects(self):
        combined_query_conditions = self.get_query_conditions()
        print(combined_query_conditions)

        if combined_query_conditions is not None and self.init_conditions is not None:
            combined_query_conditions = and_(combined_query_conditions, self.init_conditions)
        elif self.init_conditions is not None:
            combined_query_conditions = self.init_conditions

        rows = []
        with self.db.connect() as connection:
            if combined_query_conditions is None:
                stmt = select(self.destination_table)
            else:
                stmt = select(self.destination_table).where(combined_query_conditions)

            if self.order_by:
                stmt = stmt.order_by(*self.order_by)

            print(stmt)

            if self.rows_per_page and self.page:
                offset = (self.page - 1) * self.rows_per_page
                stmt = stmt.offset(offset).limit(self.rows_per_page)

            # Execute the query
            result = connection.execute(stmt)
            
            # Fetch all results
            rows = result.fetchall()

            return rows
