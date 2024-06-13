from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
VEHICLE_POSITIONS_FILE = 'vehicle_positions.json'

def load_vehicle_positions():
    if not os.path.exists(VEHICLE_POSITIONS_FILE):
        return []
    with open(VEHICLE_POSITIONS_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

@app.route('/api/vehicle', methods=['GET'])
def get_vehicle():
    license_plate = request.args.get('licensePlate')
    transport_type = request.args.get('transport_type')

    if not license_plate or not transport_type:
        return jsonify({"error": "Please provide both licensePlate and transport_type"}), 400

    vehicle_positions = load_vehicle_positions()
    results = [
        vehicle for vehicle in vehicle_positions
        if vehicle.get('licensePlate') == license_plate and vehicle.get('routeInfo', {}).get('transport_type') == transport_type
    ]

    if not results:
        return jsonify({"error": "No vehicle found with the provided licensePlate and transport_type"}), 404

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
