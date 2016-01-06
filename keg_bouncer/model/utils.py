import sqlalchemy as sa

from keg.db import db


def make_link(name, from_column_name, from_column, to_column_name, to_column,
              table_constructor=db.Table):
    """Makes a many-to-many linking table named `name` with columns named `from_column_name` and
    `to_column_name` linking `from_column` and `to_column` as `ForeignKey`s.

    :param op: must be an Alembic operations object.
    :param name: will be the name of the linking table.
    :param from_column_name: will be the name of the column that links to the "left-side" of the
                             linking.
    :param from_column: must be a SQLAlchemy Column object representing the "left-side" of the
                        linking.
    :param to_column_name: will be the name of the column that links to the "right-side" of the
                           linking.
    :param to_column: must be a SQLAlchemy Column object representing the "right-side" of the
                      linking.
    :param table_constructor: allows you to override what function is used to create the table.
                              It uses `db.Table` by default.
    """
    return table_constructor(
        name,
        sa.Column(
            from_column_name,
            from_column.type,
            sa.ForeignKey(from_column, ondelete='CASCADE'),
            nullable=False,
            primary_key=True),
        sa.Column(
            to_column_name,
            to_column.type,
            sa.ForeignKey(to_column, ondelete='CASCADE'),
            nullable=False,
            primary_key=True)
    )
