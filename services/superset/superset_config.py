import os

# Required
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "dev_secret_change_me")

# --- Basic Auth (simple login) ---
from flask_appbuilder.security.manager import AUTH_DB

AUTH_TYPE = AUTH_DB
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Admin"  # or "Gamma" if you want safer default

# --- Dev-friendly settings ---
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False

# If you're embedding Superset in an iframe
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "DASHBOARD_RBAC": True,
}

# Optional: keep logs quieter
LOG_LEVEL = "INFO"

ENABLE_UI_THEME_ADMINISTRATION = True

# Enable theme admin in UI (optional)
ENABLE_UI_THEME_ADMINISTRATION = True

APP_NAME = "ECE Superset"

# Your logo (put the file in /app/superset/static/assets/images/)
# Or keep default
# APP_ICON = "/static/assets/images/superset-logo-horiz.png"

THEME_DEFAULT = {
    "token": {
        "colorPrimary": "#2563eb",   # primary accent (blue)
        "colorLink": "#2563eb",
        "borderRadius": 8,
        "fontFamily": "Inter, Helvetica, Arial",
        "fontSize": 14,
        # "brandLogoUrl": APP_ICON,
        "brandLogoHeight": "24px",
    },
    "algorithm": "default",
}

THEME_DARK = {
    **THEME_DEFAULT,
    "algorithm": "dark",
}
