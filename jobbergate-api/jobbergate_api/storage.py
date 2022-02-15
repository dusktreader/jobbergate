"""
Persistent data storage
"""
import contextlib
import re
import typing

import asyncpg
import databases
import fastapi
import pydantic
import sqlalchemy
from fastapi.exceptions import HTTPException
from sqlalchemy import Column, or_
from sqlalchemy.sql.expression import BooleanClauseList, UnaryExpression
from starlette import status

from jobbergate_api.config import settings
from jobbergate_api.metadata import metadata

database = databases.Database(settings.DATABASE_URL)  # type: ignore


def render_sql(query) -> str:
    """
    Render a sqlalchemy query into a string for debugging.
    """
    return query.compile(dialect=database._backend._dialect, compile_kwargs={"literal_binds": True})


def search_clause(search_terms: str, searchable_fields: typing.List[Column],) -> BooleanClauseList:
    """
    Create search clause across searchable fields with search terms.
    """
    return or_(*[field.ilike(f"%{term}%") for field in searchable_fields for term in search_terms.split()])


def sort_clause(
    sort_field: str, sortable_fields: typing.List[Column], sort_ascending: bool,
) -> typing.Union[Column, UnaryExpression]:
    """
    Create a sort clause given a sort field, the list of sortable fields, and a sort_ascending flag.
    """
    sort_field_names = [f.name for f in sortable_fields]
    try:
        index = sort_field_names.index(sort_field)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sorting column requested: {sort_field}. Must be one of {sort_field_names}",
        )
    sort_column: typing.Union[Column, UnaryExpression] = sortable_fields[index]
    if not sort_ascending:
        sort_column = sort_column.desc()
    return sort_column


def create_all_tables():
    """
    Create all the tables in the database
    """
    engine = sqlalchemy.create_engine(settings.DATABASE_URL)

    metadata.create_all(engine)


@contextlib.contextmanager
def handle_fk_error():
    """
    This method is used to unpack metadata from a ForeignKeyViolationError
    """
    try:
        yield
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        FK_DETAIL_RX = (
            r"DETAIL:  Key \(id\)=\((?P<pk_id>\d+)\) is still referenced from table \"(?P<table>\w+)\""
        )
        matches = re.search(FK_DETAIL_RX, str(err), re.MULTILINE)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail=dict(
                message="Delete failed due to foreign-key constraint",
                table=matches.group("table") if matches else None,
                pk_id=matches.group("pk_id") if matches else None,
            ),
        )


T = typing.TypeVar("T", bound=pydantic.BaseModel)


async def fetch_instance(id: int, table: sqlalchemy.Table, model: typing.Type[T]) -> T:
    """
    Fetch a single frow from a table by its id and unpack it into a response model.
    """
    query = table.select(table.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Could not find {table.name} instance with id {id}")
    return model.parse_obj(result)
