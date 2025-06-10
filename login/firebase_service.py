# login/firebase_service.py
from login.firebase_config import db

def save_user_profile(user_id, profile_data):
    db.collection('users').document(user_id).set(profile_data)

def get_user_profile(user_id):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None
