2.2.2 - 2016-12-15
##################

* Fix the docs on PyPi and add a LICENSE file


2.2.1 - 2016-12-14
##################

* MAINT: Remove accidentially bundled wheels from sdist (23fc3b2_)

.. _23fc3b2: https://github.com/level12/keg-bouncer/commit/23fc3b2


2.2.0 - 2016-12-14
##################

* SEC: Enforce minimum key length for tokens (d9ed567_)
* MAINT: Replace the PyCrypto with cryptography (0c36f53_)
* Merge pull request #19 from level12/gh-18-docker-ci-tests (a878053_)
* Merge pull request #15 from level12/fix-ci-python-3.4-installation (b76df21_)
* Merge addition of codecov.yaml configuration (51d0614_)
* Merge enhancement to keep password history ordered (126e2df_)
* Merge new design with password and login history mixins (f794644_)

.. _d9ed567: https://github.com/level12/keg-bouncer/commit/d9ed567
.. _0c36f53: https://github.com/level12/keg-bouncer/commit/0c36f53
.. _a878053: https://github.com/level12/keg-bouncer/commit/a878053
.. _b76df21: https://github.com/level12/keg-bouncer/commit/b76df21
.. _51d0614: https://github.com/level12/keg-bouncer/commit/51d0614
.. _126e2df: https://github.com/level12/keg-bouncer/commit/126e2df
.. _f794644: https://github.com/level12/keg-bouncer/commit/f794644


2.1.0
#####
* Dropped Python 3.4 support

2.0.0
#####
* Redesign API
* Add API for verifying passwords and keeping password history
* Add API for keeping login history

1.0.0
#####
* Support groups/bundles/permissions.
* Support alembic integration
