import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth, firestore

app = Flask(__name__, template_folder='.')
CORS(app)

# Initialize Firebase Admin SDK
# Path to your service account key file
SERVICE_ACCOUNT_KEY = "serviceAccountKey.json"

db = None

if os.path.exists(SERVICE_ACCOUNT_KEY):
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
else:
    print(f"Warning: '{SERVICE_ACCOUNT_KEY}' not found. Backend will run in restricted mode.")
    print("To enable Firebase features, download your service account key from the Firebase Console.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    if not db:
        return jsonify({"error": "Backend not connected to Firebase. Check serviceAccountKey.json"}), 500

    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')

    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )

        db.collection('users').document(user.uid).set({
            'uid': user.uid,
            'name': name,
            'email': email,
            'role': role,
            'createdAt': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "User registered successfully", "uid": user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    if not db:
        return jsonify({"error": "Backend not connected to Firebase. Check serviceAccountKey.json"}), 500

    data = request.json
    id_token = data.get('idToken')

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return jsonify(user_doc.to_dict()), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/api/records', methods=['GET'])
def get_records():
    if not db:
        return jsonify({"error": "Backend not connected to Firebase"}), 500

    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "UID is required"}), 400

    try:
        records_ref = db.collection('records').where('userId', '==', uid)
        records = [doc.to_dict() for doc in records_ref.stream()]
        return jsonify(records), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
