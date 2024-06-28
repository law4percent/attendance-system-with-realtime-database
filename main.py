import cv2
import face_recognition
import pickle
import numpy as np
import cvzone
import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db, storage

def initializeFirebaseApp():
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

def take_a_photo(success, frame, path, prev_id):
    if success:
        cv2.imwrite(f'{path}/{prev_id + 1}.jpg', frame)
        print("Image saved as captured_image.jpg\n")
        return 1
    else:
        print("Error: Could not capture image.\n")
        return 0

def extractIDsData(path):
    print("Extracting and loading the file...", end="")
    file = open(path, "rb")
    encodeListKnownIDs = pickle.load(file)
    file.close()
    print(" done!\n")

    return encodeListKnownIDs

def importMode(folderModePath):
    modePathList = os.listdir(folderModePath)
    imgModeList = []
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
    return imgModeList

def attendeeImgFromDatabase(bucket, imgAttendee, Id):
    blob = bucket.get_blob(f"resources/registered/{Id}.jpg")
    if not blob:
        print("JPG file not found, trying PNG...")
        blob = bucket.get_blob(f"resources/registered/{Id}.png")
        
        if not blob:
            print(f"Image with ID <{id}> cannot found.")
            imgAttendee = cv2.imread("resources/not_found_icon/user.jpg")
        else:
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgAttendee = cv2.imdecode(array, cv2.COLOR_BGR2RGB)
    else:
        array = np.frombuffer(blob.download_as_string(), np.uint8)
        imgAttendee = cv2.imdecode(array, cv2.COLOR_BGR2RGB)
    return imgAttendee

def updateAttendanceToDatabase(targetPath, attendeeInfo):
    ref = db.reference(targetPath)
    
    attendeeInfo["total_attendance"] += 1

    dateTimeObject = datetime.strptime(attendeeInfo["last_attendance_time"], "%Y-%m-%d %H:%M:%S")
    secondElapsed = (datetime.now() - dateTimeObject).total_seconds()

    if secondElapsed > 30:
        ref.child("total_attendance").set(attendeeInfo["total_attendance"])
        ref.child("last_attendance_time").set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return 1
    return 0

def main():
    imgModeList = importMode("resources/Modes")
    encodeListKnown, attendeeIDs = extractIDsData("encoded_file/EncodeFile.p")
    imgBackground = cv2.imread("resources/background/bg.png") 
    
    VIDEO_SOURCE = "https://192.168.1.3:8080/video"
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    frame_width, frame_height = [640, 480]
    cap.set(3, 640)
    cap.set(4, 480)

    frame_name = "FACIAL RECOGNITION"
    cap_register_path = "resources/registered"

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    count = 0
    modeType = 0
    counter = 0
    bucket = storage.bucket()
    Id = -1
    imgAttendee = []

    while True:
        success, img = cap.read()
        if not success:
            print("Unsuccessful to capture.")
            continue
        
        img = cv2.resize(img, (frame_width, frame_height))
        img = cv2.flip(img, 1)
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS =  cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurrFrame = face_recognition.face_locations(imgS)
        encodeCurrFrame = face_recognition.face_encodings(imgS, faceCurrFrame)

        # Overlay the actual frame onto background image
        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if faceCurrFrame:
            for encodeFace, faceLoc in zip(encodeCurrFrame, faceCurrFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                print(matches)
                print(faceDis)

                matchIndex = np.argmin(faceDis)
                if matches[matchIndex]:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = [55 + x1, 162 + y1, x2 - x1, y2 - y1]
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    Id = attendeeIDs[matchIndex]
                    if counter == 0:
                        cvzone.putTextRect(imgBackground, "Analyzing...", (100, 600), scale=1)
                        cv2.imshow(frame_name, imgBackground)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1

            if counter != 0:
                if counter == 1:
                    attendeeInfo = db.reference(f"Attendee/{Id}").get()
                    print(attendeeInfo)
                    imgAttendee = attendeeImgFromDatabase(bucket, imgAttendee, Id)

                    databasePath = f"Attendee/{Id}"
                    check = updateAttendanceToDatabase(databasePath, attendeeInfo)
                    if not check:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                    
                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        colors = [(255, 255, 255), (100, 100, 100), (50, 50, 50)]
                        fontScale = [1, 0.6, 0.5]
                        
                        (w, h), _ = cv2.getTextSize(attendeeInfo["name"], cv2.FONT_HERSHEY_COMPLEX, fontScale[0], 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(attendeeInfo["name"]), (808 + offset, 445), cv2.FONT_HERSHEY_COMPLEX, fontScale[0], colors[2], 1)
                        
                        cv2.putText(imgBackground, str(attendeeInfo["total_attendance"]), (861, 125), cv2.FONT_HERSHEY_COMPLEX, fontScale[0], colors[0], 1)
                        cv2.putText(imgBackground, str(attendeeInfo["major"]), (1006, 550), cv2.FONT_HERSHEY_COMPLEX, fontScale[2], colors[0], 1)
                        cv2.putText(imgBackground, str(Id), (1006, 493), cv2.FONT_HERSHEY_COMPLEX, fontScale[2], colors[0], 1)
                        cv2.putText(imgBackground, str(attendeeInfo["standing"]), (910, 625), cv2.FONT_HERSHEY_COMPLEX, fontScale[1], colors[1], 1)
                        cv2.putText(imgBackground, str(attendeeInfo["year"]), (1025, 625), cv2.FONT_HERSHEY_COMPLEX, fontScale[1], colors[1], 1)
                        cv2.putText(imgBackground, str(attendeeInfo["year-start"]), (1125, 625), cv2.FONT_HERSHEY_COMPLEX, fontScale[1], colors[1], 1)
                        imgAttendee_resized = cv2.resize(imgAttendee, (216, 216))
                        imgBackground[175:175 + 216, 909:909 + 216] = imgAttendee_resized

                counter += 1
                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgAttendee = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            modeType = 0
            counter = 0

        # if counter == 1:
        cv2.imshow(frame_name, imgBackground)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key to break
            break
        
    cap.release()
    cv2.destroyAllWindows()
    
    
if __name__ == "__main__":
    initializeFirebaseApp()
    main()