# login/firebase_service.py
from login.firebase_config import db

def get_user_profile(user_id, id_token):
    """Get user profile with authentication"""
    try:
        # Correct syntax: pass id_token as a keyword argument 'token'
        data = db.child('users').child(user_id).get(token=id_token).val()
        return data
    except Exception as e:
        print(f"Error getting profile: {e}")
        return None

def save_user_profile(user_id, profile_data, id_token):
    """Save user profile with authentication"""
    try:
        # Correct syntax: pass id_token as a keyword argument 'token'
        db.child("users").child(user_id).set(profile_data, token=id_token)
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False