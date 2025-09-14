# Shree Swami Smartha CCTV Management System

A comprehensive full-stack CCTV camera management system with live streaming, recording, cloud storage, and user administration. Built with Django backend and React frontend, featuring GCP integration and Tailscale networking.

## 📋 Overview

This system provides a complete solution for:
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

## 🚀 Features

### Core Functionality
- **Dashboard**: Overview of system status, camera counts, and recent alerts
- **Camera Management**: Add, edit, and monitor security cameras
- **Live Feed**: Real-time camera streams with status monitoring
- **Recording Management**: View and manage recorded footage
- **User Management**: Role-based access control with permissions
- **Access Control**: API endpoints and access management
- **Scheduling**: Automated recording and maintenance schedules
- **Settings**: System configuration and preferences

### Technical Features
- **Authentication**: Secure login system with role-based access
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Dark/Light Theme**: Toggle between themes
- **TypeScript**: Full type safety and better development experience
- **Modern UI**: Clean, intuitive interface with modern design patterns
- **Real-time Streaming**: Live video feeds with quality adjustment
- **Cloud Storage**: GCP integration for video storage
- **Background Tasks**: Celery for asynchronous processing

## 🛠 Tech Stack

### Backend
- **Django**: 5.1.5 - Web framework
- **Django REST Framework**: 3.15.2 - API framework
- **Django Ninja**: 1.4.0 - FastAPI-like API framework
- **FastAPI**: 0.115.8 - Additional API framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and task queue
- **Celery**: Background task processing
- **OpenCV**: Video processing
- **FFmpeg**: Video encoding/decoding

### Frontend
- **React**: 18 + TypeScript
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **React Context API**: State management

### Cloud & Infrastructure
- **Google Cloud Platform**: Storage and compute
- **Tailscale**: Secure networking
- **Docker**: Containerization
- **Nginx**: Load balancing

## 📥 Installation & Setup

### Prerequisites
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **PostgreSQL**: 12.0 or higher
- **Redis**: 6.0 or higher
- **FFmpeg**: For video processing
- **Git**: Version control
- **Docker**: Optional containerization

### 1. Clone Repository
```bash
git clone <repository-url>
cd CCTV-footage
```

### 2. Backend Setup

#### Navigate to Backend Directory
```bash
cd Backend
```

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or macOS:
source venv/bin/activate
```

#### Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

#### Environment Configuration
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

#### Database Setup
```bash
# Create database and user
psql -U postgres
CREATE DATABASE rstp;
CREATE USER "cctv-db" WITH PASSWORD 'your-database-password-here';
GRANT ALL PRIVILEGES ON DATABASE rstp TO "cctv-db";
\q

# Run migrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 3. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd ../Frontend
```

#### Install Dependencies
```bash
npm install
```

### 4. Start Services

#### Development Mode
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
cd Backend
celery -A config worker -l info

# Terminal 3: Start Celery Beat
celery -A config beat -l info

# Terminal 4: Start Django Server
python manage.py runserver

# Terminal 5: Start Frontend
cd Frontend
npm run dev
```

#### Using Docker (Alternative)
```bash
# From project root
docker-compose up --build
```

## 🚀 Running the Project

### Development Servers
- **Backend API**: `http://localhost:8000/v0/api/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **API Documentation**: `http://localhost:8000/api/docs/swagger/`
- **Frontend**: `http://localhost:5173`

### Production Deployment
```bash
# Backend
cd Backend
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Frontend
cd Frontend
npm run build
# Deploy dist/ folder to your hosting service
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

## 📱 User Roles

The system supports four user roles:

- **Super Admin**: Full system access and user management
- **Admin**: Camera control and recording management
- **Developer**: API access and system configuration
- **Visitor**: Read-only access to camera feeds and recordings

## 🎨 Frontend Features

### Themes
The application supports both light and dark themes. Users can toggle between themes using the theme switcher in the header.

### Camera Management
- **Live Feed**: Real-time camera streams with quality adjustment
- **Camera List**: Manage all cameras with status monitoring
- **Recording Control**: Start/stop recording with scheduling
- **Error Handling**: Automatic recovery and troubleshooting

### Scheduling System
- **Continuous Recording**: 24/7 recording for high-security areas
- **One-time Schedule**: Event-specific recording
- **Daily Schedule**: Business hours monitoring
- **Weekly Schedule**: Different schedules per day

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

3. **Camera Connection Issues:**
   ```bash
   # Test camera RTSP URL
   ffprobe rtsp://username:password@camera-ip:554/stream
   
   # Check Tailscale connectivity
   tailscale status
   ```

4. **Frontend Build Issues:**
   ```bash
   # Clear node modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   
   # Check for TypeScript errors
   npm run lint
   ```

### Debug Information
```bash
# Enable debug mode for frontend
VITE_ENABLE_DEBUG=true npm run dev

# View Django logs
tail -f Backend/logs/debug.log

# Check system status
cd Backend
python manage.py check
```

## 📦 Key Dependencies

### Backend Dependencies
- **Django**: 5.1.5 - Web framework
- **Django REST Framework**: 3.15.2 - API framework
- **psycopg2-binary**: 2.9.10 - PostgreSQL adapter
- **Redis**: 5.2.1 - Caching and task queue
- **opencv-python**: 4.5.0 - Computer vision
- **google-cloud-storage**: 2.10.0 - GCP storage
- **Celery**: 5.4.0 - Distributed task queue

### Frontend Dependencies
- **React**: 18.2.0 - UI library
- **TypeScript**: 5.0.0 - Type safety
- **Vite**: 5.0.0 - Build tool
- **Tailwind CSS**: 3.3.0 - Styling
- **Lucide React**: 0.263.1 - Icons

## 🚀 Deployment

### Production Build
```bash
# Backend
cd Backend
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Frontend
cd Frontend
npm run build
```

### Recommended Hosting
- **Backend**: GCP Compute Engine, AWS EC2, or DigitalOcean
- **Frontend**: Vercel, Netlify, or AWS S3 + CloudFront
- **Database**: GCP Cloud SQL, AWS RDS, or managed PostgreSQL
- **Storage**: GCP Cloud Storage or AWS S3

## 📞 Support

For support and queries:
- Check the logs in `Backend/logs/debug.log`
- Review API documentation at `/api/docs/swagger/`
- Check GCP console for storage issues
- Verify Tailscale network connectivity
- Check browser console for frontend issues

## 🔄 Version History

- **v1.0.0** - Initial release with basic CCTV functionality
- **v1.1.0** - Added GCP integration and cloud storage
- **v1.2.0** - Implemented Tailscale networking
- **v1.3.0** - Added advanced scheduling and user management
- **v1.4.0** - Enhanced security and API documentation
- **v1.5.0** - React frontend with modern UI

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Note**: This is a comprehensive CCTV management system designed for security monitoring, live streaming, and recording management. Ensure proper security measures and compliance with local regulations when deploying in production environments.
