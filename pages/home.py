from flask import Flask, session, abort, redirect, request, render_template

from flask_mail import Mail, Message

from mongodb import mongo
from bson import ObjectId

import os
import pathlib
import requests
import sys
sys.path.append("/opt/homebrew/lib/python3.9/site-packages")
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests


app = Flask(__name__)
mail = Mail(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["DEBUG"] = True

#MAIL
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'be616fed205585'
app.config['MAIL_PASSWORD'] = '5cf7ecffae5846'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

#SSO
app.secret_key = "GeekyHuman.com" 
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  #this is to set our environment to https because OAuth 2.0 only supports https environments
GOOGLE_CLIENT_ID = "996812295199-qmebg894qq92plha2fe696lbstckvoq6.apps.googleusercontent.com"  #enter your client id you got from Google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")  #set the path to where the .json file you got Google console is
flow = Flow.from_client_secrets_file(  #Flow is OAuth 2.0 a class that stores all the information on how we want to authorize our users
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "openid"],  #here we are specifing what do we get after the authorization "https://www.googleapis.com/auth/userinfo.email"
    redirect_uri="http://127.0.0.1:5000/callback"  #and the redirect URI is the point where the user will end up after the authorization
)

def login_is_required(function):  #a function to check if the user is authorized or not
    def wrapper(*args, **kwargs):
        if "google_id" not in session:  #authorization required
            return abort(401)
        else:
            return function()

    return wrapper



@app.route('/home')
@login_is_required
def home():
    user = session['name']
    print(session)
    return render_template('home.html', user=user, session=session)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/list_rides')
def rides():
    docs_unfilled = mongo.db.rides.find({"filled":False})
    return render_template('list_rides.html', docs_unfilled = docs_unfilled)

@app.route('/list_rides/requested', methods=['POST'])
def riderequested():
    if request.method == 'POST':

        id = request.form['id']
        contact_method = request.form['contact_method']
        contact = request.form['contact']
        mongo.db.rides.update_one({"_id":ObjectId(id)},{'$inc': {'requests_left': -1}})

        email = mongo.db.rides.find_one({"_id":ObjectId(id)},{"contact":1})["contact"]

        msg = Message(subject = "Someone Requested a Ride!", sender = 'jane@mailtrap.io', recipients = [email])
        msg.body = "Here is a ride. Contact method is "+contact_method+", contact information is "+contact
        mail.send(msg)
        # return()
    return ("")


@app.route('/create_rides')
def createrides():
    user = session['name']
    return render_template('create_rides.html')


@app.route('/insert_rides', methods=['POST'])
def insertrides():
    user = session['name']
    if request.method == 'POST':
        print("got POST")
        destination=request.form['destination']
        time = request.form['time']
        num_seats = request.form['num_seats']
        duration_hr = request.form['duration_hr']
        duration_min = request.form['duration_min']
        contact = request.form['contact']
        comments = request.form['comments']


        print("here")
        
        insert=mongo.db.rides.insert_one({  "driver_name":user,
                                            "destination":destination, 
                                            "time":time, 
                                            "num_seats":num_seats,
                                            "duration_hr":duration_hr,
                                            "duration_min":duration_min,
                                            "contact":contact,
                                            "comments":comments, 
                                            "filled":False,
                                            "requests_left":10})
        print(insert)
    return ("")

@app.route('/profile')
def profile():
     return render_template('profile.html')


@app.route("/login")  #the page where the user can login
def login():
    authorization_url, state = flow.authorization_url()  #asking the flow class for the authorization (login) url
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")  #this is the page that will handle the callback process meaning process after the authorization
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  #state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")  #defing the results to show on the page
    session["name"] = id_info.get("name")
    return redirect("/home")  #the final page where the authorized users will end up


@app.route("/logout")  #the logout page and function
def logout():
    session.clear()
    return redirect("/")



if __name__ == "__main__":  #and the final closing function
    app.run(debug=True)