from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# MongoDB URI from .env (e.g., mongodb+srv://user:pass@cluster.mongodb.net/dbname)
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT') or 587)
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# --- Initialize Extensions ---
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)

# Temporary in-memory OTP store: {email: otp}
otp_store = {}

# --- HELPER CLASSES & FUNCTIONS ---

class User(UserMixin):
    """
    Wrapper class to make MongoDB documents compatible with Flask-Login.
    Flask-Login expects an object with an 'id' attribute.
    """
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.name = user_doc['name']
        self.email = user_doc['email']
        self.password = user_doc['password']

@login_manager.user_loader
def load_user(user_id):
    try:
        user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None
    except:
        return None

# --- HTML ROUTES (FRONTEND) ---

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

@app.route('/forgot_password')
def forgot_password_page():
    return render_template("forget_password.html")

@app.route('/reset_password.html')
def reset_password_page():
    return render_template("reset_password.html")

# --- API ROUTES (BACKEND) ---

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    if mongo.db.users.find_one({"email": data['email']}):
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Insert new user
    result = mongo.db.users.insert_one({
        "name": data['name'],
        "email": data['email'],
        "password": hashed_password
    })
    
    return jsonify({"message": "User registered successfully!", "id": str(result.inserted_id)}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({"email": data['email']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        return jsonify({
            "message": "Login successful!", 
            "user_id": str(user['_id']), 
            "name": user['name']
        })
    
    return jsonify({"error": "Invalid email or password"}), 401

# Get User Details
@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"name": user['name']})
    except:
        return jsonify({"error": "Invalid User ID format"}), 400

# Add Services 
@app.route('/add_service', methods=['POST'])
def add_service():
    data = request.json
    # Ensure no duplicate names
    if mongo.db.services.find_one({"name": data['name']}):
        return jsonify({"error": "Service already exists"}), 400

    mongo.db.services.insert_one({
        "name": data['name'],
        "price": data['price'],
        "duration": data['duration']
    })
    return jsonify({'message': 'Service added successfully!'})

# Fetch Services
@app.route('/services', methods=['GET'])
def get_services():
    services = mongo.db.services.find()
    result = []
    for s in services:
        result.append({
            "id": str(s['_id']),
            "name": s['name'],
            "price": s['price'],
            "duration": s['duration']
        })
    return jsonify(result)

# Book Appointment
@app.route('/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    max_slots = 5  
    
    user_id = data['user_id']
    service_id = data['service_id']
    date = data['date']
    time = data['time']

    # 1. Check if the same user already booked this service at the same date & time
    existing_appointment = mongo.db.appointments.find_one({
        "user_id": user_id,
        "service_id": service_id,
        "date": date,
        "time": time
    })

    if existing_appointment:
        return jsonify({"error": "You already have this service booked at this time!"}), 400

    # 2. Check if the time slot is full (count appointments at this specific date/time)
    count = mongo.db.appointments.count_documents({
        "date": date,
        "time": time
    })

    if count >= max_slots:
        return jsonify({"error": "Slots are full for your selected time interval. Kindly choose another time."}), 400

    # 3. Book the appointment
    mongo.db.appointments.insert_one({
        "user_id": user_id, 
        "service_id": service_id,
        "date": date,
        "time": time,
        "status": "Booked"
    })
    
    return jsonify({"message": "Appointment booked successfully!"}), 201

# View Appointments (User)
@app.route('/appointments/<user_id>', methods=['GET'])
def view_appointments(user_id):
    # MongoDB Aggregation to "Join" services collection to get Service Name
    pipeline = [
        {"$match": {"user_id": user_id}},
        # Convert string service_id to ObjectId for the lookup
        {"$addFields": {"serviceObjectId": {"$toObjectId": "$service_id"}}}, 
        {"$lookup": {
            "from": "services",
            "localField": "serviceObjectId",
            "foreignField": "_id",
            "as": "service_details"
        }},
        {"$unwind": "$service_details"} # Flatten the array
    ]
    
    appointments = list(mongo.db.appointments.aggregate(pipeline))
    
    result = []
    for appt in appointments:
        result.append({
            "id": str(appt['_id']),
            "service": appt['service_details']['name'],
            "date": appt['date'],
            "time": appt['time'],
            "status": appt['status']
        })

    return jsonify(result)

# Cancel Appointment
@app.route('/appointments/<id>', methods=['DELETE'])
def cancel_appointment(id):
    try:
        result = mongo.db.appointments.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Appointment not found"}), 404
        return jsonify({"message": "Appointment cancelled successfully!"})
    except:
        return jsonify({"error": "Invalid ID format"}), 400

# Delete Service
@app.route('/delete_service/<id>', methods=['DELETE'])
def delete_service(id):
    try:
        result = mongo.db.services.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Service not found"}), 404
        return jsonify({"message": "Service deleted successfully!"})
    except:
        return jsonify({"error": "Invalid ID format"}), 400

# Fetch all appointments for Admin
@app.route('/admin/appointments', methods=['GET'])
def get_all_appointments():
    # Join Users AND Services to get names
    pipeline = [
        {"$addFields": {
            "userObjectId": {"$toObjectId": "$user_id"},
            "serviceObjectId": {"$toObjectId": "$service_id"}
        }},
        {"$lookup": {
            "from": "users",
            "localField": "userObjectId",
            "foreignField": "_id",
            "as": "user_details"
        }},
        {"$lookup": {
            "from": "services",
            "localField": "serviceObjectId",
            "foreignField": "_id",
            "as": "service_details"
        }},
        # Unwind to get objects instead of arrays (Note: verify data integrity, if user deleted this might fail)
        {"$unwind": "$user_details"},
        {"$unwind": "$service_details"}
    ]

    appointments = list(mongo.db.appointments.aggregate(pipeline))

    result = []
    for appt in appointments:
        result.append({
            "id": str(appt['_id']),
            "user": appt['user_details']['name'],
            "service": appt['service_details']['name'],
            "date": appt['date'],
            "time": appt['time'],
            "status": appt['status']
        })

    return jsonify(result)

# Admin Update Status
@app.route('/admin/appointment/<appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get("status")

    try:
        result = mongo.db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": new_status}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Appointment not found"}), 404

        return jsonify({"message": f"Appointment status updated to {new_status}"})
    except:
        return jsonify({"error": "Invalid ID format"}), 400

# Send OTP
@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "Email not registered."}), 404

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        msg = Message("Your OTP Code", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your OTP is: {otp}"
        mail.send(msg)
        return jsonify({"success": True, "message": "OTP sent to your email."})
    except Exception as e:
        print("Email sending failed:", e)
        return jsonify({"success": False, "message": "Failed to send OTP."}), 500

# Verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if otp_store.get(email) == otp:
        return jsonify({"success": True, "message": "OTP verified."})
    else:
        return jsonify({"success": False, "message": "Invalid OTP."}), 400

# Reset Password
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')

    if not email or not new_password:
        return jsonify({"success": False, "message": "Missing email or password."}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    mongo.db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})

    # Remove OTP after successful reset
    otp_store.pop(email, None)

    return jsonify({"success": True, "message": "Password changed successfully."})

if __name__ == '__main__':
    app.run(debug=True)
