'''# Create Database
import sqlite3
con = sqlite3.connect("salon.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, 
        email TEXT UNIQUE, 
        password TEXT NOT NULL, 
        phone TEXT NOT NULL
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER NOT NULL, 
        service_id INTEGER NOT NULL, 
        date TEXT NOT NULL, 
        time TEXT NOT NULL, 
        status TEXT DEFAULT 'Booked',
        FOREIGN KEY(user_id) REFERENCES users(Id),
        FOREIGN KEY(service_id) REFERENCES services(Id)
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS services(
        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL UNIQUE,  -- Prevent duplicate services
        price INTEGER NOT NULL, 
        duration INTEGER NOT NULL
    )
""")

con.commit()
con.close()'''

# API for Users Login
from flask_mail import Mail, Message
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from flask_cors import CORS
from flask import render_template
import random
from flask import redirect, url_for
from urllib.parse import quote
from dotenv import load_dotenv
import os
load_dotenv()
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

app = Flask(__name__)
CORS(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

# Temporary in-memory OTP store: {email: otp}
otp_store = {}

@app.route('/', methods=['GET', 'HEAD'])
def home():
    return render_template('login.html')
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')
@app.route('/adminlogin', methods=['GET'])
def admin_page():
    return render_template('admin_login.html')
@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template('dashboard.html')
@app.route('/admindash', methods=['GET'])
def admindash_page():
    return render_template('dashboard_admin.html')
# Route to render Forgot Password page
@app.route('/forgot_password')
def forgot_password_page():
    return render_template("forget_password.html")
# Route to render Reset Password page
@app.route('/reset_password.html')
def reset_password_page():
    return render_template("reset_password.html")


# Configure Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.init_app(app)

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Booked")

with app.app_context():
    db.create_all()

# User Registration API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    new_user = User(name=data['name'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully!"}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"message": "Login successful!", "user_id": user.id, "name": user.name})
    
    return jsonify({"error": "Invalid email or password"}), 401

#Get User Name
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"name": user.name})

# Add Services 
@app.route('/add_service', methods=['POST'])
def add_service():
    data = request.json
    new_service = Service(name=data['name'], price=data['price'], duration=data['duration'])
    db.session.add(new_service)
    db.session.commit()
    return jsonify({'message': 'Service added successfully!'})

# Fetch Services
@app.route('/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{ "id": s.id, "name": s.name, "price": s.price, "duration": s.duration } for s in services])

# Book Appointment
@app.route('/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    max_slots = 5  # Maximum allowed bookings per time slot

    # Check if the same user already booked this service at the same date & time
    existing_appointment = Appointment.query.filter_by(
        user_id=data['user_id'],
        service_id=data['service_id'],
        date=data['date'],
        time=data['time']
    ).first()

    if existing_appointment:
        return jsonify({"error": "You already have this service booked at this time!"}), 400

    # Check if the time slot is full
    existing_appointments_count = Appointment.query.filter_by(
        date=data['date'],
        time=data['time']
    ).count()

    if existing_appointments_count >= max_slots:
        return jsonify({"error": "Slots are full for your selected time interval. Kindly choose another time."}), 400

    # Proceed with booking if slots are available
    new_appointment = Appointment(
        user_id=data['user_id'],
        service_id=data['service_id'],
        date=data['date'],
        time=data['time']
    )
    db.session.add(new_appointment)
    db.session.commit()
    
    return jsonify({"message": "Appointment booked successfully!"}), 201


# View Appointments
@app.route('/appointments/<int:user_id>', methods=['GET'])
def view_appointments(user_id):
    appointments = db.session.query(
        Appointment.id, 
        Service.name.label("service_name"),  # Fetch service name properly
        Appointment.date, 
        Appointment.time, 
        Appointment.status
    ).join(Service, Appointment.service_id == Service.id).filter(Appointment.user_id == user_id).all()

    return jsonify([
        {
            "id": appt.id,
            "service": appt.service_name,  # Ensure service name is used
            "date": appt.date,
            "time": appt.time,
            "status": appt.status
        } for appt in appointments
    ])


# Cancel Appointment
@app.route('/appointments/<int:id>', methods=['DELETE'])
def cancel_appointment(id):
    appointment = Appointment.query.get(id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment cancelled successfully!"})

# Delete Service
@app.route('/delete_service/<int:id>', methods=['DELETE'])
def delete_service(id):
    service = Service.query.get(id)  # Capital S for model Service
    if not service:
        return jsonify({"error": "Service not found"}), 404
    db.session.delete(service)
    db.session.commit()
    return jsonify({"message": "Service deleted successfully!"})

# Fetch all appointments for Admin
@app.route('/admin/appointments', methods=['GET'])
def get_all_appointments():
    appointments = db.session.query(
        Appointment.id, 
        User.name.label("user_name"),
        Service.name.label("service_name"),
        Appointment.date, 
        Appointment.time, 
        Appointment.status
    ).join(User, Appointment.user_id == User.id).join(Service, Appointment.service_id == Service.id).all()

    return jsonify([
        {
            "id": appt.id,
            "user": appt.user_name,
            "service": appt.service_name,
            "date": appt.date,
            "time": appt.time,
            "status": appt.status
        } for appt in appointments
    ])


@app.route('/appointments/<int:appointment_id>/status', methods=['PATCH'])
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['Accepted', 'Declined']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointment SET status = ? WHERE id = ?", (new_status, appointment_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Status updated successfully'}), 200


# Route to send OTP to email
@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "Email not registered."}), 404

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    # Send the email with Flask-Mail
    try:
        msg = Message("Your OTP Code", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your OTP is: {otp}"
        mail.send(msg)
        return jsonify({"success": True, "message": "OTP sent to your email."})
    except Exception as e:
        print("Email sending failed:", e)
        return jsonify({"success": False, "message": "Failed to send OTP."}), 500

# Route to verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if otp_store.get(email) == otp:
        return jsonify({"success": True, "message": "OTP verified."})
    else:
        return jsonify({"success": False, "message": "Invalid OTP."}), 400

# Route to reset password after OTP verification
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')

    if not email or not new_password:
        return jsonify({"success": False, "message": "Missing email or password."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password
    db.session.commit()

    # Remove OTP from store after successful reset
    otp_store.pop(email, None)

    return jsonify({"success": True, "message": "Password changed successfully."})

if __name__ == '__main__':
    app.run(debug=True)
