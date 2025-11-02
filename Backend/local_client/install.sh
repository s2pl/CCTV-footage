#!/bin/bash

# CCTV Local Recording Client Installation Script

set -e

echo "==================================="
echo "CCTV Local Recording Client Setup"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should NOT be run as root${NC}"
   echo "Please run as a normal user. Sudo will be used when needed."
   exit 1
fi

# Check Python version
echo -e "\n${GREEN}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

if ! python3 -c 'import sys; assert sys.version_info >= (3,8)' 2>/dev/null; then
    echo -e "${RED}Python 3.8 or higher is required${NC}"
    exit 1
fi

# Install directory
INSTALL_DIR="/opt/cctv-client"
echo -e "\n${GREEN}Installation directory: $INSTALL_DIR${NC}"

# Create installation directory
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
fi

# Copy files
echo -e "\n${GREEN}Copying files...${NC}"
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Create virtual environment
echo -e "\n${GREEN}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "\n${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "\n${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create directories
echo -e "\n${GREEN}Creating directories...${NC}"
mkdir -p recordings/recordings
mkdir -p recordings/logs
mkdir -p recordings/cache
mkdir -p recordings/pending_uploads

# Setup configuration
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        # Create basic .env file if .env.example doesn't exist
        cat > .env << 'EOF'
# Backend API Configuration
BACKEND_API_URL=http://localhost:8000

# Client Authentication (REQUIRED)
# Get CLIENT_TOKEN from Django Admin -> Local Recording Clients
CLIENT_TOKEN=
CLIENT_ID=

# GCP Storage Configuration
GCP_CREDENTIALS_PATH=
GCP_BUCKET_NAME=cctv_feed
GCP_PROJECT_ID=learningdevops-455404

# Recording Settings
RECORDING_BASE_DIR=./recordings
CLEANUP_AFTER_UPLOAD=true
KEEP_LOCAL_DAYS=1
MAX_CONCURRENT_RECORDINGS=4

# Sync Settings
SYNC_INTERVAL_SECONDS=30
HEARTBEAT_INTERVAL_SECONDS=60
MAX_RETRY_ATTEMPTS=5

# System Settings
LOG_LEVEL=INFO
TIME_ZONE=Asia/Kolkata
EOF
    fi
    echo -e "${YELLOW}Please edit .env with your configuration:${NC}"
    echo ""
    echo -e "${GREEN}Required Settings:${NC}"
    echo "  - BACKEND_API_URL: Backend API URL (default: http://localhost:8000)"
    echo "  - CLIENT_TOKEN: Authentication token from Django admin (REQUIRED)"
    echo "  - GCP_CREDENTIALS_PATH: Path to GCP service account JSON file"
    echo "  - GCP_BUCKET_NAME: GCP storage bucket (default: cctv_feed)"
    echo "  - GCP_PROJECT_ID: GCP project ID (default: learningdevops-455404)"
    echo ""
    echo -e "${YELLOW}To get CLIENT_TOKEN and CLIENT_ID:${NC}"
    echo "  1. Go to Django Admin -> CCTV -> Local Recording Clients"
    echo "  2. Create a new client or view existing client"
    echo "  3. Copy the client_token (REQUIRED)"
    echo "  4. Copy the UUID id field as CLIENT_ID (optional)"
    echo ""
    echo -e "${YELLOW}Optional Settings (see .env.example for full list):${NC}"
    echo "  - RECORDING_BASE_DIR: Directory for recordings"
    echo "  - CLEANUP_AFTER_UPLOAD: Delete local files after upload"
    echo "  - SYNC_INTERVAL_SECONDS: Schedule sync interval"
    echo "  - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)"
fi

# Create cctv user if doesn't exist
if ! id "cctv" &>/dev/null; then
    echo -e "\n${GREEN}Creating cctv user...${NC}"
    sudo useradd --system --shell /bin/bash --home "$INSTALL_DIR" cctv
fi

# Set ownership
echo -e "\n${GREEN}Setting permissions...${NC}"
sudo chown -R cctv:cctv "$INSTALL_DIR"

# Install systemd service
echo -e "\n${GREEN}Installing systemd service...${NC}"
sudo cp cctv-client.service /etc/systemd/system/
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|" /etc/systemd/system/cctv-client.service
sudo systemctl daemon-reload

echo -e "\n${GREEN}==================================="
echo "Installation Complete!"
echo "===================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Edit configuration:"
echo "   sudo nano $INSTALL_DIR/.env"
echo ""
echo "2. Test the client:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Enable and start service:"
echo "   sudo systemctl enable cctv-client"
echo "   sudo systemctl start cctv-client"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status cctv-client"
echo "   sudo journalctl -u cctv-client -f"
echo ""
echo -e "${GREEN}For help, see: $INSTALL_DIR/README.md${NC}"

