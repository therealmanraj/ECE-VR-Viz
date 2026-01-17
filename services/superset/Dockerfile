# File: Dockerfile
# Path: /services/superset/Dockerfile

FROM apache/superset:4.1.1

USER root

# Install authlib for OAuth support and flask-cors for CORS support
RUN pip install --no-cache-dir authlib flask-cors
RUN pip install --no-cache-dir psycopg2-binary
RUN pip install --no-cache-dir "trino[sqlalchemy]"

USER 1000 