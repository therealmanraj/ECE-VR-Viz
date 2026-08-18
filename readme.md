# How to run

1. Install docker desktop `https://www.docker.com/products/docker-desktop/`
2. Open the ECE-VR-VIZ folder in VS Code or open the directory it is in for example

```bash
    cd ~
    cd /Users/manrajsingh/Downloads
```

3. When running for the first time use this command in the terminal or VS Code

```bash
    docker compose up
```

4. To connect to the mongodb database use the following

![A local image](./images/Step%201.png)

Click on Settings > Database Connections

![A local image](./images/Step%202.png)

From the dropdown click on trino

![A local image](./images/Step%203.png)

Add this url in the SQLALCHEMY URI

```bash
trino://admin@trino:8080/mongo_app

trino://admin@trino:8080/mongo_prod

trino://admin@trino:8080/mongo/langara-dev-client
```

![A local image](./images/Step%204.png)

From the home menu click on add icon > Data > Create Dataset

![A local image](./images/Step%205.png)

Select Trino > langara-dev > select table

5. To turn down the container use

```bash
docker compose down
```

<hr>

Additional commands

```bash
docker compose cp services/superset/check_permissions.py superset:/app/pythonpath/check_permissions.py
docker compose exec superset python /app/pythonpath/check_permissions.py admin
docker compose exec superset python /app/pythonpath/check_permissions.py analyst
docker compose exec superset python /app/pythonpath/check_permissions.py --roles
```

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```
