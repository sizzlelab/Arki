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
# Directories for applications (static original data files etc.)
DATA_DIR = os.path.normpath(os.path.join(PARENT_DIR, "data"))

# Create directories
for DIR in [VAR_DIR, LOG_DIR, DATA_DIR]:
    if os.path.isdir(DIR) is False:
        os.mkdir(DIR)

# Directories to store fetched mail
MAIL_DIR = os.path.join(PARENT_DIR, "var", "mail")
# TODO: move to content settings
MAIL_CONTENT_DIR = os.path.join(MAIL_DIR, "content")
MAIL_NEW_DIR = os.path.join(MAIL_DIR, "new")
MAIL_PROCESSED_DIR = os.path.join(MAIL_DIR, "processed")
MAIL_FAILED_DIR =  os.path.join(MAIL_DIR, "failed")
# Create mail directories
for DIR in [MAIL_DIR, MAIL_CONTENT_DIR, MAIL_NEW_DIR, MAIL_PROCESSED_DIR, MAIL_FAILED_DIR]:
    if os.path.isdir(DIR) is False:
        os.mkdir(DIR)

DEBUG = False # Override this in local_settings.py
TEMPLATE_DEBUG = DEBUG

ADMINS = ( # Override this in local_settings.py
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

LOGIN_URL = '/login'

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
# Developers NOTE: if this is True, some Point.coords[1] values may
# be e.g 25,01 instead of 25.01. This will break e.g. Google Maps javascript.
USE_L10N = False

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
#STATIC_ROOT = os.path.join(ROOT_DIR, 'static').replace('\\','/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
#ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(ROOT_DIR, 'static').replace('\\','/'),
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


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'mestadb.content.backends.authtokenbackend.AuthTokenBackend',
)

ROOT_URLCONF = 'mestadb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
#    os.path.join(ROOT_DIR, 'templates').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'django.contrib.gis', # Enables e.g. GeoModelAdmin
    #'django.contrib.humanize',
    'rosetta',
)

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOG_FILE = os.path.normpath(os.path.join(LOG_DIR, "django.log"))
FETCH_MAIL_LOG = os.path.normpath(os.path.join(LOG_DIR, "fetch_mail.log"))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)-8s"%(message)s"'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level':'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILE,
            'formatter': 'simple',
            'delay': False,
            'when': 'midnight',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            #'handlers':['null'],
            'handlers':['file'],
            'propagate': True,
#            'level':'INFO',
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            #'level': 'DEBUG',
            'propagate': False,
        },
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)-8s"%(message)s"'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level':'INFO',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILE,
            'formatter': 'simple',
            'delay': False,
            'when': 'midnight',
        },
        'fetch_mail_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': FETCH_MAIL_LOG,
            'formatter': 'simple',
            'delay': False,
            'when': 'midnight',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            #'handlers':['null'],
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
            },
        'fetch_mail': {
            #'handlers':['null'],
            'handlers': ['fetch_mail_file'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}



CUSTOM_APPS = (
    'apijson',
)

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

# CUSTOM_APPS is likely overridden in local_settings.py
INSTALLED_APPS += CUSTOM_APPS

# APP_DATA_DIRS is defined in local_settings
# Create application data directories
for APP_DIR_KEY in APP_DATA_DIRS.keys():
    DIR = os.path.normpath(os.path.join(DATA_DIR, APP_DATA_DIRS[APP_DIR_KEY]))
    if os.path.isdir(DIR) is False:
        os.mkdir(DIR)
    APP_DATA_DIRS[APP_DIR_KEY] = DIR

for APP_DIR_KEY in APP_VAR_DIRS.keys():
    DIR = os.path.normpath(os.path.join(VAR_DIR, APP_VAR_DIRS[APP_DIR_KEY]))
    if os.path.isdir(DIR) is False:
        os.mkdir(DIR)
    APP_VAR_DIRS[APP_DIR_KEY] = DIR
