import pyrebase
config = {
    "apiKey": "AIzaSyCCdaRILPGbOyOOsV-6lR3cR1o7V6-Ezc8",
    "authDomain": "fitpal-12346.firebaseapp.com",
    "databaseURL": "https://fitpal-12346-default-rtdb.firebaseio.com",
    "projectId": "fitpal-12346",
    "storageBucket": "fitpal-12346.firebasestorage.app",
    "messagingSenderId": "964515344138",
    "appId": "1:964515344138:web:9bff1459b682b2bb77d4f3",
    "measurementId": "G-8GW9T38814"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()
