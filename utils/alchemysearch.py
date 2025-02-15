from sqlalchemy import and_, or_, not_

from .omnisearch import (
    SingleSymbolEvaluator,
    EquationEvaluator,
    OmniSearch,
)
from .sqlmodel import (
    EntriesTable,
    SourcesTable,
)


class AlchemySymbolEvaluator(SingleSymbolEvaluator):
    """
    return 1 if true
    """

    def __init__(self, table):
        self.table = table

    def evaluate_complex_symbol(self, symbol, condition_data):
        # TODO make todo check if symbol exists in table?

        if condition_data[1] == "==":
            return self.table.__table__.c[condition_data[0]] == condition_data[2]

        if condition_data[1] == "!=":
            return self.table.__table__.c[condition_data[0]] != condition_data[2]

        if condition_data[1] == ">":
            return self.table.__table__.c[condition_data[0]] > condition_data[2]

        if condition_data[1] == "<":
            return self.table.__table__.c[condition_data[0]] < condition_data[2]

        if condition_data[1] == ">=":
            return self.table.__table__.c[condition_data[0]] >= condition_data[2]

        if condition_data[1] == "<=":
            return self.table.__table__.c[condition_data[0]] <= condition_data[2]

        if condition_data[1] == "=":
            symbol = condition_data[2]
            return self.table.__table__.c[condition_data[0]].like(f"%{symbol}%")

        raise IOError("Unsupported operator")

    def evaluate_simple_symbol(self, symbol):
        """
        TODO we could check by default if entry link == symbol, or sth
        """
        return or_(
            self.table.c["link"].like(f"%{symbol}%"),
            self.table.c["title"].like(f"%{symbol}%"),
            self.table.c["description"].like(f"%{symbol}%"),
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
    def __init__(self, db, search_term, row_handler=None, order_by = None, asc=False, desc=True):
        self.db = db
        self.search_term = search_term
        self.alchemy_row_handler = row_handler
        self.order_by = order_by
        self.asc = asc
        self.desc = desc

    def search(self):
        symbol_evaluator = AlchemySymbolEvaluator(EntriesTable)
        equation_evaluator = AlchemyEquationEvaluator(
            self.search_term, symbol_evaluator
        )

        search = OmniSearch(self.search_term, equation_evaluator=equation_evaluator)
        combined_query_conditions = search.get_combined_query()

        Session = self.db.get_session()

        rows = []
        with Session() as session:
            order_by_column = getattr(EntriesTable, self.order_by, None)

            if order_by_column is None:
                raise AttributeError(f"Invalid order_by column: {self.order_by}")

            # Determine sorting order based on self.asc and self.desc
            if self.asc:
                order_by_clause = order_by_column.asc()
            elif self.desc:
                order_by_clause = order_by_column.desc()
            else:
                order_by_clause = order_by_column.asc()  # Default to ascending if no direction is provided

            rows = (
                session.query(EntriesTable)
                .filter(combined_query_conditions)
                .order_by(order_by_clause)
                .all()
            )

        for key, row in enumerate(rows):
            self.alchemy_row_handler.handle_row(row)
