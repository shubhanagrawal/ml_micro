from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS, cross_origin
import os
import requests
import json

app = Flask(__name__)
CORS(app)

# Define the internal Docker URLs for your microservices
# These are the 'service names' from your docker-compose.yml
# and their internal ports.
AUTH_SERVICE_URL = "http://localhost:3001"
UPLOAD_SERVICE_URL = "http://localhost:3002"
TRAIN_SERVICE_URL = "http://localhost:3003"
PREDICT_SERVICE_URL = "http://localhost:3004"


@app.route("/", methods=['GET'])
@cross_origin()
def home():
    """Serves the main HTML page."""
    # This will look for 'index.html' in a 'templates' folder
    return render_template('index.html')

# --- NEW: Login Route ---
@app.route("/login", methods=['POST'])
@cross_origin()
def login_route():
    """
    Forwards login credentials (username/password) to the Auth service.
    It expects 'multipart/form-data' from the frontend.
    """
    print("Gateway: Received request for /login. Forwarding to auth service...")
    try:
        # 'request.files' and 'request.form' will hold the multipart data
        # We forward both files and form data to the microservice
        res = requests.post(
            AUTH_SERVICE_URL, 
            files=request.files, 
            data=request.form
        )
        return Response(res.content, status=res.status_code, content_type=res.headers['content-type'])

    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to auth service at {AUTH_SERVICE_URL}")
        return jsonify({"error": "Auth service is currently unavailable."}), 503
    except Exception as e:
        print(f"ERROR: An unknown error occurred during login: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


# --- NEW: Upload Route ---
@app.route("/upload", methods=['POST'])
@cross_origin()
def upload_route():
    """
    Forwards an uploaded file (from 'multipart/form-data') to the Upload service.
    """
    print("Gateway: Received request for /upload. Forwarding to upload service...")
    try:
        # 'request.files' will hold the file data. We forward it.
        res = requests.post(
            UPLOAD_SERVICE_URL,
            files=request.files
        )
        # Return the JSON response from the upload service (e.g., {"filename": "..."})
        return jsonify(res.json()), res.status_code

    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to upload service at {UPLOAD_SERVICE_URL}")
        return jsonify({"error": "Upload service is currently unavailable."}), 503
    except Exception as e:
        print(f"ERROR: An unknown error occurred during upload: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


# --- UPDATED: Train Route ---
@app.route("/train", methods=['GET', 'POST'])
@cross_origin()
def train_route():
    """
    This route now acts as a gateway.
    It calls the /train endpoint of your 'train' microservice.
    It now forwards the JSON body from the frontend.
    """
    print("Gateway: Received request for /train. Forwarding to train service...")
    try:
        # Get JSON data from the incoming request (e.g., {'data_dir': ...})
        incoming_data = request.json
        
        # Forward that JSON data to the train microservice
        res = requests.post(TRAIN_SERVICE_URL, json=incoming_data)
        
        # Return the response from the microservice (e.g., "Training initiated!")
        return Response(res.text, status=res.status_code)

    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to train service at {TRAIN_SERVICE_URL}")
        return jsonify({"error": "Training service is currently unavailable."}), 503
    except Exception as e:
        print(f"ERROR: An unknown error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/predict", methods=['POST'])
@cross_origin()
def predict_route():
    """
    This route now acts as a gateway.
    It forwards the image data to your 'predict' microservice.
    """
    print("Gateway: Received request for /predict. Forwarding to predict service...")
    try:
        # Get the JSON data (which contains the base64 image) from the incoming request
        incoming_data = request.json
        
        # Forward the exact same JSON data to the predict microservice
        res = requests.post(PREDICT_SERVICE_URL, json=incoming_data)

        # Return the JSON response (the prediction) from the microservice
        return jsonify(res.json()), res.status_code

    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to predict service at {PREDICT_SERVICE_URL}")
        return jsonify({"error": "Prediction service is currently unavailable."}), 503
    except json.JSONDecodeError:
        # This handles cases where the microservice returned something other than valid JSON
        return jsonify({"error": "Prediction service returned an invalid response."}), 502
    except Exception as e:
        print(f"ERROR: An unknown error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080) # Runs on port 8080