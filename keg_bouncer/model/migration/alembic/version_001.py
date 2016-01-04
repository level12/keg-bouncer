import sqlalchemy as sa


__all__ = ['upgrade', 'downgrade']


def make_link(op, name, from_column_name, from_column, to_column_name, to_column):
    """Makes a linking table named `name` with columns named `from_column_name` and
    `to_column_name` linking `from_column` and `to_column` as `ForeignKey`s.

    `from_column` and `to_column` can be either a SQLAlchemy `Column` object or
    tuples of the form `(column_spec, type)`. For example: `('user.id', Integer)`.
    """
    column_obj_and_type = lambda col: (col if isinstance(col, tuple)
                                       else (col, col.type))
    from_column_obj, from_column_type = column_obj_and_type(from_column)
    to_column_obj, to_column_type = column_obj_and_type(to_column)
    return op.create_table(
        name,
        sa.Column(
            from_column_name,
            from_column_type,
            sa.ForeignKey(from_column_obj, ondelete='CASCADE'),
            nullable=False,
            primary_key=True),
        sa.Column(
            to_column_name,
            to_column_type,
            sa.ForeignKey(to_column_obj, ondelete='CASCADE'),
            nullable=False,
            primary_key=True)
    )


def create_label_table(op, name):
    return op.create_table(
        name,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('label', sa.Text, unique=True, nullable=False)
    )


def upgrade(op, user_primary_key_column, user_primary_key_type=None):
    """Install needed tables for KegBouncer.

    :param op: must be the Alembic operations object.

    :param user_primary_key_column: The primary key column of the user entity (i.e. the one
    that inherits `UserMixin`). This must be a `string` or a SQLAlchemy `Column` object from
    a `Table`. The column must specify both the table and the column name.

    For example, you can specify something like `'users.id'` or `users_table.c.id`.

    If you set this to `None`, you will need to add linking tables manually.

    :param user_primary_key_type: the SQLAlchemy column type which applies to the column given
    in `user_primary_key_column`.

    If you specify `user_primary_key_column`, you must specify the type as well.
    """
    permission = op.create_table(
        'permissions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False)
    )

    permission_bundle = create_label_table(op, 'permission_bundles')
    user_group = create_label_table(op, 'user_groups')

    make_link(op, 'user_group_permission_map',
              'user_group_id', user_group.c.id,
              'permission_id', permission.c.id)

    make_link(op, 'user_group_bundle_map',
              'user_group_id', user_group.c.id,
              'permission_bundle_id', permission_bundle.c.id)

    make_link(op, 'bundle_permission_map',
              'permission_bundle_id', permission_bundle.c.id,
              'permission_id', permission.c.id)

    if user_primary_key_column:
        make_link(op, 'user_user_group_map',
                  'user_id', (user_primary_key_column, user_primary_key_type),
                  'user_group_id', user_group.c.id)


def downgrade(op, include_user_linking_tables=True):
    """Removes KegBouncer tables.

    :param op: must be the Alembic operations object.
    :param include_user_linking_tables: if set to False, you must remove any linking tables to your
    user entity (the one that inherits UserMixin) manually.
    """
    if include_user_linking_tables:
        op.drop_table('user_user_group_map')
    op.drop_table('bundle_permission_map')
    op.drop_table('user_group_bundle_map')
    op.drop_table('user_group_permission_map')
    op.drop_table('user_groups')
    op.drop_table('permission_bundles')
    op.drop_table('permissions')
