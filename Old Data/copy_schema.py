"""
copy_schema.py
─────────────────────────────────────────────────────────────────────────────
Copies the working _schema from langara-dev-client into app_db.
Since langara-dev-client already has correct Trino types (timestamp(3),
bigint, array(row(...)) etc.), we just clone it directly.

Run:
  python3 copy_schema.py
─────────────────────────────────────────────────────────────────────────────
"""

import os
import pymongo
from bson import ObjectId

# ── Both databases are on the same cluster ────────────────────────────────────
MONGO_URI    = os.getenv("MONGO_URI", "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0")
SOURCE_DB    = "langara-dev-client"   # has the working _schema
TARGET_DB    = "app_db"               # where we want to copy it to

def main():
    client = pymongo.MongoClient(MONGO_URI)

    source = client[SOURCE_DB]
    target = client[TARGET_DB]

    # ── Read all schema docs from langara-dev-client ──────────────────────────
    source_schemas = list(source["_schema"].find({}))

    if not source_schemas:
        print(f"❌  No documents found in {SOURCE_DB}._schema")
        client.close()
        return

    print(f"✅  Found {len(source_schemas)} schema definitions in '{SOURCE_DB}._schema':\n")
    for s in source_schemas:
        table = s.get("table", s.get("name", "unknown"))
        fields = s.get("fields", [])
        print(f"   📋  {table:30s} ({len(fields)} fields)")

    # ── Check which tables actually exist in app_db ───────────────────────────
    app_db_collections = set(target.list_collection_names())
    print(f"\n📦  Collections in '{TARGET_DB}':")
    for name in sorted(app_db_collections):
        count = target[name].count_documents({})
        print(f"   {name:30s} {count:>5} docs")

    # ── Copy schema docs, reassigning new _ids ─────────────────────────────────
    print(f"\n⚙️   Copying _schema to '{TARGET_DB}' …\n")
    target["_schema"].drop()

    copied  = []
    skipped = []

    for doc in source_schemas:
        table = doc.get("table", doc.get("name", ""))
        # Give each doc a fresh _id to avoid conflicts
        doc["_id"] = ObjectId()

        if table in app_db_collections:
            copied.append(doc)
        else:
            # Still copy it — Trino may need it even if collection is empty
            # but flag it so you're aware
            skipped.append(table)
            copied.append(doc)

    target["_schema"].insert_many(copied)

    print(f"✅  Copied {len(copied)} schema definitions to '{TARGET_DB}._schema'\n")

    if skipped:
        print(f"⚠️   These tables are in _schema but NOT in {TARGET_DB} yet:")
        for name in skipped:
            print(f"   ⚠️   {name}")
        print(f"    (You may need to import those collections too)\n")

    # ── Verify ────────────────────────────────────────────────────────────────
    print(f"📋  Final _schema in '{TARGET_DB}':")
    for doc in target["_schema"].find({}, {"table": 1, "name": 1, "fields": 1}):
        table  = doc.get("table", doc.get("name", "unknown"))
        fields = doc.get("fields", [])
        print(f"   {table:30s} ({len(fields)} fields)")

    print(f"\n🔄  Now restart Trino:")
    print(f"    docker restart $(docker ps -qf 'name=trino')")
    print(f"\n🔍  Then test in Superset SQL Lab:")
    print(f"    SELECT * FROM mongo.app_db.users LIMIT 5;")
    print(f"    SELECT * FROM mongo.app_db.levels LIMIT 5;\n")

    client.close()


if __name__ == "__main__":
    main()
