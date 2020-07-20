import face_recognition
import picamera
import numpy as np
from config import *
from PIL import Image, ImageDraw
from datetime import timedelta, datetime
import uuid

camera = picamera.PiCamera()
camera.rotation = rotation
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)


while True:
    #---------- Reload faces
    print("Loading known face image(s)")
    res = dbget()
    known_face_ids = res[0]
    known_face_names = res[1]
    trusted = res[2]
    announce = res[3]
    known_face_encoding = res[4]

    camera.capture(output, format="rgb")
    face_locations = face_recognition.face_locations(output)
    print("Found {} faces in image.".format(len(face_locations)))
    face_encodings = face_recognition.face_encodings(output, face_locations)

    faces = Image.fromarray(output)

    # Loop over each face found in the frame to see if it's someone we know.
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        match = face_recognition.compare_faces(known_face_encoding, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_face_encoding, face_encoding)
        best_match_index = np.argmin(face_distances)
        if match[best_match_index]:
            name = known_face_names[best_match_index]
            person_id = known_face_ids[best_match_index]
        else:
            unique = uuid.uuid1()
            name = "Unknown-" + str(unique)
            extrawidth = 0.2*(right - left)
            extraheight = 0.2*(bottom - top)
            face = faces.crop(((left - extrawidth), (top - 3*extraheight), (right + extrawidth), (bottom + extraheight)))
            image_loc = people_dir + str(unique) + ".JPG"
            face.save(image_loc)
            face.close()
            person_id = db_person_add(name)
            db_face_add(person_id, image_loc, face_encoding)
        #if same name within 9 seconds ignore
        timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        recent = set()
        for i in range(10):
            recent.add((datetime.now() - timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S"))
        if not (tempname == name and temptimestamp in temptimestamp):
            db.execute('INSERT INTO log ("person_id", "datetime", "distance") VALUES(?, ?, ?)',person_id, timestamp, float(face_distances[best_match_index]))
            print(name, timestamp, float(face_distances[best_match_index]))
            tempname = name
            temptimestamp = timestamp
