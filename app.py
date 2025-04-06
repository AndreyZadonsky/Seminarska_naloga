from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# @app.before_request
# def check_login():
#     if 'id' not in session:
#         return redirect('/login')

app.config['SESSION_PERMANENT'] = False
indexes = [
    ['00', '01', '02', '03', '04'],
    ['10', '11', '12', '13', '14'],
    ['20', '21', '22', '23', '24'],
    ['30', '31', '32', '33', '34'],
    ['40', '41', '42', '43', '44'],
    ['50', '51', '52', '53', '54'],
    ['60', '61', '62', '63', '64'],
    ['70', '71', '72', '73', '74'],
    ['80', '81', '82', '83', '84'],
    ['90', '91', '92', '93', '94']
]

@app.route("/")
def home():
    if 'id' in session and get_user(int(session['id'])):
        return redirect('/0')
    else:
        return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = get_user(email)
        if user and check_password_hash(user[2], password):
            session['id'] = user[0]
            return redirect("/0")
        else:
            return render_template("authorisation.html", state2="hidden", message = "Napačno geslo ali e-naslov")
    if request.args.get('new'):
        return render_template("authorisation.html", state1="hidden", state2="")
    else:
        return render_template("authorisation.html", state1="hidden", state2="hidden")


@app.route("/<int:n>", methods=["GET", "POST"])
def index(n):
    if not session.get("id"):
        return redirect("/login")

    user_id = session.get("id")
    user = get_user(int(user_id))

    if request.method == "POST":
        week_date = get_date_range(n)[2]
        if "add" in request.form:
            cell_value = request.form.get("add")
            if add_reservation(week_date, cell_value, user_id):
                return redirect(f"/{n}")
        if "remove" in request.form:
            cell_value = request.form.get("remove")
            remove_reservation(week_date, cell_value, user_id)
            return redirect(f"/{n}")

    reservations = get_reservations(get_date_range(n)[2])
    return render_template("index.html",
                           indexes = indexes,
                           user_name = extract_name(user[1]),
                           user_id = user_id,
                           offset = n,
                           date_range = get_date_range(n),
                           reservations = reservations
                           )


@app.route("/reg", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        email = request.form["new_email"]
        password = request.form["new_password"]
        repeat_password = request.form["repeat_password"]
        if password != repeat_password:
            return render_template("registration.html", message = "Vneseni gesli se ne ujemata")

        if email and password:
            success = create_user(email, password)
            if success:
                return redirect("/login?new=True")

            else:
                return render_template("registration.html", message = "Ta uporabnik že obstaja")
        else:
            return render_template("registration.html", message = "Manjka geslo ali e-naslov")

    return render_template("registration.html", state1="hidden")



def get_user(data):
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    if type(data) == str:
        cursor.execute("SELECT id, email, password FROM users WHERE email = ?", (data,))
    elif type(data) == int:
        cursor.execute("SELECT id, email, password FROM users WHERE id = ?", (data,))
    user = cursor.fetchone()
    db.close()
    return user

def create_user(email, password):
    hashed = generate_password_hash(password)
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
        db.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        db.close()
    return True

def get_reservations(week_date):
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    cursor.execute("SELECT date, time, user_id FROM booking")
    reservations = {slot[1]: slot[2] for slot in cursor.fetchall() if slot[0] == week_date}
    db.close()
    return reservations

def add_reservation(week_date, time, user_id):
    slot_id = week_date + "-" + time
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO booking (user_id, date, time, slot_id) VALUES (?, ?, ?, ?)", (user_id, week_date, time, slot_id))
        db.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        db.close()
    return True

def remove_reservation(week_date, time, user_id):
    slot_id = week_date + "-" + time
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM booking WHERE slot_id = ?", (slot_id,))
    reservation = cursor.fetchone()
    if reservation[0] == user_id:
        cursor.execute("DELETE FROM booking WHERE slot_id = ?", (slot_id,))
        db.commit()
    db.close()

def extract_name(email):
    position = email.find("@")
    email = email[:position]
    name = email.split(".")
    return " ".join(name).title()

def get_date_range(offset):
    months = {
        1: "januar",
        2: "februar",
        3: "marec",
        4: "april",
        5: "maj",
        6: "junij",
        7: "julij",
        8: "avgust",
        9: "september",
        10: "oktober",
        11: "november",
        12: "december"
    }

    week_days = [
        "ponedeljek",
        "torek",
        "sreda",
        "četrtek",
        "petek"
    ]

    current = date.today()
    mon = current - timedelta(days = current.weekday()) + timedelta(days = offset * 7)
    fri = mon + timedelta(days = 4)
    days_range = []
    first = str(mon.day) + ". " + str(months[mon.month])
    last = str(fri.day) + ". " +  str(months[fri.month])

    for i in range(5):
        d = mon + timedelta(days=i)
        days_range.append((str(d.day) + "." + str(d.month), week_days[i]))

    return str(first + " — " + last), days_range, str(mon)


if __name__ == "__main__":
  app.run(debug=True)
