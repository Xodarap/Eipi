# Django settings for eipi2 project.

DEBUG  = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('bwest', 'xodarap00@gmail.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'django.db.backends.mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABSE_ENGINE = 'mysql'
DATABASE_NAME = 'eipi'             # Or path to database file if using sqlite3.
DATABASE_USER = 'eipi'             # Not used with sqlite3.
DATABASE_PASSWORD = 'vegANdoit2011'         # Not used with sqlite3.
DATABASE_HOST = '' #'web182.webfactional.com'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = '' #'3306'             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/eipi/eipi2/static'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'c1f5l(+c1*+n=q9(1z_j7q%f5r)s^ux85@$r3h2hel+dno&^n_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'eipi2.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #'/home/eipi/webapps/django/eipi2/eipi2/',
    #'/home/eipi/webapps/django/eipi2/eipi2/feeds'
    '/home/eipi/eipi/feeds',
    '/home/eipi/eipi/',
    '/home/eipi/eipi/UserAnalytics'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'feeds',
    'UserAnalytics',
    'django_cron'
)

LOGIN_URL = '/account/login'
LOGIN_REDIRECT_URL = '/feeds/'

#Email stuff
EMAIL_HOST = 'smtp.webfaction.com'
EMAIL_HOST_USER = 'eipi'
EMAIL_HOST_PASSWORD = 'vegANdoit2011'
DEFAULT_FROM_EMAIL = 'xodarap00@gmail.com'
SERVER_EMAIL = 'xodarap00@gmail.com'

CRON_POLLING_FREQUENCY = 60
