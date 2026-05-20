"""
Django settings for WorkHub — Unified Business Workspace.
"""

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # WorkHub apps
    "accounts",
    "integrations",
    "dashboard",
    "email_hub",
    "meetings",
    "ai_assistant",
    "slack_hub",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "workHub.urls"

TEMPLATES_DIR = BASE_DIR / "templates"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "workHub.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default=""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }
else:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth redirects ────────────────────────────────────────────────────────────
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# ── Microsoft Identity (Azure App Registration) ───────────────────────────────
MS_CLIENT_ID = config("MS_CLIENT_ID", default="")
MS_CLIENT_SECRET = config("MS_CLIENT_SECRET", default="")
MS_TENANT_ID = config("MS_TENANT_ID", default="common")
MS_AUTHORITY = f"https://login.microsoftonline.com/{config('MS_TENANT_ID', default='common')}"
MS_SCOPES = [
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Calendars.Read",
    "OnlineMeetings.Read",
]
MS_REDIRECT_URI = "http://localhost:8000/integrations/callback/"

# ── Slack App ─────────────────────────────────────────────────────────────────
SLACK_CLIENT_ID = config("SLACK_CLIENT_ID", default="")
SLACK_CLIENT_SECRET = config("SLACK_CLIENT_SECRET", default="")
SLACK_BOT_TOKEN = config("SLACK_BOT_TOKEN", default="")
SLACK_SIGNING_SECRET = config("SLACK_SIGNING_SECRET", default="")
SLACK_APP_TOKEN = config("SLACK_APP_TOKEN", default="")  # xapp- token for Socket Mode
SLACK_BOT_AUTOSTART = config("SLACK_BOT_AUTOSTART", default="false")
SLACK_SCOPES = "channels:read,channels:history,channels:join,chat:write,users:read,groups:read,groups:history,im:read,im:history"
SLACK_REDIRECT_URI = "http://localhost:8000/integrations/slack/callback/"

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# ── Fernet encryption (for token storage) ────────────────────────────────────
FERNET_KEY = config("FERNET_KEY", default="")
