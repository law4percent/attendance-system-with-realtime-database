import cv2
import face_recognition
import pickle
import os

import firebase_admin
from firebase_admin import credentials, db, storage

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

# Path to the folder containing registered face images
folder_path = "resources/registered"
pathList = os.listdir(folder_path)
print("Image list:", pathList)

imgList = []
attendeeIDs = []

# Load images and their corresponding IDs
for path in pathList:
    img = cv2.imread(os.path.join(folder_path, path))
    if img is not None:
        imgList.append(img)
        attendeeIDs.append(os.path.splitext(path)[0])
    
    fileName = f"{folder_path}/{path}"
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)

print("IDs:", attendeeIDs)

# Function to find face encodings for a list of images
def findEncodings(imgList):
    encodeList = []
    for img in imgList:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Get the face encodings
        encodings = face_recognition.face_encodings(img_rgb)
        # Ensure at least one face encoding is found
        if encodings:
            encodeList.append(encodings[0])
        else:
            print("No face found in image")


    return encodeList

print("\nStart encoding...", end="")
encodeListKnown = findEncodings(imgList)
print(" Encoding complete")

print("\nPrinting the data...")
print(encodeListKnown)

encodeListKnownWithIDs = [encodeListKnown, attendeeIDs]

# Save the encodings and IDs to a file
with open(f"encoded_file/EncodeFile.p", "wb") as file:
    pickle.dump(encodeListKnownWithIDs, file)
print("\nFile saved")
