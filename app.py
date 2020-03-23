import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, render_template, request

app = Flask(__name__)

# Use a service account
cred = credentials.Certificate('./credentials.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# TODO: Create a POST endpoint that displays a form after taking a business name in query string
@app.route("/form", methods=['get'])
def form():
    place = request.args.get("place")
    place_ref = db.collection(place).stream()

    times = []
    schedule = []

    # potential race condition in here
    for doc in place_ref:
        # print("Time: " + doc.id + ", num ppl: " + str(len(doc.to_dict())))
        schedule.append({'time': doc.id, 'people': doc.to_dict()})
        time_id = doc.id
        time_dict = doc.to_dict()
        if len(time_dict) < 10:
                times.append(time_id)

    return render_template("./form.html",step_no="1", place=place, times=times)

@app.route('/handle_data', methods=['post'])
def handle_data():
    print("Form data: ", request.form)
    print("Form data: ", request.form['timeSelect'])
    time = request.form['timeSelect'].strip()

    print(request.form['field0'])

    place_ref = db.collection(request.form["field0"]).document(time)

    print('??')

    doc = place_ref.get()
    print('??')
    if len(doc.to_dict()) < 10:
            db.collection(request.form['field0']).document(time).update({str(len(doc.to_dict())+1): {
                'name': request.form['field1'],
                'email': request.form["field2"],
                'phone': request.form["field4"]
            }})
    else:
        return "That time slot has already been filled!"

    # doc = place_ref.get()
    # print(u'Document data: {}'.format(doc.to_dict()))
    # schedule.append(doc.to_dict())
    # your code
    # return a response
    return "200 OK"

# TODO: Create a GET endpoint to serve an onboarding form for a new business

# TODO: Create a POST endpoint for a business to add itself to DB

@app.route("/test", methods=['get'])
def test():
    places = []
    for coll in db.collections():
        print(coll.id)
        places.append(coll.id)
    print(places)
    return render_template("./form.html", places=places)

@app.route("/handlePlace", methods=['get', 'post'])
def handlePlace():
    print(request.args.get("place"))
    place = request.args.get("place")
    place_ref = db.collection(place).stream()

    # TODO: display availability for all times
    # Then, make a dropdown selector for the times that are available

    # schedule = []
    times = []
    for doc in place_ref:
        times.append(doc.id)

    return render_template("./form.html", places=[place], times=times)

@app.route("/handleTime", methods=['get', 'post'])
def handleTime():
    print(request.args.get("place"))
    place = request.args.get("place")
    place_ref = db.collection(u'place').document(u'08:35')

    schedule = []

    try:
        doc = place_ref.get()
        print(u'Document data: {}'.format(doc.to_dict()))
    except:
        print(u'No such document!')

    for doc in place_ref:
        schedule.append({'time': doc.id, 'people': doc.to_dict()})

    return render_template("./form.html", places=[place])

if __name__ == '__main__':
    if os.environ.get('APP_DEBUG') is True:
        app_debug_state = True
    else:
        app_debug_state = False
    app.run(debug=app_debug_state, host='0.0.0.0')
