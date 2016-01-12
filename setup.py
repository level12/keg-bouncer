import os

from setuptools import setup, find_packages

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()

from keg_bouncer.version import VERSION

setup(
    name='KegBouncer',
    version=VERSION,
    description='A three-tiered permissions model for KegElements built atop Flask-User',
    author='Level 12',
    author_email='devteam@level12.io',
    url='https://github.com/level12/keg-bouncer',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=['keg_bouncer_test_app*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask-User',
        'Keg',
        'KegElements',
        'SQLAlchemy',
        'wrapt',
    ],
    long_descripton=README,
)
