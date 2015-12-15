from __future__ import absolute_import

from keg.db import db


def in_session(obj):
    """Adds an entity to the current DB session and hands the entity back to you.
    Useful when building entities declaratively.

    :param obj: may be a scalar entity or iterable of entities.
    """
    try:
        iterobj = iter(obj)
    except TypeError:
        iterobj = [obj]

    for x in iterobj:
        db.session.add(x)
    db.session.flush()

    return obj
