# SmartParcel - Parcel Tracking System

**NET214 Network Programming Project - Spring 2026**

## Author
- **Name:** Oswald Xavier Pereira
- **Student ID:** 20240005935
- **Email:** 20240005935@students.cud.ac.ae
- **AWS Account ID:** 778900739808

## Project Description
Cloud-native parcel tracking system that allows delivery drivers to update parcel status in real-time, customers to check their parcel status via API, and automatic email notifications when status changes.

## Tech Stack
- **Compute:** AWS EC2 (t3.micro)
- **Framework:** Flask (Python)
- **Database:** DynamoDB
- **Storage:** S3 (encrypted)
- **Queue:** SQS
- **Compute (Serverless):** Lambda
- **Notifications:** SNS
- **Monitoring:** CloudWatch

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/parcels` | Create a new parcel | Driver |
| GET | `/api/parcels/<id>` | Get parcel details | Any |
| PUT | `/api/parcels/<id>/status` | Update parcel status | Driver |
| GET | `/api/parcels` | List all parcels | Admin |
| DELETE | `/api/parcels/<id>` | Cancel a parcel | Admin |
| POST | `/api/parcels/<id>/photo` | Upload delivery proof photo | Driver |
| GET | `/health` | Health check | None |

## Authentication
API keys with role-based access:

| API Key | Role | Permissions |
|---------|------|-------------|
| `key-driver-001` | Driver | Create parcels, update status, upload photos |
| `key-admin-001` | Admin | List all parcels, cancel parcels |
| `key-customer-001` | Customer | View parcel details |

## Deployment
- **EC2 Public IP:** 3.106.211.152
- **API Base URL:** http://3.106.211.152:8080
- **Health Check:** http://3.106.211.152:8080/health

## AWS Architecture
- **VPC:** 10.0.0.0/16
- **Public Subnet:** 10.0.1.0/24
- **EC2:** t3.micro with public IP
- **DynamoDB:** smartparcel-parcels table with status-index GSI
- **S3:** smartparcel-photos-20240005935 (SSE-S3 encrypted)
- **SQS:** smartparcel-notifications-20240005935
- **Lambda:** smartparcel-notifier-20240005935
- **SNS:** smartparcel-alerts-20240005935
- **CloudWatch Alarm:** CPUUtilization > 70%


