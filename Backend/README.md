# Shree Swami Smartha CCTV Management System - Backend

A comprehensive Django-based backend system for CCTV camera management, live streaming, recording, and user administration with GCP integration and Tailscale networking.

## 📋 Overview

This backend system provides a complete solution for:
- **CCTV Camera Management**: Add, configure, and monitor IP cameras
- **Live Video Streaming**: Real-time video streaming with multiple quality options
- **Recording Management**: Scheduled and manual recording with GCP cloud storage
- **User Management**: Role-based access control with JWT authentication
- **Email Services**: Automated email notifications and OTP verification
- **Admin Dashboard**: Comprehensive administration interface
- **GCP Integration**: Cloud storage and video processing
- **Tailscale Networking**: Secure remote access to cameras

## 🏗 System Architecture

### High-Level Architecture
```mermaid
graph TB
    subgraph "Client Layer"
        A[React Frontend<br/>Vite + TypeScript]
        B[Mobile App<br/>Capacitor/Ionic]
        C[Admin Panel<br/>Django Admin]
    end
    
    subgraph "API Gateway"
        D[Nginx<br/>Load Balancer]
    end
    
    subgraph "Backend Services"
        E[Django REST API<br/>Main Application]
        F[FastAPI<br/>Streaming Service]
        G[Celery Workers<br/>Background Tasks]
        H[Redis<br/>Cache & Queue]
    end
    
    subgraph "Data Layer"
        I[PostgreSQL<br/>Primary Database]
        J[GCP Cloud Storage<br/>Video Files]
        K[Local Storage<br/>Temporary Files]
    end
    
    subgraph "External Services"
        L[GCP Services<br/>Storage & Compute]
        M[Email Service<br/>SMTP/Gmail]
        N[Tailscale Network<br/>Secure VPN]
    end
    
    subgraph "Camera Network"
        O[IP Cameras<br/>RTSP Streams]
        P[MediaMTX Server<br/>Stream Relay]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    E --> H
    E --> I
    E --> J
    E --> K
    F --> P
    G --> H
    G --> J
    G --> M
    E --> L
    P --> O
    N --> O
    N --> E
```

### Data Flow Architecture
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant C as Camera
    participant G as GCP Storage
    participant R as Redis
    participant D as Database
    
    U->>F: Login Request
    F->>B: POST /auth/login
    B->>D: Validate Credentials
    D-->>B: User Data
    B-->>F: JWT Token
    F-->>U: Login Success
    
    U->>F: View Live Stream
    F->>B: GET /cameras/{id}/stream
    B->>C: RTSP Connection
    C-->>B: Video Stream
    B-->>F: Stream URL
    F-->>U: Live Video
    
    U->>F: Start Recording
    F->>B: POST /cameras/{id}/start_recording
    B->>C: Start Capture
    B->>R: Store Recording State
    B-->>F: Recording Started
    
    Note over B,G: Background Process
    B->>G: Upload Recording
    G-->>B: Upload Complete
    B->>D: Update Recording Status
```

### Network Architecture with Tailscale
```mermaid
graph TB
    subgraph "Local Network"
        A[Local Machine<br/>Development]
        B[IP Cameras<br/>192.168.1.x]
        C[Local Server<br/>Django Backend]
    end
    
    subgraph "Tailscale Network"
        D[Tailscale Node 1<br/>Local Machine]
        E[Tailscale Node 2<br/>GCP VM]
        F[Tailscale Node 3<br/>Remote Access]
    end
    
    subgraph "GCP Cloud"
        G[GCP VM Instance<br/>Production Backend]
        H[GCP Cloud Storage<br/>Video Files]
        I[GCP Database<br/>PostgreSQL]
    end
    
    subgraph "Internet"
        J[Web Users<br/>Frontend Access]
        K[Mobile Users<br/>App Access]
    end
    
    A -.->|Tailscale VPN| D
    B -.->|Local Network| A
    C -.->|Local Network| A
    
    D -.->|Secure Tunnel| E
    E -.->|GCP Internal| G
    G -.->|GCP Services| H
    G -.->|GCP Services| I
    
    F -.->|Tailscale VPN| E
    J -.->|HTTPS| G
    K -.->|HTTPS| G
    
    style D fill:#e1f5fe
    style E fill:#e1f5fe
    style F fill:#e1f5fe
```

### API Architecture
```mermaid
graph LR
    subgraph "Frontend Layer"
        A[React Components]
        B[API Services]
        C[Context Providers]
    end
    
    subgraph "API Layer"
        D[Django REST API<br/>/v0/api/]
        E[Django Ninja API<br/>/v0/api/]
        F[FastAPI<br/>/stream/]
    end
    
    subgraph "Service Layer"
        G[Authentication Service]
        H[Camera Service]
        I[Recording Service]
        J[User Service]
        K[Email Service]
    end
    
    subgraph "Data Layer"
        L[PostgreSQL<br/>User Data]
        M[Redis<br/>Cache & Sessions]
        N[GCP Storage<br/>Media Files]
    end
    
    A --> B
    B --> D
    B --> E
    B --> F
    
    D --> G
    D --> H
    D --> I
    D --> J
    D --> K
    
    E --> G
    E --> H
    E --> I
    E --> J
    E --> K
    
    F --> H
    F --> I
    
    G --> L
    G --> M
    H --> L
    H --> N
    I --> L
    I --> N
    J --> L
    K --> M
```

### Deployment Architecture
```mermaid
graph TB
    subgraph "Development Environment"
        A[Local Machine<br/>Frontend + Backend]
        B[Local Database<br/>PostgreSQL]
        C[Local Redis<br/>Cache]
    end
    
    subgraph "Production Environment"
        D[GCP VM Instance<br/>Backend Services]
        E[GCP Cloud SQL<br/>PostgreSQL]
        F[GCP Memorystore<br/>Redis]
        G[GCP Cloud Storage<br/>Media Files]
        H[Load Balancer<br/>Nginx]
    end
    
    subgraph "CDN & Static Assets"
        I[GCP Cloud CDN<br/>Static Files]
        J[GCP Cloud Storage<br/>Frontend Build]
    end
    
    subgraph "Monitoring & Logging"
        K[GCP Cloud Logging<br/>Application Logs]
        L[GCP Cloud Monitoring<br/>System Metrics]
        M[GCP Error Reporting<br/>Error Tracking]
    end
    
    A --> B
    A --> C
    
    H --> D
    D --> E
    D --> F
    D --> G
    D --> I
    D --> K
    D --> L
    D --> M
    
    I --> J
    
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style G fill:#e8f5e8
```

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **PostgreSQL**: 12.0 or higher
- **Redis**: 6.0 or higher
- **FFmpeg**: For video processing
- **Node.js**: 14.0 or higher (for frontend integration)

### Development Tools
- Git
- Docker and Docker Compose (optional)
- Python virtual environment
- PostgreSQL client
- Tailscale account and client

## 📥 Installation & Setup

### 1. Clone and Navigate to Backend

```bash
# Clone the repository
git clone <repository-url>
cd "Backend"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For Ubuntu/Linux systems, use:
# pip install -r requirements-ubuntu.txt
```

### 4. Environment Configuration

Create a `.env` file in the Backend directory:

```env
# Debug Settings
DEBUG=True
SECRET_KEY=your-secure-secret-key-here

# Database Configuration
DB_NAME=rstp
DB_USER=cctv-db
DB_PASSWORD=your-database-password-here
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key

# GCP Cloud Storage Configuration
GCP_STORAGE_USE_GCS=True
GCP_STORAGE_PROJECT_ID=your-gcp-project-id
GCP_STORAGE_BUCKET_NAME=your-bucket-name
GCP_STORAGE_CREDENTIALS_PATH=credentials/your-service-account-key.json

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

### 5. Database Setup

#### PostgreSQL Installation and Configuration

**Windows:**
```bash
# Download and install PostgreSQL from https://www.postgresql.org/download/windows/
# During installation, set password for 'postgres' user
```

**Ubuntu/Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

#### Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE rstp;
CREATE USER "cctv-db" WITH PASSWORD 'your-database-password-here';
GRANT ALL PRIVILEGES ON DATABASE rstp TO "cctv-db";
\q
```

### 6. GCP Service Account Setup

1. **Create GCP Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Note your Project ID

2. **Enable Required APIs:**
   - Cloud Storage API
   - Cloud Storage Transfer API

3. **Create Service Account:**
   ```bash
   # Using gcloud CLI (install from https://cloud.google.com/sdk/docs/install)
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud iam service-accounts create cctv-service-account
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:cctv-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/storage.admin"
   ```

4. **Download Credentials:**
   ```bash
   gcloud iam service-accounts keys create credentials/your-service-account-key.json \
       --iam-account=cctv-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

5. **Create Storage Bucket:**
   ```bash
   gsutil mb gs://your-bucket-name
   ```

### 7. Tailscale Setup

#### Install Tailscale

**Windows:**
```bash
# Download from https://tailscale.com/download/windows
# Install and sign in with your account
```

**Ubuntu/Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

**macOS:**
```bash
brew install --cask tailscale
```

#### Configure Tailscale for Camera Access

1. **Install on GCP VM:**
   ```bash
   # On your GCP instance
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. **Configure Camera Network:**
   - Add your local machine to Tailscale network
   - Add GCP VM to Tailscale network
   - Configure camera IPs to be accessible via Tailscale

3. **Update Settings:**
   ```env
   # Add to .env file
   TAILSCALE_NETWORK=100.64.0.0/10
   CAMERA_NETWORK=192.168.1.0/24
   ```

### 8. Run Database Migrations

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 9. Start Services

#### Development Mode

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A config worker -l info

# Terminal 3: Start Celery Beat (for scheduled tasks)
celery -A config beat -l info

# Terminal 4: Start Django Server
python manage.py runserver
```

#### Using Docker (Alternative)

```bash
# Build and run containers
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🚀 Running the Project

### Development Server

```bash
# Start all services
python manage.py runserver 0.0.0.0:8000
```

The backend will be available at:
- **API Base URL**: `http://localhost:8000/v0/api/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **API Documentation**: `http://localhost:8000/api/docs/swagger/`

### Production Deployment

```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 📚 API Documentation

### Main API Endpoints

#### Authentication & Users
- `POST /v0/api/users/auth/login/` - User login
- `POST /v0/api/users/auth/logout/` - User logout
- `GET /v0/api/users/users/` - List users
- `POST /v0/api/users/users/` - Create user
- `GET /v0/api/users/profile/` - Get user profile

#### CCTV Management
- `GET /v0/api/cctv/cameras/` - List cameras
- `POST /v0/api/cctv/cameras/register/` - Register camera
- `GET /v0/api/cctv/cameras/{id}/stream/` - Live stream
- `POST /v0/api/cctv/cameras/{id}/start_recording/` - Start recording
- `POST /v0/api/cctv/cameras/{id}/stop_recording/` - Stop recording

#### Recordings
- `GET /v0/api/cctv/recordings/` - List recordings
- `GET /v0/api/cctv/recordings/{id}/` - Get recording details
- `POST /v0/api/cctv/recordings/transfer-to-gcp/` - Transfer to GCP

#### Schedules
- `GET /v0/api/cctv/schedules/` - List schedules
- `POST /v0/api/cctv/schedules/` - Create schedule
- `POST /v0/api/cctv/schedules/{id}/activate/` - Activate schedule

#### Email Services
- `POST /v0/api/mail/request-password-reset` - Request password reset
- `POST /v0/api/mail/auth/send-email` - Send email
- `POST /v0/api/mail/auth/send-bulk-email` - Send bulk email

### API Documentation URLs
- **Swagger UI**: `/api/docs/swagger/`
- **ReDoc**: `/api/docs/redoc/`
- **OpenAPI Schema**: `/api/docs/schema/`

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: 4 user roles (Super Admin, Admin, Developer, Visitor)
- **CORS Configuration**: Cross-origin resource sharing setup
- **CSRF Protection**: Cross-site request forgery protection
- **Password Hashing**: Bcrypt password hashing
- **Admin Honeypot**: Security monitoring for admin panel
- **Rate Limiting**: API rate limiting
- **Input Validation**: Comprehensive input validation

## 🔄 Background Tasks

Celery tasks handle:
- **Email Sending**: Asynchronous email delivery
- **Video Processing**: FFmpeg video processing
- **GCP Uploads**: Cloud storage transfers
- **Scheduled Recordings**: Automated recording schedules
- **System Cleanup**: Log and file cleanup
- **Health Monitoring**: System health checks

## 📦 Key Dependencies

### Core Framework
- **Django**: 5.1.5 - Web framework
- **Django REST Framework**: 3.15.2 - API framework
- **Django Ninja**: 1.4.0 - FastAPI-like API framework
- **FastAPI**: 0.115.8 - Additional API framework

### Database & Cache
- **psycopg2-binary**: 2.9.10 - PostgreSQL adapter
- **Redis**: 5.2.1 - Caching and task queue

### Authentication & Security
- **djangorestframework-simplejwt**: 5.4.0 - JWT authentication
- **python-jose**: 3.3.0 - JWT token handling
- **bcrypt**: 3.2.0 - Password hashing

### Video Processing
- **opencv-python**: 4.5.0 - Computer vision
- **ffmpeg-python**: 0.2.0 - Video processing
- **Pillow**: 8.0.0 - Image processing

### Cloud Services
- **google-cloud-storage**: 2.10.0 - GCP storage
- **google-auth**: 2.30.0 - GCP authentication

### Task Processing
- **Celery**: 5.4.0 - Distributed task queue
- **APScheduler**: 3.9.0 - Advanced scheduling

## 🛠 Configuration Files

### Environment Variables (.env)
```env
# Core Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DB_NAME=rstp
DB_USER=cctv-db
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# GCP Configuration
GCP_STORAGE_USE_GCS=True
GCP_STORAGE_PROJECT_ID=your-project-id
GCP_STORAGE_BUCKET_NAME=your-bucket-name
GCP_STORAGE_CREDENTIALS_PATH=credentials/service-account.json

# Email Settings
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret
```

### Django Settings
- **Database**: PostgreSQL configuration
- **CORS**: Cross-origin settings
- **JWT**: Token configuration
- **GCP**: Cloud storage settings
- **Email**: SMTP configuration
- **Admin**: Admin panel customization

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error:**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Check database exists
   psql -U postgres -l
   ```

2. **Redis Connection Error:**
   ```bash
   # Start Redis server
   redis-server
   
   # Check Redis status
   redis-cli ping
   ```

3. **GCP Upload Fails:**
   ```bash
   # Check service account credentials
   gcloud auth activate-service-account --key-file=credentials/service-account.json
   
   # Test GCP access
   gsutil ls gs://your-bucket-name
   ```

4. **Camera Connection Issues:**
   ```bash
   # Test camera RTSP URL
   ffprobe rtsp://username:password@camera-ip:554/stream
   
   # Check Tailscale connectivity
   tailscale status
   ```

### Logs and Debugging

```bash
# View Django logs
tail -f logs/debug.log

# View Celery logs
celery -A config worker -l debug

# Check system status
python manage.py check
```

## 📞 Support

For support and queries:
- Check the logs in `logs/debug.log`
- Review API documentation at `/api/docs/swagger/`
- Check GCP console for storage issues
- Verify Tailscale network connectivity

## 🔄 Version History

- **v1.0.0** - Initial release with basic CCTV functionality
- **v1.1.0** - Added GCP integration and cloud storage
- **v1.2.0** - Implemented Tailscale networking
- **v1.3.0** - Added advanced scheduling and user management
- **v1.4.0** - Enhanced security and API documentation

---
