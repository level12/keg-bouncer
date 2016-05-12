.. default-role:: code
.. role:: python(code)
  :language: python

==========
KegBouncer
==========

.. image:: https://circleci.com/gh/level12/keg-bouncer.svg?style=svg
  :target: https://circleci.com/gh/level12/keg-bouncer

.. image:: https://codecov.io/github/level12/keg-bouncer/coverage.svg?branch=master
  :target: https://codecov.io/github/level12/keg-bouncer?branch=master

.. _Keg: https://pypi.python.org/pypi/Keg
.. _KegElements: https://pypi.python.org/pypi/KegElements
.. _Flask-Login: http://flask-login.readthedocs.io/en/latest/

A one-stop shop for all things related to authentication and authorization in a Keg_ app.


Intro
-----

Built on top of Keg_ and KegElements_, KegBouncer offers several features for managing authorization and authentication. KegBouncer allows you to pick and choose which features you want it to handle in you application. It achieves this by providing each feature as a Mixin class which you can optionally mixin to your entities (probably a `User` entity).

The available mixins cover:

* Three-tierd permission system
* Password-based authentication and password history
* Login history

Refer to the sections below on how to use each of these.

One-Primary-Key Requirement
***************************

Note that each mixin will automatically determine the primary key of your entitiy. However, your entity must have exactly one primary key, and it must be specified as SQLAlchemy declarative class attribute.


Permissions
-----------

In order to use KegBouncer's authorization features to protect Keg views, you will also need Flask-Login_.
However, KegBouncer's models do not require that dependency.


`keg_bouncer.mixins.PermissionMixin` provides a three-tiered permissions model. It manages four kinds of entities:

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


Usage
*****

To add permission facilities to your user entity, inherit the `PermissionMixin` like this:

.. code:: python

   import flask_login  # Only necessary if using KegBouncer to protect you views.
   from sqlalchemy import import Column, Integer, String

   Base = sqlalchemy.ext.declarative.declarative_base()

   class User(Base, flask_login.UserMixin, keg_bouncer.model.mixins.PermissionMixin):
       __tablename__ = 'users'
       id = Column(Integer, primary_key=True)


Protecting Views and Components
*******************************

To protect various parts of your application, you can use the tools provided in `keg_bouncer.auth`:

In order to take advantage of these tools, your `User` entity needs to also mixin `flask_login.UserMixin`.

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


Also within this merge revision, you will need to create some linking tables for your `User`
entity (which mixes in ``keg_bouncer.model.mixins.PermissionMixin``).


Password-based Authentication
-----------------------------

To add password-based authentication to your entity, you need to dynamically construct a password mixin object and mix it in to your entity.

.. code:: python

  from keg_bouncer.model import mixins
  from passlib.context import CryptContext
  import sqlalchemy as sa

  crypt_context = CryptContext(schemes=['bcrypt'])

  # This mixin is optional but allows you to add additional fields to the password history table.
  class OptionalAdditionalFields(object):
      another_field = sa.Column(sa.Integer)


  password_history_mixin = mixins.make_password_mixin(
      OptionalAdditionalFields,    # [optional] Allows you to add more fields to the password
                                   # history table via a mixin
      crypt_context=crypt_context  # [optional, but must be provided here or via another means]
                                   # Configures the CryptContext for hashing and verifying
  )


  class User(password_history_mixin):
      default_crypt_context = crypt_context  # An alternative way of specifying your CryptContext

      # Yet another way to specify your CryptContext
      def get_crypt_context(self):
          return crypt_context


  help(User.set_password)  # Adds password to password history

  help(User.verify_password)  # Verifies a password against most recent password

  help(User.is_password_used_previously)  # Looks for password in history

  help(User.password_history_entity)  # SQLAlchemy entity defining password history entries

  User.password_history  # SQLAlchemy relationship for past passwords;
                         # sorted in reverse chronological order


**Note:** If you use `is_password_used_previously` or a similar concept, your choice of a hashing algorithm can drastically impact performance since password verification is intentionally slow.
For example, using `bcrypt` instead of `sha256_crypt` will allow you to verify passwords about twice as quickly. This makes a big difference when you're sifting through past passwords.


Login History
-------------

To add login history to your entity, you need to dynamically construct a history mixin object and mix it in to your entity.

.. code:: python

  from keg_bouncer.model import mixins
  import sqlalchemy as sa

  # This mixin is optional but allows you to add additional fields to the login history table.
  class OptionalAdditionalFields(object):
      another_field = sa.Column(sa.Integer)


  login_history_mixin = mixins.make_login_history_mixin(
      OptionalAdditionalFields,  # [optional] Allows you to add more fields to the login history
                                 # table via a mixin
  )


  class User(login_history_mixin):
      pass


  help(User.login_history_entity)  # SQLAlchemy entity defining login history entries

  User.login_history  # SQLAlchemy relationship for past logins;
                      # sorted in reverse chronological order

  # Example use:
  def register_login(user):
      user.login_history.insert(0, user.login_history_entity(is_login_successful=True))


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
