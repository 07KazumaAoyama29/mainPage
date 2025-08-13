# settings.py

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECRET_KEYはRenderの環境変数から読み込む
SECRET_KEY = os.environ.get('SECRET_KEY')

# DEBUGモードは本番環境では必ずFalseに
DEBUG = False

# 正しいALLOWED_HOSTSの設定
ALLOWED_HOSTS = ['main-page-n44z.onrender.com', 'www.akamafu.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # WhiteNoiseを追加
    'django.contrib.staticfiles',
    'mainpages.apps.MainpagesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # WhiteNoiseのミドルウェアを追加
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main_page.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.django. bambini',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main_page.wsgi.application'


# Database
# RenderのPostgreSQLに接続する設定
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}


# Password validation
# ... (この部分は変更なし) ...
AUTH_PASSWORD_VALIDATORS = [
    # ...
]


# Internationalization
# ... (この部分は変更なし) ...
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'


# Static files (CSS, JavaScript, Images)
# 本番環境用の静的ファイル設定
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# ... (この部分は変更なし) ...
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'