

import os
from unittest import result
from flask import Flask, render_template, Response, request, redirect, url_for, flash
import urllib.request
import cv2
import face_recognition
import numpy as np
import pickle
from face_recognition.face_recognition_cli import image_files_in_folder
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
app=Flask(__name__)
app.secret_key = "super secret key"


DB_HOST = "localhost"
DB_NAME = "final_project"
DB_USER = "postgres"
DB_PASS = "12345"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
      


known_face_encodings=[]
known_face_names=[]
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

if(conn):
    print("connection established")

camera = cv2.VideoCapture(0)


def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
           
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)
            

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/')
def index():
    return render_template('index.html')


# @app.route('/video_feed')
# def video_feed():
#     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/newcase')
def newcase():
    return render_template('newcase.html')    

@app.route('/newcase', methods=['POST'])
def newcase_upload():
    m_name = request.form.get("m_name","")
    mobile = request.form.get("mobile","")
    location = request.form.get("location","")
    face_img = request.files['face_img']

    if m_name == "":
        msg = "Please fill in name"
        return render_template("newcase.html", message = msg)

    if mobile == "":
        msg = "Please fill in mobile"
        return render_template("newcase.html", message = msg)    
    if location == "":
        msg = "Please fill in location"
        return render_template("newcase.html", message = msg)
    if face_img == "":
        msg = "Please upload in face image"
        return render_template("newcase.html", message = msg)
    if face_img and allowed_file(face_img.filename):
        filename = secure_filename(face_img.filename)
        face_img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))    
    cur = conn.cursor()
    cur.execute("INSERT INTO cases (m_name, mobile, location, face_img) VALUES('{m_name}', '{mobile}', '{location}', '{face_img}')")
    try:
        conn.commit()
    except psycopg2.Error as e:
        msg="Database error: " + e
        return render_template("newcase.html", message = msg)
    cur.close()
    return redirect('/')        


    
    
    

@app.route('/train', methods=['GET'])
def train():
    cur = conn.cursor()
    cur.execute(f"SELECT m_name,face_img FROM cases")
    try:
        conn.commit()
    except psycopg2.Error as e:
        msg="Database error: " + e
        return render_template("newcase.html", message = msg)
    results =cur.fetchall()
    for i in results:
        name = i[0]
        image = i[1]
        face_image = face_recognition.load_image_file(image)
        face_encoding = face_recognition.face_encodings(face_image)[0]

        known_face_encodings.append(face_encoding)
        known_face_names.append(name) 
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')        
    cur.close()        
    
if __name__=='__main__':
    app.run(debug=True)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=2204, threaded=True)