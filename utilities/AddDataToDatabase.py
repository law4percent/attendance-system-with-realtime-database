import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase app with credentials and database URL
try:
    cred = credentials.Certificate("path/to/serviceAccountKey.json")
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://realtimefaceattendance-3e65b-default-rtdb.firebaseio.com/",
            "storageBucket": "realtimefaceattendance-3e65b.appspot.com"
        }
    )
    print("Firebase initialized successfully.")
except ValueError:
    print("Firebase app already initialized or SDK is already in use.")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    
ref = db.reference("Attendee")

# Data to be written
data = {
    "4201400":
        {
            "name": "Lawrence Roble",
            "major": "Computer Vision and Embedded System",
            "year-start": 2021,
            "total_attendance": 15,
            "standing": "S",
            "year": 4,
            "last_attendance_time": "2022-11-3 12:33:13",
        },
    "4201401":
        {
            "name": "Floyd Mayweather",
            "major": "Embedded System Engineer",
            "year-start": 2011,
            "total_attendance": 115,
            "standing": "B",
            "year": 11,
            "last_attendance_time": "2022-11-3 12:33:13",
        },
    "4201402":
        {
            "name": "Manny Pacquiao",
            "major": "Full Stack Developer",
            "year-start": 2021,
            "total_attendance": 125,
            "standing": "A",
            "year": 6,
            "last_attendance_time": "2022-11-3 12:33:13",
        },
}

# Attempt to write data to the database
try:
    for key, value in data.items():
        ref.child(key).set(value)
    print("Data successfully written to Firebase.")
except Exception as e:
    print(f"Error writing data to Firebase: {e}")