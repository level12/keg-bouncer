import os

from setuptools import setup, find_packages

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()

version_fpath = os.path.join(cdir, 'keg_bouncer', 'version.py')
version_globals = {}
with open(version_fpath) as fo:
    exec(fo.read(), version_globals)

setup(
    name='KegBouncer',
    version=version_globals['VERSION'],
    description='A three-tiered permissions model for KegElements built atop Flask-User',
    long_description=README,
    author='Level 12',
    author_email='devteam@level12.io',
    url='https://github.com/level12/keg-bouncer',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=['keg_bouncer_test_app*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask-Login',
        'Keg',
        'KegElements',
        'cryptography',
        'six',
        'SQLAlchemy',
        'wrapt',
    ],
)
