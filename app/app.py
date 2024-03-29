from crypt import methods
from dotenv import load_dotenv
import os
import re
from sre_constants import SUCCESS
from cv2 import split
from flask import Flask, render_template, Response, request, redirect, url_for, flash, session
import urllib.request
import cv2
import face_recognition
import numpy as np
from face_recognition.face_recognition_cli import image_files_in_folder
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
from datetime import date,datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ipregistry import IpregistryClient
import json
from geopy.geocoders import Nominatim
import ast
from db import conn

load_dotenv()
# IP_REGISTRY_KEY = os.getenv('IP_REGISTRY_KEY')
# resource = urllib.request.urlopen(IP_REGISTRY_KEY)
# payload = resource.read().decode('utf-8')

# geoLoc = Nominatim(user_agent="GetLoc")



app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET")

# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASS = os.getenv("DB_PASS")

# DB_HOST = "localhost"
# DB_NAME = "final_project"
# DB_USER = "postgres"
# DB_PASS = "12345"

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
known_face_encodings = []
known_face_names = []
TOLERANCE = 0.6



face_locations = []
face_encodings = []
face_names = []
process_this_frame = True



screenshorts=[]
locations =[]
names =[]
dates=[]
# screenshort =""
# location =""


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
if(conn):
    print("Database set up completed and connection established succesfully")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


camera = cv2.VideoCapture(0)


# def verifyImage(cases):
#     train_images = []
#     known_face =[]
#     for i in cases:
#         train_images.append(i[5])
#         known_face.append(i[1])
#         face_locations = face_recognition.face_locations(rgb_small_frame)
#         face_encodings = face_recognition.face_encodings(rgb_small_frame)
#         print(face_encodings)
#     return train_images+known_face
def Remove(duplicate):
    final_list = []
    for num in duplicate:
        if num not in final_list:
            final_list.append(num)
    return final_list

def gen_frames():
    # latitude = json.loads(payload)['location']['latitude']
    # longitude = json.loads(payload)['location']['longitude']
    # la=str(latitude)
    # lo=str(longitude)
    # locname = geoLoc.reverse(la+','+lo)
    
    while True:
        success, frame = camera.read()

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
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding, TOLERANCE)
                name = "Unknown"
                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                path = 'static/screenshots/'
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    # num = 0
                    # while num < 3:
                    #     cv2.imwrite(os.path.join(
                    #         path, name+str(num)+'.jpg'), frame)
                    #     screenshorts.append(name+str(num)+'.jpg')    
                    #     # filename = secure_filename(name+str(num)+'.jpg'.filename)    
                    #     # name+str(num)+'.jpg'.save(os.path.join(app.config['path'], filename))
                    #     # screenshorts.append(name+str(num)+'.jpg')
                    #     num = num+1
                    cv2.imwrite(os.path.join(path, name+str(1)+'.jpg'), frame)
                    # locations.append(locname.address)
                    screenshorts.append(name+str(1)+'.jpg')
                    names.append(name)
                    now=datetime.now()
                    dt_str=now.strftime("%d/%m/%Y")
                    dates.append(dt_str)
                face_names.append(name)

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35),
                              (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()
    cv2.destroyAllWindows()


@app.route('/')
def index():
    # if 'loggedin' in session:
    #     return render_template('policehome.html')
    # scr = Remove(screenshorts)
    # print(scr)
    # loc =Remove(locations)
    # print(loc)
    # print(locations)
    
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    scr = Remove(screenshorts)
    loc =Remove(locations)
    name =Remove(names)
    date =Remove(dates)

    print("--------------------------",scr)
    print("--------------------------",loc)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("INSERT INTO spoted (image, location, name, date) VALUES (%s,%s,%s,%s)",(scr,loc,name,date))
    conn.commit()
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/newcase')
def newcase():
    if 'loggedin' in session:
        return render_template('newcase.html')
    return redirect('login')


@app.route('/newcase', methods=['POST'])
def casedetails():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    m_name = request.form['m_name']
    mobile = request.form['mobile']
    age = request.form['age']
    m_date = date.today()
    file = request.files['file']
    location = request.form['location']

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #print('upload_image filename: ' + filename)
        cursor.execute("INSERT INTO newcases (m_name,mobile,date,age,file,location) VALUES (%s,%s,%s,%s,%s,%s)",
                       (m_name, mobile, m_date, age, filename, location,))
        conn.commit()

        flash('Image successfully uploaded and displayed below')
        # return render_template('index.html', filename=filename)
        return redirect(url_for('policehome'))
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/train', methods=['GET'])
def train():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT m_name, file  FROM newcases")
    results = cursor.fetchall()

    for i in results:
        m_name = i[0]
        m_image = i[1]
        # print(m_name,m_image)
        image_directory = os.path.join(app.config['UPLOAD_FOLDER'], m_image)
        missing_image = face_recognition.load_image_file(image_directory)
        missing_face_encoding = face_recognition.face_encodings(missing_image)[0]

        known_face_encodings.append(missing_face_encoding)
        known_face_names.append(m_name)
        print("++++++++ Training done for "+m_name +
              " with image: "+m_image+" ++++++++")
    flash("Refresh completed.")
    return redirect(url_for('policehome'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('policehome'))
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'police_id' in request.form and 'password' in request.form:
        police_id = request.form['police_id']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM police WHERE police_id = %s', (police_id,))
        # Fetch one record and return result
        account = cursor.fetchone()

        if account:
            password_rs = account['password']
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['police_id'] = account['police_id']
                # Redirect to home page
                return redirect(url_for('policehome'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect user credentials')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'loggedin' in session:
        return redirect(url_for('policehome'))
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'police_id' in request.form and 'password' in request.form and 'mobile' in request.form:
        # Create variables for easy access
        police_id = request.form['police_id']
        p_name = request.form['p_name']
        station = request.form['station']
        post = request.form['post']
        mobile = request.form['mobile']
        password = request.form['password']

        _hashed_password = generate_password_hash(password)
        print(_hashed_password)
        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM police WHERE police_id = %s', (police_id,))
        account = cursor.fetchone()
      
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        # elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        #     flash('Invalid email address!')
        # elif not re.match(r'[A-Za-z0-9]+', username):
        #     flash('Username must contain only characters and numbers!')
        # elif not username or not password or not email:
        #     flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            try:

                cursor.execute("INSERT INTO police (police_id, p_name, station, post, mobile, password) VALUES (%s,%s,%s,%s,%s,%s)",
                           (police_id, p_name, station, post, mobile, _hashed_password,))
                conn.commit()
                flash('You have successfully registered!')
                return redirect(url_for('login'))
            except (Exception, psycopg2.DatabaseError) as error:
                print('error is --------------'+error)
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('register.html')


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('p_id', None)
    session.pop('police_id', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/police_home')
def policehome():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("select * from newcases")
    data = cursor.fetchall()
    
    if 'loggedin' in session:
        return render_template('policehome.html', value=data)
    return redirect(url_for('login'))

@app.route('/results')
def results():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("select * from spoted")
    data = cursor.fetchall()
    print("data= ",data)
    # for x in data:
    #     img=x[1]
    #     loc=x[2]
    # dictionary =eval(img)
    # dictionary1 =eval(loc)
    # print(dictionary1)
    # final_data =np.hstack((dictionary,dictionary1))
    # f_d = Remove(final_data)
    
    # loc_data=json.loads(loc)
        
    return render_template('results.html', value=data)
@app.route('/user')
def userrend():
    return render_template('user.html')



@app.route('/user' ,methods=['POST','GET'])
def user():
    if request.method == 'POST':
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        u_name = request.form['u_name']
        phone = request.form['phone']
        location = request.form['location']
        file = request.files['file']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #print('upload_image filename: ' + filename)
            cursor.execute("INSERT INTO users (name,mobile,location,file) VALUES (%s,%s,%s,%s)",
                       (u_name, phone, location, filename,))
            conn.commit()

            flash('Image successfully uploaded and displayed below')
        # return render_template('index.html', filename=filename)
            return redirect(url_for('user'))

@app.route('/userupload')
def userupload():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # cursor.execute("select * from newcases")
    # cases = cursor.fetchall()
    # match = verifyImage(cases)
    # print(match)
    cursor.execute("select * from users")
    data = cursor.fetchall()
    return render_template('useruploads.html', value=data)


@app.route('/admin', methods=['POST','GET'])
def admin():
    if 'admin-loggedin' in session:
        return redirect(url_for('adminhome'))
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'a_name' in request.form and 'password' in request.form:
        a_name = request.form['a_name']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM admin WHERE a_name = %s', (a_name,))
        # Fetch one record and return result
        account = cursor.fetchone()

        if account:
            password_rs = account['password']
            # If account exists in users table in out database
            if (password_rs == password):
                # Create session data, we can access this data in other routes
                session['admin-loggedin'] = True
                session['a_name'] = account['a_name']
                # Redirect to home page
                return redirect(url_for('adminhome'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect user credentials')
    
    return render_template('admin.html')

@app.route('/adminhome')
def adminhome():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("select * from newcases")
    data = cursor.fetchall()
    
    if 'admin-loggedin' in session:
        return render_template('adminhome.html', value=data)
    return redirect(url_for('admin'))

@app.route('/adminlogout')
def adminlogout():
    # Remove session data, this will log the user out
    session.pop('admin-loggedin', None)
    session.pop('a_name', None)
    
    return redirect(url_for('admin'))

# if __name__=='__main__':
    
#     app.run(debug=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2204, threaded=True)
