from __future__ import absolute_import

import sqlalchemy as sa

from keg.db import db
from keg_bouncer.model.mixins import UserMixin


class User(db.Model, UserMixin):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(), nullable=False)
