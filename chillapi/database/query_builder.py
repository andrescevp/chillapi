import operator
from typing import List

from pypika import functions as fn, Order, Parameter, Query, Table, Tables

sql_operators = {
    "=": operator.eq,
    "!=": operator.ne,
    "<>": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<=": operator.le,
    "<": operator.lt,
    "like": "like",
    "isnotnull": "isnotnull",
    "isnull": "isnull",
}


def create_select_paginated_query(table, columns: List[str], filters: dict):
    """

    :param table:
    :param columns: List[str]:
    :param filters: dict:

    """
    table = Table(table)
    table_columns = [table[c] for c in columns]
    query = (
        Query.from_(table)
        .select(*table_columns)
        .orderby(*filters["order"]["field"], order=Order[filters["order"]["direction"]])
        .limit(filters["size"]["limit"])
        .offset(filters["size"]["offset"])
    )

    query = set_query_filters(filters, query, table)

    return query.get_sql()


def create_select_filtered_paginated_ordered_query(table, columns: List[str], filters: dict):
    """

    :param table:
    :param columns: List[str]:
    :param filters: dict:

    """
    table = Table(table)
    table_columns = [table[c] for c in columns]
    query = (
        Query.from_(table)
        .select(*table_columns)
        .orderby(*filters["order"]["field"], order=Order[filters["order"]["direction"]])
        .limit(filters["size"]["limit"])
        .offset(filters["size"]["offset"])
    )

    query = set_query_filters(filters, query, table)

    return query.get_sql()


def create_select_filtered_paginated_query_count(table, filters: dict, id_field_where: str):
    """

    :param table:
    :param filters: dict:
    :param id_field_where: str:

    """
    table = Table(table)
    query = Query.from_(table).select(fn.Count(id_field_where, alias="count"))

    query = set_query_filters(filters, query, table)

    return query.get_sql()


def set_query_filters(filters, query, table):
    """

    :param filters:
    :param query:
    :param table:

    """
    for k, v in filters.items():
        if k == "size":
            continue
        if k == "order":
            continue
        op = v["op"]
        _op = sql_operators[op]
        if type(_op) == str:
            filter_value = v["value"]
            if _op == "like":
                query = query.where(table[k].like(filter_value))
            if _op == "isnull":
                query = query.where(table[k].isnull())
            if _op == "isnotnull":
                query = query.where(table[k].notnull())
            continue
        else:
            query = query.where(_op(table[k], Parameter(f":{k}")))
    return query


def create_select_filtered_query(table, columns: List[str], filters: dict):
    """

    :param table:
    :param columns: List[str]:
    :param filters: dict:

    """
    table = Table(table)
    table_columns = [table[c] for c in columns]
    query = Query.from_(table).select(*table_columns)

    if columns[0] == "*":
        query = Query.from_(table).select("*")

    query = set_query_filters(filters, query, table)

    return query.get_sql()


def create_insert(table, columns: List[str]):
    """

    :param table:
    :param columns: List[str]:

    """
    table = Table(table)
    table_columns = [table[c] for c in columns]
    query = Query.into(table).columns(*table_columns).insert(*[Parameter(f":{c}") for c in columns])

    return query.get_sql()


def create_update(table, columns: dict, filters: dict):
    """

    :param table:
    :param columns: dict:
    :param filters: dict:

    """
    table = Table(table)
    query = Query.update(table)
    for k, v in columns.items():
        query = query.set(k, v)
    query = set_query_filters(filters, query, table)
    return query.get_sql()


def create_delete(table, filters):
    """

    :param table:
    :param filters:

    """
    table = Table(table)
    query = Query.from_(table).delete()
    query = set_query_filters(filters, query, table)
    return query.get_sql()


def create_select_join_soft_delete_filter(table, relation_column_id, relation_join_table, relation_columns):
    """

    :param table:
    :param relation_column_id:
    :param relation_join_table:
    :param relation_columns:

    """
    _table, _relation_join_table = Tables(table, relation_join_table)
    query = (
        Query.from_(_table)
        .select(relation_column_id)
        .join(_relation_join_table)
        .on(getattr(_relation_join_table, relation_columns["join"]) == getattr(_table, relation_column_id))
        .where(getattr(_relation_join_table, relation_columns["main"]) == Parameter(":id"))
    )

    return query.get_sql()
