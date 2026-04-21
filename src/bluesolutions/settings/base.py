import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['blue.communityplaylist.com']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.portfolio',
    'apps.main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bluesolutions.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bluesolutions.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'bluesolutions'),
        'USER': os.environ.get('DB_USER', 'bluesolutions'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Denver'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get(
    'STATIC_ROOT',
    '/var/www/vhosts/communityplaylist.com/blue.communityplaylist.com/staticfiles/'
)
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get(
    'MEDIA_ROOT',
    '/var/www/vhosts/communityplaylist.com/blue.communityplaylist.com/media/'
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Drive sync settings
GDRIVE_PORTFOLIO_FOLDER_ID = os.environ.get(
    'GDRIVE_PORTFOLIO_FOLDER_ID', '1g1K0dg5YFEtdna0md5PBg1-6BndfVSVk'
)
GDRIVE_CREDENTIALS_FILE = os.environ.get(
    'GDRIVE_CREDENTIALS_FILE', '/app/gdrive_credentials.json'
)

JAZZMIN_SETTINGS = {
    'site_title': 'Blue Solutions Admin',
    'site_header': 'Blue Solutions',
    'site_brand': 'Blue Solutions',
    'welcome_sign': 'Blue Solutions Admin',
    'copyright': 'Blue Solutions',
    'topmenu_links': [
        {'name': '🏛️ View Site', 'url': '/', 'new_window': True},
        {'name': '❓ How To Guide', 'url': '/admin/help/'},
    ],
    'show_ui_builder': False,
}
