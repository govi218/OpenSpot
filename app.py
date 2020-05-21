import os
import firebase_admin
import datetime as dt
import hashlib
import time as tm
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, render_template, request
from _datetime import date
from _datetime import datetime

app = Flask(__name__)

# Use a service account
cred = credentials.Certificate('./credentials.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

### GET Requests

# TODO: Create a POST endpoint that displays a form after taking a business name in query string
@app.route("/form", methods=['get'])
def form():
    place = request.args.get("place")
    info_ref = db.collection("businesses").document(place).collection("data").document("info")

    info = info_ref.get().to_dict()
    start_time_str = info["start_time"]

    start_time = datetime.strptime(start_time_str, '%H:%M')

    end_time_str = info["end_time"]
    end_time = datetime.strptime(end_time_str, '%H:%M')

    num_employees = info["num_employees"]
    time_per_person = info["time_per_person"]

    times = []
    schedule = []

    curr_time = start_time

    while curr_time < end_time:
        times.append(curr_time.strftime('%H:%M'))
        curr_time = curr_time + dt.timedelta(minutes=int(time_per_person))

    today = datetime.now().strftime("%m-%d-%Y, %H:%M:%S")

    place_ref = db.collection("businesses").document(place).collection("data").document("dates").collection(today).stream()

    # potential race condition in here
    for entry in place_ref:
        if entry.id == "info":
            continue
        schedule.append({'time': entry.id, 'people': entry.to_dict()})
        time_id = entry.id
        time_dict = entry.to_dict()
        if len(time_dict) < 10:
                times.append(time_id)

    return render_template("./form.html",step_no="1", place=place, times=times)

# GET endpoint to serve an onboarding form for a new business
@app.route("/onboard", methods=['get'])
def onboard():
    places = []
    for coll in db.collections():
        print(coll.id)
        places.append(coll.id)
    print(places)
    return render_template("./onboard.html", places=places)

@app.route("/", methods=['get'])
def admin():
    return render_template("./index.html")


@app.route("/admin", methods=['get'])
def index():
    return render_template("./login.html")


### POST Requests

@app.route('/handle_data', methods=['post'])
def handle_data():
    time = request.form['timeSelect'].strip()
    today = datetime.now().strftime("%m-%d-%Y")
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').strftime('%m-%d-%Y')

    info_ref = db.collection("businesses").document(request.form["times"]).collection("data").document("info")
    place_ref = db.collection("businesses").document(request.form["times"]).collection("data").document("dates").collection(date).document(time)

    info = info_ref.get()
    doc = place_ref.get()

    max_people = 0
    num_employees = 0
    len_queue = 0

    if info.exists:
        print(info.to_dict)
        max_people = int(info.to_dict()['max_people'])
        num_employees = int(info.to_dict()['num_employees'])
    else:
        return "No such place"

    if doc.exists:
        print(len(doc.to_dict()))
        len_queue = len(doc.to_dict())
        if len_queue+num_employees == max_people:
            return "This slot is full"
        place_ref.update({str(len_queue+1): {
            'name': request.form['name'],
            'email': request.form["email"],
            'phone': request.form["phone"]
        }})
    else:
        place_ref.set({str(len_queue+1): {
            'name': request.form['name'],
            'email': request.form["email"],
            'phone': request.form["phone"]
        }})

    return "Your response has been submitted!"


# POST endpoint for a business to add itself to DB
@app.route('/handle_onboard', methods=['post'])
def handle_onboard():
    start_time_str = request.form['openTime']
    start_time = datetime.strptime(start_time_str, '%H:%M').strftime('%H:%M')

    end_time_str = request.form['closeTime']
    end_time = datetime.strptime(end_time_str, '%H:%M').strftime('%H:%M')

    time_per_person = request.form["time_per_person"]
    max_people = request.form["max_people"]
    num_employees = request.form["num_employees"]
    business_name = request.form["businessName"]

    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    info_ref = db.collection("businesses").document(business_name).collection("data").document("info")
    info_ref.set({
        "password_hash": pass_hash,
        "email": request.form["email"],
        "business_name": business_name,
        "num_employees": num_employees,
        "max_people": max_people,
        "submit_time": int(tm.time()),
        "start_time": start_time,
        "end_time": end_time,
        "time_per_person": int(time_per_person)
    })

    return "Your response has been submitted! Your business' unique link is: <a href=\"/form?place="+business_name+"\">https://open-spot.herokuapp.com/form?place="+business_name+"</a>. <br><br><br> You can check your reservations by going to the <a href=\"/admin\">admin page</a> and typing the password you just created."

@app.route("/handle_admin_creds", methods=['get', 'post'])
def handle_admin_creds():
    email = request.form["email"]
    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if email == "" or password == "":
        return "400"


    # subcollection query goes here
    coll = db.collection_group("data").where("email","==",email).stream()
    data = []

    for d in coll:
        doc_dict = d.to_dict()
        if doc_dict["password_hash"] != pass_hash:
            return "403"

        info_ref = db.collection("businesses").document(d.to_dict()["business_name"]).collection("data").document("info")
        place_ref = db.collection("businesses").document(d.to_dict()["business_name"]).collection("data").document("dates").collections()
        # places = place_ref.get()
        info = info_ref.get()

        # print(places.to_dict())
        # print(info.to_dict())

        for y in place_ref:
            coll = y.stream()
            colls = []
            for d in coll:
                apt_dict = d.to_dict()
                colls.append({
                    "time": d.id,
                    "appointments":[apt_dict[a] for a in apt_dict]
                })
                # print(d.id, ": ", d.to_dict())
            # print('====')
            data.append({
                'id': y.id,
                'dates': colls
            })
        print(data)
    return render_template("./reservations.html", data=data)


if __name__ == '__main__':
    if os.environ.get('APP_DEBUG') is True:
        app_debug_state = True
    else:
        app_debug_state = False
    port = os.environ.get('PORT', 3000)
    app.run(debug=app_debug_state, host='0.0.0.0', port=port)
