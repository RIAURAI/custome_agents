"""
Django settings for WorkHub — Unified Business Workspace.
"""

from pathlib import Path
from decouple import config
import dj_database_url
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # WorkHub apps
    "companies",
    "accounts",
    "integrations",
    "dashboard",
    "email_hub",
    "meetings",
    "ai_assistant",
    "slack_hub",
    "google_hub",
    "social_media",
    "microsoft",
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
    "companies.middleware.CompanyMiddleware",
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
                "companies.middleware.company_context",
            ],
        },
    },
]

WSGI_APPLICATION = "workHub.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
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
MS_BASE_SCOPES = ["User.Read", "profile", "offline_access"]

# Feature → required Microsoft Graph scopes mapping.
# Each company enables features individually; OAuth requests only the scopes needed.
MS_FEATURE_SCOPES = {
    "email": {
        "label": "Outlook Mail",
        "icon": "bi-envelope",
        "description": "Read, send, and manage emails via Outlook.",
        "scopes": ["Mail.ReadWrite", "Mail.Send"],
    },
    "calendar": {
        "label": "Calendar & Meetings",
        "icon": "bi-calendar3",
        "description": "View calendar events and online meetings.",
        "scopes": ["Calendars.ReadWrite", "OnlineMeetings.Read"],
    },
    "presence": {
        "label": "Teams Presence",
        "icon": "bi-circle-fill",
        "description": "See who's online, busy, or away in real time.",
        "scopes": ["Presence.Read", "Presence.Read.All"],
    },
    "onedrive": {
        "label": "OneDrive Files",
        "icon": "bi-cloud",
        "description": "Browse, upload, download, and share files.",
        "scopes": ["Files.ReadWrite"],
    },
    "tasks": {
        "label": "To Do & Planner",
        "icon": "bi-check2-square",
        "description": "Manage tasks, to-do lists, and Planner boards.",
        "scopes": ["Tasks.ReadWrite", "Group.Read.All"],
    },
    "teams_chat": {
        "label": "Teams Chat",
        "icon": "bi-chat-dots",
        "description": "Read and send Teams chat and channel messages.",
        "scopes": ["Chat.ReadWrite", "ChannelMessage.Read.All", "ChannelMessage.Send",
                   "Team.ReadBasic.All", "Channel.ReadBasic.All"],
    },
    "contacts": {
        "label": "People & Contacts",
        "icon": "bi-people",
        "description": "Search people, view org directory and profiles.",
        "scopes": ["People.Read", "User.Read.All"],
    },
}

# Default features enabled for new companies (backwards-compatible)
MS_DEFAULT_FEATURES = ["email", "calendar"]
MS_REDIRECT_URI = "http://localhost:8000/integrations/callback/"

# ── Unfold Admin ──────────────────────────────────────────────────────────────
UNFOLD = {
    "SITE_TITLE": "WorkHub Admin",
    "SITE_HEADER": "WorkHub",
    "SITE_SUBHEADER": "Unified Business Workspace",
    "SITE_URL": "/dashboard/",
    "SITE_SYMBOL": "hub",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "primary": {
            "50": "oklch(97.5% .014 254)",
            "100": "oklch(94.5% .03 254)",
            "200": "oklch(88% .06 254)",
            "300": "oklch(80% .1 254)",
            "400": "oklch(70% .16 254)",
            "500": "oklch(60% .22 254)",
            "600": "oklch(52% .24 254)",
            "700": "oklch(45% .22 254)",
            "800": "oklch(39% .18 254)",
            "900": "oklch(33% .14 254)",
            "950": "oklch(25% .11 254)",
        },
    },
    "DASHBOARD_CALLBACK": "dashboard.admin.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Overview"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Companies"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Companies"),
                        "icon": "business",
                        "link": reverse_lazy("admin:companies_company_changelist"),
                    },
                    {
                        "title": _("Memberships"),
                        "icon": "group",
                        "link": reverse_lazy("admin:companies_membership_changelist"),
                    },
                    {
                        "title": _("Invitations"),
                        "icon": "mail",
                        "link": reverse_lazy("admin:companies_invitation_changelist"),
                    },
                    {
                        "title": _("Platform Access"),
                        "icon": "key",
                        "link": reverse_lazy("admin:companies_platformaccess_changelist"),
                    },
                    {
                        "title": _("Activity Logs"),
                        "icon": "history",
                        "link": reverse_lazy("admin:companies_activitylog_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Auth"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Integrations"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Company Integrations"),
                        "icon": "cable",
                        "link": reverse_lazy("admin:integrations_companyintegration_changelist"),
                    },
                ],
            },
            {
                "title": _("Slack"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Messages"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:slack_hub_slackmessage_changelist"),
                    },
                    {
                        "title": _("Auto Reply Rules"),
                        "icon": "smart_toy",
                        "link": reverse_lazy("admin:slack_hub_autoreplyrule_changelist"),
                    },
                ],
            },
        ],
    },
}

# ── Slack App ─────────────────────────────────────────────────────────────────
SLACK_CLIENT_ID = config("SLACK_CLIENT_ID", default="")
SLACK_CLIENT_SECRET = config("SLACK_CLIENT_SECRET", default="")
SLACK_BOT_TOKEN = config("SLACK_BOT_TOKEN", default="")
SLACK_SIGNING_SECRET = config("SLACK_SIGNING_SECRET", default="")
SLACK_APP_TOKEN = config("SLACK_APP_TOKEN", default="")  # xapp- token for Socket Mode
SLACK_BOT_AUTOSTART = config("SLACK_BOT_AUTOSTART", default="false")
SLACK_SCOPES = "channels:read,channels:history,channels:join,chat:write,users:read,groups:read,groups:history,im:read,im:history"
SLACK_REDIRECT_URI = "http://localhost:8000/integrations/slack/callback/"

# ── Calendly (OAuth 2.0 — per-company credentials stored in DB) ───────────────
CALENDLY_REDIRECT_URI = "http://localhost:8000/integrations/calendly/callback/"
CALENDLY_AUTH_BASE_URL = "https://auth.calendly.com/oauth/authorize"
CALENDLY_TOKEN_URL = "https://auth.calendly.com/oauth/token"
CALENDLY_API_BASE_URL = "https://api.calendly.com"

# ── Google Workspace (OAuth 2.0 — per-company credentials stored in DB) ───────
GOOGLE_REDIRECT_URI = "http://localhost:8000/integrations/google/callback/"

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# ── Fernet encryption (for token storage) ────────────────────────────────────
FERNET_KEY = config("FERNET_KEY", default="")

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "integrations": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "integrations.token_health": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "microsoft": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
