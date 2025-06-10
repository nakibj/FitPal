from login.firebase_config import auth

class AuthManager:
    def signup(self, email, password):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            return user
        except Exception as e:
            return str(e)

    def login(self, email, password):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            return user
        except Exception as e:
            return str(e)
