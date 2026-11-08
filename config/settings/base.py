import os
from pathlib import Path

from apps.core.public_operator import read_public_operator

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = env(name, "true" if default else "false").strip().lower()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"Environment variable {name} must be a boolean")


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


def env_int(name: str, default: int = 0) -> int:
    raw_value = env(name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def env_int_range(name: str, default: int, *, minimum: int, maximum: int) -> int:
    value = env_int(name, default)
    if not minimum <= value <= maximum:
        raise RuntimeError(f"Environment variable {name} must be between {minimum} and {maximum}")
    return value


SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.integrations",
    "apps.catalog",
    "apps.storefront",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.catalog.middleware.OwnerPanelPrivacyHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.storefront.geo_locale.EuropeCountryLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.PrivateLoginRateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", "127.0.0.1"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "pt-pt"
LANGUAGES = [
    ("pt-pt", "Português"),
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("de", "Deutsch"),
]
LANGUAGE_COOKIE_NAME = "lowcost_language"
LANGUAGE_COOKIE_SAMESITE = "Lax"
LANGUAGE_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SECURE = not DEBUG

# Opt in only after the local, attributed MMDB has been provisioned on the VPS.
GEO_LANGUAGE_ENABLED = env_bool("DJANGO_GEO_LANGUAGE_ENABLED", False)
# Release gate: enable only after explicit PT/ES crawl QA on the real host.
LOCALE_SEO_ENABLED = env_bool("DJANGO_LOCALE_SEO_ENABLED", False)
GEO_LANGUAGE_COUNTRY_DB = BASE_DIR / ".geoip" / "dbip-country-lite.mmdb"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PUBLIC_SITE_URL = env("DJANGO_PUBLIC_SITE_URL", "").rstrip("/")
PUBLIC_INDEXING_ENABLED = env_bool("DJANGO_PUBLIC_INDEXING_ENABLED", False)
# Development/test default keeps historic fixture semantics; production opts in.
PUBLIC_RECENT_PRICE_REQUIRED = False
INDEXNOW_KEY = env("DJANGO_INDEXNOW_KEY", "")
PUBLIC_OPERATOR = read_public_operator(BASE_DIR / ".legal" / "operator.json")

CATALOG_MAINTENANCE_BATCH_SIZE = env_int_range(
    "CATALOG_MAINTENANCE_BATCH_SIZE", 5, minimum=1, maximum=20
)

OWNER_PANEL_USERNAME = "lowcost-owner"

PRIVATE_LOGIN_RATE_LIMIT_ATTEMPTS = 5
PRIVATE_LOGIN_RATE_LIMIT_WINDOW_SECONDS = 300
PRIVATE_LOGIN_RATE_LIMIT_THROTTLE_SECONDS = 300
PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES = 4096
PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH = "/run/lowcost-europa/private-login-rate-limit.json"
PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH = "/run/lowcost-europa/private-login-rate-limit.lock"
