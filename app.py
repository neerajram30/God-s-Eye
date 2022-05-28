

import os
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

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
if(conn):
    print("connection established")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
     


def predict(img_path, knn_clf=None, model_path=None, threshold=0.6): # 6 needs 40+ accuracy, 4 needs 60+ accuracy
    if knn_clf is None and model_path is None:
        raise Exception("Must supply knn classifier either thourgh knn_clf or model_path")
    # Load a trained KNN model (if one was passed in)
    if knn_clf is None:
        with open(model_path, 'rb') as f:
            knn_clf = pickle.load(f)
    # Load image file and find face locations
    img = img_path
    face_box = face_recognition.face_locations(img)
    # If no faces are found in the image, return an empty result.
    if len(face_box) == 0:
        return []
    # Find encodings for faces in the test iamge
    faces_encodings = face_recognition.face_encodings(img, known_face_locations=face_box)
    # Use the KNN model to find the best matches for the test face
    closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=2)
    matches = [closest_distances[0][i][0] <= threshold for i in range(len(face_box))]
    # Predict classes and remove classifications that aren't within the threshold
    return [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings),face_box,matches
    )]


camera =cv2.VideoCapture(0)

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



            small_frame=cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            predictions = predict(small_frame, model_path="classifier/trained_knn_model.clf")



            for name, (top, right, bottom, left) in predictions:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                # cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                #cv2.putText(frame, name, (left-10,top-6), font, 0.8, (255, 255, 255), 1)
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 

           

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/newcase')
def newcase():
    return render_template('newcase.html')    

@app.route('/newcase', methods=['POST'])
def casedetails():
    
    UPLOAD_FOLDER = 'static/uploads/'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #print('upload_image filename: ' + filename)
 
        cursor.execute("INSERT INTO upload VALUES (%s)", (filename,))
        conn.commit()
 
        flash('Image successfully uploaded and displayed below')
        return render_template('index.html', filename=filename)
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)
    return redirect('/newcase')    

@app.route('/train', methods=['GET'] ['POST'])
def train():
    
    
if __name__=='__main__':
    app.run(debug=True)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=2204, threaded=True)