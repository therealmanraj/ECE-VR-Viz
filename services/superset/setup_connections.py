"""
Auto-provisions Trino database connections in Superset on startup.
Runs during superset-init. Skips any connection that already exists by name.
"""

from superset import create_app
from superset.extensions import db

CONNECTIONS = [
    {
        "database_name": "Trino",
        "sqlalchemy_uri": "trino://admin@trino:8080/mongo",
    },
    {
        "database_name": "Trino - mongo_app",
        "sqlalchemy_uri": "trino://admin@trino:8080/mongo_app",
    },
    {
        "database_name": "Trino - mongo_prod",
        "sqlalchemy_uri": "trino://admin@trino:8080/mongo_prod",
    },
]

app = create_app()

with app.app_context():
    # Import after app is initialized to avoid EncryptedType init error
    from superset.models.core import Database

    for conn in CONNECTIONS:
        existing = (
            db.session.query(Database)
            .filter_by(database_name=conn["database_name"])
            .first()
        )
        if existing:
            print(f"[setup_connections] '{conn['database_name']}' already exists, skipping.")
        else:
            new_db = Database(
                database_name=conn["database_name"],
                sqlalchemy_uri=conn["sqlalchemy_uri"],
            )
            db.session.add(new_db)
            db.session.commit()
            print(f"[setup_connections] Created connection: '{conn['database_name']}' -> {conn['sqlalchemy_uri']}")
