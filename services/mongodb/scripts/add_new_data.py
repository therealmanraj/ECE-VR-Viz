from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi

MONGO_URI = "mongodb+srv://therealmanraj:therealmanraj@cluster0.co763wd.mongodb.net/?appName=Cluster0"
DB_NAME = "arc_dev"

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client[DB_NAME]

now = datetime.now(timezone.utc)

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
