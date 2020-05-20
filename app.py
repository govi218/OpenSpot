import os
import firebase_admin
import datetime
import hashlib
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, render_template, request

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
    place_ref = db.collection("businesses").document(place).collection("data").stream()

    times = []
    schedule = []

    # potential race condition in here
    for doc in place_ref:
        if doc.id == "info":
            continue
        # print("Time: " + doc.id + ", num ppl: " + str(len(doc.to_dict())))
        schedule.append({'time': doc.id, 'people': doc.to_dict()})
        time_id = doc.id
        time_dict = doc.to_dict()
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


@app.route("/admin", methods=['get'])
def admin():
    return render_template("./login.html")


### POST Requests

@app.route('/handle_data', methods=['post'])
def handle_data():
    time = request.form['timeSelect'].strip()

    place_ref = db.collection("businesses").document(request.form["field0"]).collection("data").document(time)
    info_ref = db.collection("businesses").document(request.form["field0"]).collection("data").document("info")

    info = info_ref.get().to_dict()
    doc = place_ref.get()
    if len(doc.to_dict()) < int(info["max_people"]):
            place_ref.update({str(len(doc.to_dict())+1): {
                'name': request.form['field1'],
                'email': request.form["field2"],
                'phone': request.form["field4"]
            }})
    else:
        return "That time slot has already been filled!"

    return "Your response has been submitted!"


# POST endpoint for a business to add itself to DB
@app.route('/handle_onboard', methods=['post'])
def handle_onboard():
    start_time_str =request.form['openTime']
    start_time = datetime.datetime.strptime(start_time_str, '%H:%M')

    end_time_str = request.form['closeTime']
    end_time = datetime.datetime.strptime(end_time_str, '%H:%M')

    time_per_person = request.form["time_per_person"]
    max_people = request.form["max_people"]
    num_employees = request.form["num_employees"]
    business_name = request.form["businessName"]

    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    times = []
    curr_time = start_time
    while curr_time < end_time:
        times.append(curr_time.strftime('%H:%M'))
        curr_time = curr_time + datetime.timedelta(minutes=int(time_per_person))


    employees = []
    for i in range(int(num_employees)):
        employee = {
            'name': "staff"+str(i),
            'email': request.form["email"],
            'number': request.form["number"]
        }
        employees.append(employee)

    print(employees)
    for time in times:
        doc_ref = db.collection("businesses").document(business_name).collection("data").document(time)
        doc_ref.set({str(i+1): employees[i] for i in range(int(num_employees))})

    info_ref = db.collection("businesses").document(business_name).collection("data").document("info")
    info_ref.set({
        "password_hash": pass_hash,
        "email": request.form["email"],
        "business_name": business_name,
        "max_people": max_people
    })

    return "Your response has been submitted!"

@app.route("/handle_admin_creds", methods=['get', 'post'])
def handle_admin_creds():
    email = request.form["email"]
    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if email == "" or password == "":
        return "400"


    # subcollection query goes here
    coll = db.collection_group("data").where("email","==",email).stream()

    for d in coll:
        doc_dict = d.to_dict()
        if doc_dict["password_hash"] != pass_hash:
            return "403"

        place_ref = db.collection("businesses").document(d.to_dict()["business_name"]).collection("data").stream()
        for y in place_ref:
            print(y.id)
            print(y.to_dict())
    return render_template("./reservations.html")


if __name__ == '__main__':
    if os.environ.get('APP_DEBUG') is True:
        app_debug_state = True
    else:
        app_debug_state = False
    port = os.environ.get('PORT', 3000)
    app.run(debug=app_debug_state, host='0.0.0.0', port=port)
