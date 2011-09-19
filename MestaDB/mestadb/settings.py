# -*- coding: utf-8 -*-
# Django settings for mestadb project.
# This file imports local_settings in the end. You can override most of
# the settings configured here.
#

import os
# Shortcuts to some common directories
ROOT_DIR = os.path.normpath(os.path.dirname(__file__))
PARENT_DIR = os.path.normpath(os.path.join(ROOT_DIR, ".."))
# Directories for variable data (logs etc.)
VAR_DIR = os.path.normpath(os.path.join(PARENT_DIR, "var"))
LOG_DIR = os.path.normpath(os.path.join(VAR_DIR, "log"))

# Create directories
for DIR in [VAR_DIR, LOG_DIR]:
    if os.path.isdir(DIR) is False:
        os.mkdir(DIR)

DEBUG = False # Override this in local_settings.py
TEMPLATE_DEBUG = DEBUG

ADMINS = ( # Override this in local_settings.py
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = { # Mandatory: override this in local_settings.py
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Helsinki' # Optional: override this in local_settings.py

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us' # Optional: override this in local_settings.py

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'cy0m@3=i33)6avrrcw3s4e@%&txcxv*45_kz&)ciw1+5tw6gw2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware', # For i18n
)

ROOT_URLCONF = 'mestadb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    #'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'django.contrib.gis', # Enables e.g. GeoModelAdmin
    #'django.contrib.humanize',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

### Server/developer workstation specific settings ###
try:
    from local_settings import *
except ImportError:
    print """
    -------------------------------------------------------------------------
    You need to create a local_settings.py file which needs to contain at least
    database connection information.

    Copy local_settings_example.py to local_settings.py and edit it.
    -------------------------------------------------------------------------
    """
    import sys
    sys.exit(1)


STATIC_DOC_ROOT = os.path.join(ROOT_DIR, 'static').replace('\\','/')
STATIC_ROOT = os.path.join(ROOT_DIR, 'static').replace('\\','/')

# Put your custom apps you want to use here
# TODO: To local_settings!
CUSTOM_APPS = (
    'apijson',
    'place',
)
INSTALLED_APPS += CUSTOM_APPS