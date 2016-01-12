.. default-role:: code
.. role:: python(code)
  :language: python

==========
KegBouncer
==========


.. image:: https://coveralls.io/repos/level12/keg-bouncer/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/level12/keg-bouncer?branch=master


.. image:: https://circleci.com/gh/level12/keg-bouncer.svg?style=svg
    :target: https://circleci.com/gh/level12/keg-bouncer


Intro
-----

A three-tiered permissions model for KegElements that builds atop flask-user. KegBouncer is aware of four kinds of
entities:

* Users
* Permissions (for describing actions that can be guarded within the system)
* User groups (for grouping users in a way that best models business needs)
* Permission bundles (for grouping permissions in a way that best models the system)

We call this a "three-tiered" permissions model because a user can be granted permissions in three ways:

1. Directly
2. Through permission bundles
3. Through user groups

This terminology is designed to distinguish this permissions model from other ones, like RBAC, which permit higherarchies of any depth. Technically, this three-tier model is a special case of RBAC.

**Note about the term "role":** While this model is technically a special case of the widely-used *Role-based access control (RBAC)*, we took great pains to avoid the highly ambiguous term "role."

About Flask-User's Built-in Roles
*********************************

Flask-User comes built-in with a [very primitive] notion of "roles" which can be assigned to users. As noted above, Flask-User's notion of "role" is quite different and far less flexible than the "role" in RBAC. KegBouncer
supercedes any permission/role system in Flask-User and assumes you don't plan to use it.


Usage
-----

Adding Permissions to Your Model
********************************

To add permission facilities to your user entity, inherit the `UserMixin` and configure the primary key:

.. code:: python

   from sqlalchemy import import Column, Integer, String

   Base = sqlalchemy.ext.declarative.declarative_base()

   class User(Base, keg_bouncer.model.mixins.UserMixin):
       __tablename__ = 'users'
       id = Column(Integer, primary_key=True)

You must have a single-column primary key, but it may have any name or any type you like.

The mixin will assume your primary key is named `id` on the ORM object. If you want to name your primary key something other than `id` you can do it two different ways.

Most simply, you can explicitly provide a column name on the entity:

.. code:: python

   # ...
   class User(Base, keg_bouncer.model.mixins.UserMixin):
       __tablename__ = 'users'
       id = Column('name', String, primary_key=True)

Or you can tell the mixin the name of your primary key column:

.. code:: python

   # ...
   class User(Base, keg_bouncer.model.mixins.UserMixin):
       __tablename__ = 'users'
       primary_key_column = 'name'
       name = Column(String, primary_key=True)


Protecting Views and Components
*******************************

To protect various parts of your application, you can use the tools provided in `keg_bouncer.auth`:

#. Use an `if` block and check for permissions:

   .. code:: python

      # ...
      if keg_bouncer.auth.current_user_has_permissions('launch-missiles'):
          launch_missiles()

#. Decorate a function:

   .. code:: python

      # ...
      @keg_bouncer.auth.requires_permissions('launch-missiles')
      def launch_missiles(target=Enemy())
          # ...

#. Inherit from `ProtectedBaseView`:

   .. code:: python

      # ...
      class LaunchMissilesView(keg_bouncer.auth.ProtectedBaseView):
          requires_permission = 'launch-missiles'

Migration
*********

KegBouncer uses Alembic_ to manage migrations and it assumes your app does as well.

.. _Alembic: https://alembic.readthedocs.org/

To use the migrations that KegBouncer provides, you need to tell Alembic where
to find the revisions.  In your `alembic.ini` file for your application, adjust
your ``version_locations`` setting to include your KegBouncer's versions
folder.


.. code:: ini

      [alembic]
      version_locations = alembic/versions keg_bouncer:alembic/versions


If you run ``alembic heads`` you should now see two heads, one for your application and one for
KegBouncer.

.. code:: txt

    $ alembic heads
    51ba1b47505e (application) (head)
    13d265b97e4d (keg_bouncer) (head)


It is totally fine for the application to have multiple heads, but you will need to upgrade them
independently. A better option is to merge the two heads into one. Do that with the
``alembic merge`` comand.


.. code:: sh

  $ alembic merge -m "pull KegBouncer into application" 51ba1b 13d265
  Generating /path/to/app/alembic/versions/31b094b2844f_pull_keg_bouncer_into_application.py ... done


If you run ``alembic heads`` again you will find that there is one head.

.. code:: txt

  $ alembic heads
  31b094b2844f (application, keg_bouncer) (head)


Also within this merge revision, you will need to create some linking tables for your User
entity (which mixes in ``keg_bouncer.model.mixins.UserMixin``). You can modify the migration to look
very much like this:

.. code:: python

  from keg_bouncer.model import migration

  from app.model.entities import User


  def upgrade():
      migration.link_user_to_user_groups(op, User.id)


  def downgrade():
      migration.drop_link_from_user_to_user_groups(op)


Development
-----------

Branches & State
****************

* `master`: our "production" branch

All other branches are feature branches.

Project Requirements
********************

See `requirements` directory for the files needed and note:

* You should clone Keg and KegElements and `pip install -e .` to get working copies.  Since these
  libraries are new, they will likely change frequently.
* Read the notes in the requirements files if you have problems.
* There is a `build-wheelhouse.py` script that can be run if new requirements have been added.  It
  always rebuilds libraries in `wheel-only.txt` so Git will always show them modified.  But, if they
  haven't really been changed, you should revert those files so as to not add "static" to the
  commits.

Development Environment
***********************

To quickly setup a virtual environment for development, you can use one of the supplied scripts.

If `pyenv` + `virtualenv` is your thing, use `source scripts/make-env-venv.sh`.

If `vex` is your thing, use `source scripts/make-env-vex.sh`.

Lint
****

Protect yourself from committing lint by installing the pre-commit hook:

.. code:: sh

   ln -s scripts/pre-commit .git/hooks
