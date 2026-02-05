from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ▼▼▼ 環境を判断するスイッチ ▼▼▼
# Renderの環境では'RENDER'という環境変数が設定されている
IS_PRODUCTION = 'RENDER' in os.environ

if IS_PRODUCTION:
    # --- 本番環境 (Render) の設定 ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    ALLOWED_HOSTS = [os.environ.get('RENDER_EXTERNAL_HOSTNAME')]
    #カスタムドメインをここに追加
    ALLOWED_HOSTS.append('akamafu.com')
    ALLOWED_HOSTS.append('www.akamafu.com') 
    
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    
    
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    MEDIA_URL = 'media/'
    MEDIA_ROOT = '/var/data/media'

else:
    # --- 開発環境 (あなたのPC) の設定 ---
    SECRET_KEY = 'django-insecure-your-local-secret-key' # ローカル用の簡単なキー
    DEBUG = True
    ALLOWED_HOSTS = []

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


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
    'django_bootstrap5',
    #Todoアプリ
    'todo.apps.TodoConfig',
    #学習ノート
    'learning_logs.apps.LearningLogsConfig',
    #ユーザー認証
    'accounts.apps.AccountsConfig',
    #ルーレットアプリ
    'roulette_app',
    #ロボ団タイマーアプリ
    'robodone_timer',
    'reading_notes.apps.ReadingNotesConfig',
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
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', # ★ここが正しい記述です
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main_page.wsgi.application'

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
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'



# Default primary key field type
# ... (この部分は変更なし) ...
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ログイン・ログアウト後のリダイレクト先
LOGIN_REDIRECT_URL = "mainpages:home" # ログイン後は学習ノートのトピック一覧へ
LOGOUT_REDIRECT_URL = "mainpages:home" # ログアウト後はサイトのトップページへ

