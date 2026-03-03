"""
seed_mongo.py
─────────────────────────────────────────────────────────────────────────────
Populates a local MongoDB instance with dummy data that mirrors the schema:

  users · tokens · levelFlows · levelFlowscenes · levels
  level_scenes · trainingModels · promptModel

Run:
  pip install pymongo faker
  python3 seed_mongo.py

By default connects to  mongodb://localhost:27017  and uses database  app_db.
Override with env vars:
  MONGO_URI=mongodb://user:pass@host:27017
  MONGO_DB=my_database
─────────────────────────────────────────────────────────────────────────────
"""

import os
import random
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from faker import Faker
import pymongo

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0"
MONGO_DB  = os.getenv("MONGO_DB",  "app_db")

NUM_USERS   = 10
NUM_LEVELS  = 8
NUM_SCENES_PER_LEVEL = 4   # level_scenes rows per level
NUM_FLOWS_PER_USER   = 3   # levelFlows per user

fake = Faker()

def now():
    return datetime.now(tz=timezone.utc)

def rand_past(days=180):
    return now() - timedelta(days=random.randint(0, days),
                             hours=random.randint(0, 23))

# ── Helpers ───────────────────────────────────────────────────────────────────
def make_object_id():
    return ObjectId()

# ── Seed functions ─────────────────────────────────────────────────────────────

def seed_users(db):
    docs = []
    for _ in range(NUM_USERS):
        docs.append({
            "_id":           make_object_id(),
            "userName":      fake.user_name(),
            "password":      fake.sha256(),          # hashed placeholder
            "role":          random.choice(["admin", "teacher", "parent"]),
            "children":      [{"name": fake.first_name(), "age": random.randint(4, 12)}
                              for _ in range(random.randint(1, 3))],
            "created":       rand_past(),
            "updatedAtTime": rand_past(30),
        })
    db.users.drop()
    db.users.insert_many(docs)
    print(f"  users          → {len(docs)} docs")
    return [d["_id"] for d in docs]


def seed_tokens(db, user_ids):
    docs = []
    for uid in user_ids:
        docs.append({
            "_id":           make_object_id(),
            "userId":        uid,
            "token":         fake.uuid4(),
            "valid":         random.choice([True, True, False]),
            "created":       rand_past(),
            "updatedAtTime": rand_past(30),
        })
    db.tokens.drop()
    db.tokens.insert_many(docs)
    print(f"  tokens         → {len(docs)} docs")


def seed_levels(db):
    docs = []
    for i in range(1, NUM_LEVELS + 1):
        scene_refs = [{"sceneNo": s, "ref": str(make_object_id())}
                      for s in range(1, NUM_SCENES_PER_LEVEL + 1)]
        docs.append({
            "_id":            make_object_id(),
            "title":          f"Level {i}: {fake.catch_phrase()}",
            "scanningAudio":  f"audio/level{i}_scan.mp3",
            "image360":       f"images/360/level{i}.jpg",
            "childA":         fake.first_name(),
            "childAStanding": random.choice([True, False]),
            "objectOfConflicts": random.choice(["toy", "book", "ball", "tablet"]),
            "propsOnTable":   random.choice(["cup", "pen", "eraser"]),
            "published":      random.choice([True, False]),
            "create":         rand_past(365),
            "update":         rand_past(30),
            "scenes":         scene_refs,
        })
    db.levels.drop()
    db.levels.insert_many(docs)
    print(f"  levels         → {len(docs)} docs")
    return [d["_id"] for d in docs]


def seed_level_scenes(db, level_ids):
    docs = []
    animations = ["idle", "walk", "sit", "point", "wave", "nod"]
    for lid in level_ids:
        for scene_no in range(1, NUM_SCENES_PER_LEVEL + 1):
            docs.append({
                "_id":               make_object_id(),
                "levelId":           lid,          # logical FK
                "sceneNo":           scene_no,
                "sceneName":         f"Scene {scene_no} – {fake.bs()}",
                "childAAnimation":   random.choice(animations),
                "childBAnimation":   random.choice(animations),
                "physicalInteraction": random.choice([True, False]),
                "nlpModelLink":      f"models/nlp/scene{scene_no}.bin" if random.random() > 0.3 else None,
                "nlpLastUpdate":     rand_past(60) if random.random() > 0.3 else None,
                "create":            rand_past(365),
                "blame":             {"editor": fake.name(), "reason": fake.sentence()},
                "hint":              fake.sentence(),
                "speech":            {
                    "childA": fake.sentence(),
                    "childB": fake.sentence(),
                },
            })
    db.level_scenes.drop()
    db.level_scenes.insert_many(docs)
    print(f"  level_scenes   → {len(docs)} docs")


def seed_training_models(db, level_ids):
    docs = []
    for lid in level_ids:
        for scene_no in range(1, NUM_SCENES_PER_LEVEL + 1):
            orig  = [fake.sentence() for _ in range(random.randint(5, 15))]
            gen   = [fake.sentence() for _ in range(random.randint(10, 30))]
            test  = [fake.sentence() for _ in range(random.randint(5, 10))]
            docs.append({
                "_id":                make_object_id(),
                "level":              {"id": lid, "sceneNo": scene_no},
                "scene":              {"sceneNo": scene_no, "levelId": lid},
                "modelLink":          f"models/trained/level_{lid}_scene{scene_no}.bin",
                "lastModelUpdate":    rand_past(90),
                "originalSentences":  orig,
                "generatedSentences": gen,
                "testingSentences":   test,
                "accuracy":           round(random.uniform(0.60, 0.99), 4),
                "blame":              random.choice([True, False]),
                "create":             rand_past(365),
                "update":             rand_past(30),
            })
    db.trainingModels.drop()
    db.trainingModels.insert_many(docs)
    print(f"  trainingModels → {len(docs)} docs")


def seed_level_flows(db, user_ids, level_ids):
    docs = []
    for uid in user_ids:
        for _ in range(NUM_FLOWS_PER_USER):
            lid = random.choice(level_ids)
            docs.append({
                "_id":              make_object_id(),
                "userId":           uid,
                "levelId":          lid,
                "levelName":        f"Level flow for {lid}",
                "avatarInfo":       {"avatar": random.choice(["fox", "bear", "cat"]),
                                     "color": fake.color_name()},
                "personality_childB": random.choice(["shy", "bold", "curious"]),
                "personality_childA": random.choice(["shy", "bold", "curious"]),
                "levelComplete":    random.choice([True, False]),
                "create":           rand_past(180),
                "update":           rand_past(30),
                "scene":            {"currentScene": random.randint(1, NUM_SCENES_PER_LEVEL)},
            })
    db.levelFlows.drop()
    db.levelFlows.insert_many(docs)
    print(f"  levelFlows     → {len(docs)} docs")
    return [d["_id"] for d in docs]


def seed_level_flow_scenes(db, flow_ids):
    docs = []
    for fid in flow_ids:
        num_scenes = random.randint(2, NUM_SCENES_PER_LEVEL)
        for sno in range(1, num_scenes + 1):
            docs.append({
                "_id":                  make_object_id(),
                "levelFlowId":          fid,          # logical FK
                "sceneNo":              sno,
                "purpose":              random.choice(["intro", "conflict", "resolution", "outro"]),
                "userPhysicalInteraction": random.choice([True, False]),
                "backStoryTrigger":     random.choice([True, False]),
                "backStoryTrigger2":    random.choice([True, False]),
                "sceneComplete":        random.choice([True, False]),
                "create":               rand_past(180),
                "conversations":        [
                    {"speaker": random.choice(["childA", "childB"]),
                     "text": fake.sentence(),
                     "timestamp": str(rand_past(30))}
                    for _ in range(random.randint(2, 8))
                ],
            })
    db.levelFlowscenes.drop()
    db.levelFlowscenes.insert_many(docs)
    print(f"  levelFlowscenes→ {len(docs)} docs")


def seed_prompt_models(db):
    prompts = [
        ("conflict_intro",    "You are mediating a conflict between two children. Start by…"),
        ("empathy_probe",     "Ask the child how the other child might be feeling right now."),
        ("resolution_guide",  "Guide the children toward a fair resolution by asking…"),
        ("backstory_reveal",  "Reveal the backstory of the conflict gently by saying…"),
        ("celebration",       "Celebrate the successful resolution with positive reinforcement."),
    ]
    docs = []
    for pid, (name, text) in enumerate(prompts, 1):
        docs.append({
            "_id":        make_object_id(),
            "id":         f"PROMPT_{pid:03d}",
            "promptText": text,
            "create":     rand_past(365),
            "update":     rand_past(30),
        })
    db.promptModel.drop()
    db.promptModel.insert_many(docs)
    print(f"  promptModel    → {len(docs)} docs")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    client = pymongo.MongoClient(MONGO_URI)
    db     = client[MONGO_DB]

    print(f"\nConnected to  {MONGO_URI}  →  database: {MONGO_DB}\n")
    print("Seeding collections …")

    user_ids  = seed_users(db)
    seed_tokens(db, user_ids)
    level_ids = seed_levels(db)
    seed_level_scenes(db, level_ids)
    seed_training_models(db, level_ids)
    flow_ids  = seed_level_flows(db, user_ids, level_ids)
    seed_level_flow_scenes(db, flow_ids)
    seed_prompt_models(db)

    print("\n✅  Done! Collections in", MONGO_DB, ":")
    for name in sorted(db.list_collection_names()):
        print(f"   {name:25s} {db[name].count_documents({}):>4} docs")

    client.close()


if __name__ == "__main__":
    main()


# python3 -c "
# import pymongo
# from datetime import datetime
# client = pymongo.MongoClient('mongodb+srv://admin:8nAp7UJiLys1NcaN@cluster0.ix4lzb2.mongodb.net')
# db = client['langara-dev']
# first_doc = db['_schema'].find_one()
# if first_doc:
#     created = first_doc['_id'].generation_time
#     print(f'_schema created at: {created}')
#     print(f'Total schema definitions: {db[\"_schema\"].count_documents({})}')
# else:
#     print('❌ _schema collection not found or empty in langara-dev')
# "