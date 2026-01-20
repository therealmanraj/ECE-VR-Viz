connect using trino

<!-- trino://admin@trino:8080/mongo/arc_dev -->

trino://admin@trino:8080/mongo/langara-dev

docker compose cp services/superset/check_permissions.py superset:/app/pythonpath/check_permissions.py
docker compose exec superset python /app/pythonpath/check_permissions.py admin
docker compose exec superset python /app/pythonpath/check_permissions.py analyst
docker compose exec superset python /app/pythonpath/check_permissions.py --roles
