from flask import Flask, url_for, redirect, render_template, flash, session, request
import os
import pymongo
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from json import JSONEncoder
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from string import ascii_uppercase
from random import choice
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

sender_email = 'randomtestingemail1@gmail.com'

current_rooms = []

password = os.getenv("GMAILPASSWORD")
SECRET_KEY = os.getenv('SECRET_KEY')
db_link = os.getenv('db_link')

client = pymongo.MongoClient(db_link)
db = client['invasion_insight']
chats = db['chats']
logindetails = db['logindetails']

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

@app.route('/')
def home_page():
    return render_template('index.html')

def Generate_code():
    code = ''
    for _ in range(5):
        code += choice(ascii_uppercase)
    return code

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if not 'loginname' in session:
        if form.validate_on_submit():
            username = form.email.data
            password = form.password.data
            if logindetails.find_one({'username': username}):
                flash('Username already exists!', 'Error')
                return redirect(url_for('home_page'))
            logindetails.insert_one({'username': username, 'password': generate_password_hash(password, "scrypt"), 'is_admin': False})
            flash('Successfully registered!', 'Success')
            return redirect(url_for('home_page'))
        else:
            return render_template("register.html", form=form)
    else:
        flash('Already logged in!', "Error")
        return redirect(url_for("home_page"))

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if not 'loginname' in session:
        if form.validate_on_submit():
            username = form.email.data
            password = form.password.data
            a = logindetails.find_one({'username': username})
            if not a:
                return render_template('login.html', form=form, failed=True)
            else:
                if (check_password_hash(a['password'], password)):
                    session["loginname"] = username
                    flash('Logged in successfully', 'Success')
                    return redirect(url_for('home_page'))
                else:
                    return render_template('login.html', form=form, failed=True)
        else:
            return render_template('login.html', form=form)
    else:
        flash("Already logged in!", "Error")
        return redirect(url_for("home_page"))

@app.route('/logout')
def remove_session():
    session.pop('loginname')
    flash('Successfully logged out', 'Success')
    return redirect(url_for('home_page'))

@app.route('/admin')
def admin():
    if 'loginname' in session:
        current_user = logindetails.find_one({'username': session['loginname']})
        if current_user and current_user['is_admin']:
            return render_template('admin.html', rooms=current_rooms)
        else:
            return "Hell, nah!"
    else:
        flash("You need to login to view this page!", "Error")
        return redirect(url_for("login"))
    

@app.route('/livechat', methods=['GET', 'POST'])
def livechat():
    if 'loginname' in session:
        return render_template('livechat.html')
    else:
        flash("You need to login to view this page!", "Error")
        return redirect(url_for("login"))

@app.route('/tips')
def tips():
    return render_template("tips.html")

@app.route('/evacuation')
def evacuation():
    return render_template("evacuation.html")

#@socketio.on('')
@socketio.on('message')
def on_message(data):
    send(data[2]+": "+data[0], broadcast=True, room=data[1])

@socketio.on('join')
def on_join(data):
    username = session['loginname']
    room = data.get('room') or (session['loginname'] + '`s room')
    join_room(room)
    if room not in current_rooms:
        current_rooms.append(room)
    send(f"{username} has joined the room", room=room)
    admin_users = logindetails.find({'is_admin': True})
    for admin_user in admin_users:
        receiver_email = admin_user['email']
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = f'New chat started'
        body = f"New chat started, check it out at {request.url_root + 'admin'}"
        message.attach(MIMEText(body, 'plain'))
        text = message.as_string()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
        server.quit()


@socketio.on('leave')
def on_leave(data):
    username = session['loginname']
    room = username + '`s room'
    leave_room(room)
    if not socketio.server.rooms(room):
        current_rooms.remove(room)
    send(f"{username} has left the room", room=room)

if __name__ == '__main__':
    socketio.run(app)