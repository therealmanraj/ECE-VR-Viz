"""
import_to_app_db.py
─────────────────────────────────────────────────────────────────────────────
Imports MongoDB Compass JSON exports into app_db.

Usage:
  python3 import_to_app_db.py

Place your exported JSON files in a folder called  Data/  next to this script.
Files should be named like:
  langara-dev-client.users.json
  langara-dev-client.levels.json
  langara-dev-client.tokens.json
  langara-dev-client.levelFlows.json
  langara-dev-client.trainingModels.json
  langara-dev-client.promptModel.json
  ... etc

The script will:
  1. Auto-detect all .json files in the Data/ folder
  2. Extract the collection name from the filename
  3. Convert $oid, $date, $numberInt etc (Extended JSON) if present
  4. Insert all documents into app_db under the same collection name
  5. Skip duplicates safely (won't overwrite existing docs)
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
import pymongo

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI", "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0")
MONGO_DB   = os.getenv("MONGO_DB",  "app_db")
DATA_DIR   = Path(__file__).parent / "Data JSON"   # folder with your JSON files

# ── Extended JSON → native BSON types ─────────────────────────────────────────
def convert_extended_json(obj):
    """
    Recursively converts MongoDB Extended JSON types to native Python/BSON types.
    Handles both v1 ($oid, $date) and v2 ($oid as string) formats.
    """
    if isinstance(obj, dict):
        # ObjectId
        if "$oid" in obj:
            return ObjectId(obj["$oid"])

        # Date/Timestamp
        if "$date" in obj:
            val = obj["$date"]
            if isinstance(val, (int, float)):
                return datetime.fromtimestamp(val / 1000, tz=timezone.utc)
            if isinstance(val, str):
                # Try ISO format
                val = val.replace("Z", "+00:00")
                return datetime.fromisoformat(val)
            if isinstance(val, dict) and "$numberLong" in val:
                return datetime.fromtimestamp(int(val["$numberLong"]) / 1000, tz=timezone.utc)

        # NumberLong / NumberInt / NumberDecimal
        if "$numberLong" in obj:
            return int(obj["$numberLong"])
        if "$numberInt" in obj:
            return int(obj["$numberInt"])
        if "$numberDouble" in obj:
            return float(obj["$numberDouble"])
        if "$numberDecimal" in obj:
            return float(obj["$numberDecimal"])

        # Recurse into all keys
        return {k: convert_extended_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [convert_extended_json(item) for item in obj]

    return obj


# ── Extract collection name from filename ─────────────────────────────────────
def get_collection_name(filepath: Path) -> str:
    """
    Extracts collection name from filenames like:
      langara-dev-client.users.json        → users
      langara-dev-client.levelFlows.json   → levelFlows
      users.json                            → users
    """
    stem = filepath.stem  # filename without .json
    parts = stem.split(".")
    # If format is "database.collection", take the last part
    return parts[-1] if len(parts) > 1 else parts[0]


# ── Load a JSON file ──────────────────────────────────────────────────────────
def load_json_file(filepath: Path) -> list:
    """
    Loads a Compass JSON export. Handles both:
      - Array format:  [ {...}, {...} ]
      - JSONL format:  one JSON object per line
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # Try array format first
    if content.startswith("["):
        docs = json.loads(content)
        return docs if isinstance(docs, list) else [docs]

    # Try JSONL (one doc per line)
    docs = []
    for line in content.splitlines():
        line = line.strip().rstrip(",")  # handle trailing commas
        if line:
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return docs


# ── Import a single collection ────────────────────────────────────────────────
def import_collection(db, filepath: Path):
    collection_name = get_collection_name(filepath)
    print(f"\n  📂  {filepath.name}")
    print(f"       → collection: {collection_name}")

    # Load raw docs
    raw_docs = load_json_file(filepath)
    if not raw_docs:
        print(f"       ⚠️  File is empty, skipping.")
        return

    # Convert Extended JSON types
    docs = [convert_extended_json(doc) for doc in raw_docs]

    # Insert with duplicate protection
    collection = db[collection_name]
    inserted = 0
    skipped  = 0
    errors   = 0

    for doc in docs:
        try:
            collection.insert_one(doc)
            inserted += 1
        except pymongo.errors.DuplicateKeyError:
            skipped += 1
        except Exception as e:
            print(f"       ❌  Error inserting doc: {e}")
            errors += 1

    print(f"       ✅  {inserted} inserted  |  {skipped} skipped (duplicates)  |  {errors} errors")
    return inserted


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Check Data folder exists
    if not DATA_DIR.exists():
        print(f"\n❌  Data folder not found at: {DATA_DIR}")
        print(f"    Create a folder called 'Data' next to this script")
        print(f"    and put your JSON exports inside it.\n")
        return

    # Find all JSON files
    json_files = sorted(DATA_DIR.glob("*.json"))
    if not json_files:
        print(f"\n❌  No JSON files found in {DATA_DIR}")
        print(f"    Export your collections from Compass as JSON and place them there.\n")
        return

    print(f"\n🔗  Connecting to MongoDB …")
    client = pymongo.MongoClient(MONGO_URI)
    db     = client[MONGO_DB]
    print(f"✅  Connected  →  database: {MONGO_DB}")
    print(f"\n📋  Found {len(json_files)} JSON file(s) to import:\n")

    total_inserted = 0
    for filepath in json_files:
        result = import_collection(db, filepath)
        if result:
            total_inserted += result

    # Summary
    print(f"\n{'─'*50}")
    print(f"✅  Import complete!  {total_inserted} total documents inserted")
    print(f"\n📊  Collections now in '{MONGO_DB}':")
    for name in sorted(db.list_collection_names()):
        count = db[name].count_documents({})
        print(f"   {name:30s} {count:>5} docs")

    client.close()


if __name__ == "__main__":
    main()
