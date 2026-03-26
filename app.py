# -------------------------------------------------------------------
# SmartParcel --- NET_214 Project, Spring 2026
# Author : Oswald Xavier Pereira
# ID : 20240005935
# Email : 20240005935@students.cud.ac.ae
# AWS Acc : 778900739808
# -------------------------------------------------------------------

from flask import Flask, jsonify, request
import socket
import boto3
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# API Keys with roles
API_KEYS = {
    "key-driver-001": {"role": "driver", "name": "Driver 1"},
    "key-admin-001": {"role": "admin", "name": "Admin"},
    "key-customer-001": {"role": "customer", "name": "Customer"}
}

def check_auth(required_role=None):
    """Check API key and role"""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None, jsonify({'error': 'API key required'}), 401
    
    if api_key not in API_KEYS:
        return None, jsonify({'error': 'Invalid API key'}), 401
    
    user = API_KEYS[api_key]
    
    if required_role and user['role'] != required_role:
        return None, jsonify({'error': f'Access denied. {required_role} role required'}), 403
    
    return user, None, None

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
table = dynamodb.Table('smartparcel-parcels')

# S3 client
s3 = boto3.client('s3', region_name='ap-southeast-2')
S3_BUCKET = 'smartparcel-photos-20240005935'

# SQS client
sqs = boto3.client('sqs', region_name='ap-southeast-2')
SQS_QUEUE_URL = 'https://sqs.ap-southeast-2.amazonaws.com/778900739808/smartparcel-notifications-20240005935'

def generate_parcel_id():
    return f"PKG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname()
    })

@app.route('/api/parcels', methods=['POST'])
def create_parcel():
    user, error_response, status = check_auth(required_role='driver')
    if error_response:
        return error_response, status
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    required = ['sender', 'receiver', 'address', 'email']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    parcel_id = generate_parcel_id()
    timestamp = datetime.now().isoformat()

    item = {
        'parcel_id': parcel_id,
        'sender': data['sender'],
        'receiver': data['receiver'],
        'address': data['address'],
        'email': data['email'],
        'status': 'created',
        'history': [{'status': 'created', 'timestamp': timestamp}],
        'created_at': timestamp,
        'updated_at': timestamp
    }

    table.put_item(Item=item)

    return jsonify({
        'parcel_id': parcel_id,
        'status': 'created',
        'message': 'Parcel created successfully'
    }), 201

@app.route('/api/parcels/<parcel_id>', methods=['GET'])
def get_parcel(parcel_id):
    user, error_response, status = check_auth()
    if error_response:
        return error_response, status
    try:
        response = table.get_item(Key={'parcel_id': parcel_id})
        if 'Item' not in response:
            return jsonify({'error': 'Parcel not found'}), 404
        return jsonify(response['Item'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parcels/<parcel_id>/status', methods=['PUT'])
def update_status(parcel_id):
    user, error_response, status = check_auth(required_role='driver')
    if error_response:
        return error_response, status
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing status field'}), 400

    valid_statuses = ['picked_up', 'in_transit', 'delivered']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    try:
        response = table.get_item(Key={'parcel_id': parcel_id})
        if 'Item' not in response:
            return jsonify({'error': 'Parcel not found'}), 404

        item = response['Item']

        if item['status'] == 'delivered':
            return jsonify({'error': 'Cannot update delivered parcel'}), 409

        timestamp = datetime.now().isoformat()
        item['status'] = data['status']
        item['history'].append({'status': data['status'], 'timestamp': timestamp})
        item['updated_at'] = timestamp

        table.put_item(Item=item)
        
        # Write to debug file
        with open('/tmp/sqs_debug.log', 'a') as f:
            f.write(f"UPDATE: {parcel_id} -> {data['status']} at {timestamp}\n")
        
        # Send notification to SQS
        try:
            response = sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps({
                    'parcel_id': parcel_id,
                    'new_status': data['status'],
                    'customer_email': item['email'],
                    'driver_name': user['name'],
                    'timestamp': timestamp
                })
            )
            with open('/tmp/sqs_debug.log', 'a') as f:
                f.write(f"SQS SENT: MessageId={response.get('MessageId')}\n")
        except Exception as e:
            with open('/tmp/sqs_debug.log', 'a') as f:
                f.write(f"SQS ERROR: {e}\n")


        return jsonify({
            'parcel_id': parcel_id,
            'status': data['status'],
            'updated': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/parcels', methods=['GET'])
def list_parcels():
    user, error_response, status = check_auth(required_role='admin')
    if error_response:
        return error_response, status
    status_filter = request.args.get('status')

    try:
        if status_filter:
            response = table.query(
                IndexName='status-index',
                KeyConditionExpression='status = :status',
                ExpressionAttributeValues={':status': status_filter}
            )
        else:
            response = table.scan()

        return jsonify({
            'parcels': response.get('Items', []),
            'count': len(response.get('Items', []))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parcels/<parcel_id>', methods=['DELETE'])
def cancel_parcel(parcel_id):
    user, error_response, status = check_auth(required_role='admin')
    if error_response:
        return error_response, status
    try:
        response = table.get_item(Key={'parcel_id': parcel_id})
        if 'Item' not in response:
            return jsonify({'error': 'Parcel not found'}), 404

        item = response['Item']

        if item['status'] not in ['created']:
            return jsonify({'error': 'Cannot cancel parcel that is already picked up or in transit'}), 409

        timestamp = datetime.now().isoformat()
        item['status'] = 'cancelled'
        item['history'].append({'status': 'cancelled', 'timestamp': timestamp})
        item['updated_at'] = timestamp

        table.put_item(Item=item)

        return jsonify({
            'parcel_id': parcel_id,
            'cancelled': True,
            'message': 'Parcel cancelled'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parcels/<parcel_id>/photo', methods=['POST'])
def upload_photo(parcel_id):
    user, error_response, status = check_auth(required_role='driver')
    if error_response:
        return error_response, status
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Create S3 key
        s3_key = f"{parcel_id}/{photo.filename}"
        
        # Upload to S3 with encryption
        s3.upload_fileobj(
            photo,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        
        # Generate public URL
        photo_url = f"https://{S3_BUCKET}.s3.ap-southeast-2.amazonaws.com/{s3_key}"
        
        # Update parcel in DynamoDB with photo URL
        response = table.get_item(Key={'parcel_id': parcel_id})
        if 'Item' in response:
            item = response['Item']
            if 'photos' not in item:
                item['photos'] = []
            item['photos'].append({
                'url': photo_url,
                'filename': photo.filename,
                'uploaded_at': datetime.now().isoformat()
            })
            table.put_item(Item=item)
        
        return jsonify({
            'parcel_id': parcel_id,
            'photo_url': photo_url,
            'message': 'Photo uploaded successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
