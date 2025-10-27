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
TRAIN_SERVICE_URL = "http://train:3003/train"
PREDICT_SERVICE_URL = "http://predict:3004/predict"


@app.route("/", methods=['GET'])
@cross_origin()
def home():
    """Serves the main HTML page."""
    return render_template('index.html')


@app.route("/train", methods=['GET', 'POST'])
@cross_origin()
def train_route():
    """
    This route now acts as a gateway.
    It calls the /train endpoint of your 'train' microservice.
    """
    print("Gateway: Received request for /train. Forwarding to train service...")
    try:
        # Make a request to the train microservice
        # Using 'train' as the hostname works because Docker's DNS will resolve it
        # to the correct container's IP within the 'cnn-network'.
        # We use a POST request as it's typically used to initiate an action.
        res = requests.post(TRAIN_SERVICE_URL)
        
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