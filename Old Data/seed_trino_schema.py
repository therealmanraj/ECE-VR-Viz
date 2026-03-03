"""
seed_trino_schema.py
─────────────────────────────────────────────────────────────────────────────
Creates the _schema collection in app_db so Trino can correctly map all
collections with proper field types.

Collection names match what's actually in Compass:
  - levelflows        (not levelFlows)
  - levels
  - prompttexts       (not promptModel)
  - tokens
  - trainingmodels    (not trainingModels)
  - users

Run:
  python3 seed_trino_schema.py
─────────────────────────────────────────────────────────────────────────────
"""

import os
import pymongo

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0")
MONGO_DB  = os.getenv("MONGO_DB",  "app_db")


def build_schemas():
    return [

        # ── users ─────────────────────────────────────────────────────────────
        {
            "table": "users",
            "fields": [
                {"name": "_id",           "type": "ObjectId"},
                {"name": "userName",      "type": "varchar"},
                {"name": "password",      "type": "varchar"},
                {"name": "role",          "type": "varchar"},
                {"name": "children",      "type": "array"},
                {"name": "created",       "type": "timestamp"},
                {"name": "updatedAtTime", "type": "timestamp"},
            ]
        },

        # ── tokens ────────────────────────────────────────────────────────────
        {
            "table": "tokens",
            "fields": [
                {"name": "_id",           "type": "ObjectId"},
                {"name": "userId",        "type": "ObjectId"},
                {"name": "token",         "type": "varchar"},
                {"name": "valid",         "type": "boolean"},
                {"name": "created",       "type": "timestamp"},
                {"name": "updatedAtTime", "type": "timestamp"},
            ]
        },

        # ── levels ────────────────────────────────────────────────────────────
        {
            "table": "levels",
            "fields": [
                {"name": "_id",               "type": "ObjectId"},
                {"name": "title",             "type": "varchar"},
                {"name": "scanningAudio",     "type": "varchar"},
                {"name": "image360",          "type": "varchar"},
                {"name": "childA",            "type": "varchar"},
                {"name": "childAStanding",    "type": "boolean"},
                {"name": "objectOfConflicts", "type": "varchar"},
                {"name": "propsOnTable",      "type": "varchar"},
                {"name": "published",         "type": "boolean"},
                {"name": "create",            "type": "timestamp"},
                {"name": "update",            "type": "timestamp"},
                {"name": "scenes",            "type": "array"},
            ]
        },

        # ── levelflows ────────────────────────────────────────────────────────
        # NOTE: stored as lowercase "levelflows" in your Atlas
        {
            "table": "levelflows",
            "fields": [
                {"name": "_id",                "type": "ObjectId"},
                {"name": "userId",             "type": "ObjectId"},
                {"name": "levelId",            "type": "ObjectId"},
                {"name": "levelName",          "type": "varchar"},
                {"name": "avatarInfo",         "type": "json"},
                {"name": "personality_childB", "type": "varchar"},
                {"name": "personality_childA", "type": "varchar"},
                {"name": "levelComplete",      "type": "boolean"},
                {"name": "create",             "type": "timestamp"},
                {"name": "update",             "type": "timestamp"},
                {"name": "scene",              "type": "json"},
            ]
        },

        # ── trainingmodels ────────────────────────────────────────────────────
        # NOTE: stored as lowercase "trainingmodels" in your Atlas
        {
            "table": "trainingmodels",
            "fields": [
                {"name": "_id",                "type": "ObjectId"},
                {"name": "level",              "type": "json"},
                {"name": "scene",              "type": "json"},
                {"name": "modelLink",          "type": "varchar"},
                {"name": "lastModelUpdate",    "type": "timestamp"},
                {"name": "originalSentences",  "type": "array"},
                {"name": "generatedSentences", "type": "array"},
                {"name": "testingSentences",   "type": "array"},
                {"name": "accuracy",           "type": "double"},
                {"name": "blame",              "type": "boolean"},
                {"name": "create",             "type": "timestamp"},
                {"name": "update",             "type": "timestamp"},
            ]
        },

        # ── prompttexts ───────────────────────────────────────────────────────
        # NOTE: stored as "prompttexts" in your Atlas (not promptModel)
        {
            "table": "prompttexts",
            "fields": [
                {"name": "_id",        "type": "ObjectId"},
                {"name": "id",         "type": "varchar"},
                {"name": "promptText", "type": "varchar"},
                {"name": "create",     "type": "timestamp"},
                {"name": "update",     "type": "timestamp"},
            ]
        },

    ]


def main():
    client = pymongo.MongoClient(MONGO_URI)
    db     = client[MONGO_DB]

    print(f"\nConnected to {MONGO_URI}")
    print(f"Database: {MONGO_DB}\n")

    # Check existing collections
    existing = db.list_collection_names()
    print(f"📋  Collections found in {MONGO_DB}:")
    for name in sorted(existing):
        count = db[name].count_documents({})
        print(f"   {name:30s} {count:>5} docs")

    print(f"\n⚙️   Writing _schema collection for Trino …\n")

    # Drop and recreate _schema
    db["_schema"].drop()

    schemas = build_schemas()

    # Only include schemas for collections that actually exist
    existing_set    = set(existing)
    valid_schemas   = []
    skipped_schemas = []

    for s in schemas:
        if s["table"] in existing_set or s["table"] == "_schema":
            valid_schemas.append(s)
        else:
            skipped_schemas.append(s["table"])

    db["_schema"].insert_many(valid_schemas)

    print(f"✅  Inserted {len(valid_schemas)} schema definitions:\n")
    for s in valid_schemas:
        print(f"   ✅  {s['table']:30s} → {len(s['fields'])} fields")

    if skipped_schemas:
        print(f"\n⚠️   Skipped (collection not found in {MONGO_DB}):")
        for name in skipped_schemas:
            print(f"   ⚠️   {name}")

    print(f"\n🔄  Now restart your Trino container to pick up the schema:")
    print(f"    docker restart $(docker ps -qf 'name=trino')\n")

    print(f"🔍  Then verify in Trino CLI:")
    print(f"    SHOW TABLES FROM mongo.app_db;")
    print(f"    SELECT * FROM mongo.app_db.users LIMIT 5;\n")

    client.close()


if __name__ == "__main__":
    main()
