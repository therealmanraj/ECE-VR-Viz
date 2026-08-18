# File: Dockerfile
# Path: /services/superset/Dockerfile

FROM apache/superset:6.0.0

USER root

RUN uv pip install --no-cache-dir authlib flask-cors psycopg2-binary "trino[sqlalchemy]"

USER 1000 