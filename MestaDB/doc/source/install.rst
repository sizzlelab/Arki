MestaDB installation guide
==========================

Introduction
------------

MestaDB is based on the `Django Python Web Framework <https://www.djangoproject.com/>`_.
MestaDB offers a simple **REST-like API**, which
is *an application* in the MestaDB Django project.

Getting the source code
-----------------------

You can checkout the latest source code with Git::

    git clone git@github.com:sizzlelab/Arki.git

Supported platforms
-------------------

MestaDB has been tested to be fully working in:

* Ubuntu 10.04 and 11.04 Linux with i386 architecture

* Mac Os X 10.6.8 (Intel)

System requirements
-------------------

You can run MestaDB in 512MB RAM / 10GB disk space virtual server, but generally:
more data you have in the database, more memory and disk space you need.

Pre-requisites
--------------

Before you can use MestaDB, you must have installed:

* Python 2.6 or 2.7

* PostGIS 1.5 and PostgreSQL 8.4 or 9.x (currenlty there is bug in Django so 9.1 is not recommended)

* python-psycopg2 (PostgreSQL database adapter for Python)

* Django 1.3.x

Optional
________

* Apache2 and mod_wsgi (for running MestaDB in production server)

* `Python Imaging Library (PIL) <http://www.pythonware.com/products/pil/>`_ for your Python version (for converting image files)

* `ffmpeg <http://ffmpeg.org/>`_ (for transcoding multimedia files)

Installing MestaDB
------------------

Although it may be possible to run MestaDB in Windows, it is not tested.
The easiest environment is Ubuntu Linux, because all necessary software
can be installed with apt-get or aptitude. Mac Os X 10.6 and 10.7
are good options too, at least as develompent environments.

Install GeoDjango
-----------------

You should find full instructions in
`GeoDjango Installation guide <https://docs.djangoproject.com/en/1.3/ref/contrib/gis/install/>`_,
but here are step-by-step instructions for Ubuntu.

Ubuntu 10.04 LTS - 11.04
________________________

    **Ubuntu 10.04 only**: You’ll need to install Postgis 1.5 from unofficial repository,
    check https://launchpad.net/~ubuntugis/+archive/ubuntugis-unstable
    But generally follow this steps:

    1. Open terminal window or ssh into your Ubuntu 10.04 box

    2. Copy and paste these commands::

        sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 314DF160
        sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable

Update repository lists::

    sudo aptitude update && sudo aptitude safe-upgrade

Install PostgreSQL 8.4-9.x, PostGIS 1.5, some python stuff and libraries::

    sudo aptitude install postgresql-8.4-postgis postgresql-contrib libpq-dev python-psycopg2 python-imaging python-virtualenv python-gdal

Mac Os X 10.6
_____________

Download and install required applications on your Mac in this order

   * GDAL Complete from here: http://www.kyngchaos.com/software/frameworks

   * PostgreSQL 9.x, PostGIS 1.5 for Postgres 9.x from here:
     http://www.kyngchaos.com/software/postgres

   * Psycopg2 2.4 for Postgres 9.x, PIL 1.1.x from here:
     http://www.kyngchaos.com/software/python

Initialise spatial database
___________________________

Create postgres user for your own username::

    sudo su - postgres -c "createuser --superuser $USER"

Test that it works::

    psql -c "SELECT CURRENT_TIMESTAMP" template1

Create spatial template, copy/paste this into terminal::

    POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib/postgis-1.5
    createdb -E UTF8 template_postgis
    createlang -d template_postgis plpgsql
    psql -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    psql -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql
    psql -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
    psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

Test that it works::

    psql -c "SELECT postgis_full_version()" template_postgis

a) Download and untar django 1.3.1::

    wget -O django.tar.gz http://www.djangoproject.com/download/1.3.1/tarball/
    tar zxvf django.tar.gz

b) OR go to https://www.djangoproject.com/download/ download and untar the latest version manually

Create virtualenv for django::

    export VIRTUALENVDIR=django-1.3-virtualenv
    virtualenv $VIRTUALENVDIR

Put this virtualenv in your path::

    export PATH=$(pwd)/$VIRTUALENVDIR/bin:$PATH
    which python
    # -> /home/user/django-1.3-virtualenv/bin/python

Install Django into new virtualenv::

    pip install django.tar.gz

OPTIONAL: Install Apache and mod_wsgi::

    sudo aptitude install apache2-mpm-prefork libapache2-mod-wsgi

OPTIONAL: Install ffmpeg::

    sudo aptitude install ffmpeg

After installation
------------------

TODO:

   * initialise database (manage.py syncdb)

   * testing dev server

   * running tests

   * put some test data into the database

   * Apache and mod_wsgi


Running public test server
--------------------------

If you want to access MestaDB from the outside world (not only from
localhost) start your Django server with command::

    $ python manage.py runserver 0.0.0.0:8000

Consult Django documentation to find out the meanings of additional
parameters.


:Author: Aapo Rista
