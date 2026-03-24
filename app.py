# -------------------------------------------------------------------
# SmartParcel --- NET_214 Project, Spring 2026
# Author : Oswald Xavier Pereira
# ID : 20240005935
# Email : 20240005935@students.cud.ac.ae
# AWS Acc : 778900739808
# -------------------------------------------------------------------




from flask import Flask, jsonify
import socket

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname()
    })

@app.route('/api/parcels', methods=['POST'])
def create_parcel():
    return jsonify({'message': 'Parcel created'}), 201

@app.route('/api/parcels/<id>', methods=['GET'])
def get_parcel(id):
    return jsonify({'parcel_id': id, 'status': 'pending'})

@app.route('/api/parcels/<id>/status', methods=['PUT'])
def update_status(id):
    return jsonify({'updated': True})

@app.route('/api/parcels', methods=['GET'])
def list_parcels():
    return jsonify({'parcels': []})

@app.route('/api/parcels/<id>', methods=['DELETE'])
def cancel_parcel(id):
    return jsonify({'cancelled': True})

@app.route('/api/parcels/<id>/photo', methods=['POST'])
def upload_photo(id):
    return jsonify({'photo_url': 's3://bucket/photo.jpg'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
