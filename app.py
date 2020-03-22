import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, render_template, request

app = Flask(__name__)

# Use a service account
cred = credentials.Certificate('<KEY_FILE>')
firebase_admin.initialize_app(cred)

db = firestore.client()


@app.route("/test", methods=['get'])
def test():
    places = []
    for coll in db.collections():
        print(coll.id)
        places.append(coll.id)
    print(places)
    return render_template("./form.html", places=places)

@app.route("/handlePlace", methods=['get', 'post'])
def handler():
    print(request.args.get("place"))
    place = request.args.get("place")
    place_ref = db.collection(place).stream()
    # schedule = []
    times = []
    for doc in place_ref:
        times.append(doc.id)

    return render_template("./form.html", places=[place], times=times)

if __name__ == '__main__':
    if os.environ.get('APP_DEBUG') is True:
        app_debug_state = True
    else:
        app_debug_state = False
    app.run(debug=app_debug_state, host='0.0.0.0')
