from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi

MONGO_URI = "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0"
DB_NAME = "arc_dev"

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client[DB_NAME]

now = datetime.now(timezone.utc)

def ensure_collection(name, validator=None):
    existing = db.list_collection_names()
    if name in existing:
        return
    opts = {}
    if validator:
        opts["validator"] = validator
        opts["validationLevel"] = "moderate"  # use "strict" later if you want
    db.create_collection(name, **opts)

# --- 1) Create collections (light validators; you can tighten later) ---
ensure_collection("users", {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["userName", "password", "role", "children", "createdAt", "updatedAt"],
        "properties": {
            "userName": {"bsonType": "string"},
            "password": {"bsonType": "string"},
            "role": {"enum": ["student", "instructor"]},
            "children": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["childName", "personalityIndex"],
                    "properties": {
                        "childName": {"bsonType": "string"},
                        "personalityIndex": {"bsonType": "int"},
                        "personalityLabel": {"bsonType": "string"}
                    }
                }
            },
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"}
        }
    }
})

ensure_collection("tokens", {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["userId", "token", "isValid", "createdAt", "updatedAt"],
        "properties": {
            "userId": {"bsonType": "objectId"},
            "token": {"bsonType": "string"},
            "isValid": {"bsonType": "bool"},
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"}
        }
    }
})

# levels has embedded scenes[] (static)
ensure_collection("levels")
# levelFlows has embedded scenes[] (runtime)
ensure_collection("levelFlows")

ensure_collection("trainingModels", {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["level_id", "levelName", "scene", "modelLink", "accuracy", "blame", "lastModelUpdate"],
        "properties": {
            "level_id": {"bsonType": "objectId"},
            "levelName": {"bsonType": "string"},
            "scene": {"bsonType": "array"},
            "modelLink": {"bsonType": "string"},
            "accuracy": {"bsonType": ["double", "int"]},
            "blame": {"bsonType": "bool"},
            "lastModelUpdate": {"bsonType": "date"}
        }
    }
})

ensure_collection("promptTexts", {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["promptId", "promptText", "createdAt", "updatedAt"],
        "properties": {
            "promptId": {"bsonType": "string"},
            "promptText": {"bsonType": "string"},
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"}
        }
    }
})

# --- 2) Indexes for “FK lookups” ---
db.tokens.create_index([("userId", 1)])
db.levelFlows.create_index([("userId", 1), ("levelId", 1)])
db.trainingModels.create_index([("level_id", 1)])

# --- 3) Seed sample data (minimal but valid) ---
u = {
    "userName": "demo_student",
    "password": "hashed_pw_goes_here",
    "role": "student",
    "children": [{"childName": "Aarav", "personalityIndex": 0, "personalityLabel": "PDA_Autism"}],
    "createdAt": now,
    "updatedAt": now
}
user_id = db.users.insert_one(u).inserted_id

db.tokens.insert_one({
    "userId": user_id,
    "token": "demo_refresh_token",
    "isValid": True,
    "createdAt": now,
    "updatedAt": now
})

level = {
    "title": "Level 1: Conflict Resolution",
    "image360": "https://cdn.example/level1.jpg",
    "scanningAudio": "https://cdn.example/scan.mp3",
    "childA": "Earline",
    "childAStanding": True,
    "conflictObjectLink": "https://cdn.example/conflict.glb",
    "propsLinks": ["https://cdn.example/table.glb"],
    "published": True,
    "ready": True,
    "scenes": [
        {
            "sceneNo": 1,
            "sceneName": "Intro",
            "childAAnimation": "wave",
            "childBAnimation": "idle",
            "speeches": [{"text": "Welcome!", "audioLink": "https://cdn.example/a1.mp3", "visemeLink": "https://cdn.example/v1.json"}],
            "physicalInteractionRequired": False,
            "nlpModelLink": "s3://models/level1_scene1_eval.pkl",
            "blame": {"enabled": False, "modelLink": None},
            "createdAt": now
        }
    ],
    "createdAt": now,
    "updatedAt": now
}
level_id = db.levels.insert_one(level).inserted_id

db.trainingModels.insert_one({
    "level_id": level_id,
    "levelName": level["title"],
    "scene": [1],
    "modelLink": "s3://models/level1_scene1_eval.pkl",
    "originalSentences": ["Welcome!"],
    "generatedSentences": ["Hello and welcome"],
    "testingSentences": ["Hi"],
    "accuracy": 0.9,
    "blame": False,
    "lastModelUpdate": now,
    "createdAt": now,
    "updatedAt": now
})

db.levelFlows.insert_one({
    "userId": user_id,
    "levelId": level_id,
    "levelName": level["title"],
    "avatar": {"childA": "Earline", "childB": "Aarav"},
    "personality": {"childA": 4, "childB": 0},
    "levelComplete": False,
    "scenes": [
        {
            "sceneNo": 1,
            "purpose": "Intro",
            "physicalInteractionRequired": False,
            "backStoryTrigger": False,
            "backStoryTrigger2": False,
            "sceneComplete": True,
            "conversations": [
                {"text": "Hi!", "type": "user", "isCorrect": True, "blame": False, "timestamp": now},
                {"text": "Welcome!", "type": "child", "isCorrect": True, "blame": False, "timestamp": now}
            ]
        }
    ],
    "createdAt": now,
    "updatedAt": now
})

db.promptTexts.insert_one({
    "promptId": "BLAME_DETECTION_PROMPT_V1",
    "promptText": "Detect blaming language. Return true/false.",
    "createdAt": now,
    "updatedAt": now
})

print("Seed complete.")
print("user_id =", user_id)
print("level_id =", level_id)
