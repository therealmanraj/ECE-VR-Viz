import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "dev_secret_change_me")

from flask_appbuilder.security.manager import AUTH_DB

AUTH_TYPE = AUTH_DB
# AUTH_USER_REGISTRATION = True
# AUTH_USER_REGISTRATION_ROLE = "Gamma"  


WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False

# Stricter login rate limiting to block brute-force attempts
AUTH_RATE_LIMITED = True
AUTH_RATE_LIMIT = "10 per minute"

FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "DASHBOARD_RBAC": True,
    "GLOBAL_ASYNC_QUERIES": False,
}


# Query timeout settings — increase these if large MongoDB queries time out
SQLLAB_TIMEOUT = 600          # seconds SQLLab waits for a query result (default 30)
SUPERSET_WEBSERVER_TIMEOUT = 600  # seconds before gunicorn kills a request
SQL_MAX_ROW = 100000           # max rows returned to the browser

LOG_LEVEL = "INFO"

ENABLE_UI_THEME_ADMINISTRATION = True


ENABLE_UI_THEME_ADMINISTRATION = True

APP_NAME = "ECE Superset"

# APP_ICON = "/static/assets/images/superset-logo-horiz.png"

THEME_DEFAULT = {
    "token": {
        "colorPrimary": "#2563eb",
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
