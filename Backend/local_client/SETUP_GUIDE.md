# Local Client Setup Guide

Complete guide for setting up and connecting the local CCTV recording client to the backend.

## Prerequisites

✅ Backend Django server running  
✅ Python 3.8+ installed  
✅ Network connectivity to backend  
✅ Admin access to Django Admin panel  

## Step 1: Create Local Recording Client in Backend

1. **Access Django Admin**
   ```
   Navigate to: http://localhost:8000/admin/
   ```

2. **Go to Local Recording Clients**
   ```
   CCTV → Local Recording Clients → Add Local Recording Client
   ```

3. **Create New Client**
   - **Name**: Give your client a descriptive name (e.g., "Office Recording Station")
   - **Description**: Optional description of the client
   - **Location**: Physical location of the recording client (optional)
   - Click **Save**

4. **Copy Client Token**
   - After saving, you'll see a `client_token` field
   - **Copy this entire token** - you'll need it for configuration
   - Example: `abc123XYZ456def789GHI012jkl345MNO678pqr901STU234vwx567`

5. **Assign Cameras (Important!)**
   - In the same client edit page, scroll to "Assigned cameras"
   - Select the cameras you want this client to manage
   - Click **Save** again

6. **Set Camera Recording Mode**
   - Go to **CCTV → Cameras**
   - Edit each camera you want recorded by local client
   - Set **Recording mode** to "Local Client Recording"
   - Click **Save**

## Step 2: Install Local Client

1. **Navigate to local_client directory**
   ```bash
   cd Backend/local_client
   ```

2. **Create Python virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   .\venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create required directories**
   ```bash
   mkdir -p recordings/recordings recordings/logs recordings/cache recordings/pending_uploads
   ```

## Step 3: Configure Local Client

1. **Copy environment template**
   ```bash
   # On Linux/Mac:
   cp env.template .env
   
   # On Windows:
   copy env.template .env
   ```

2. **Edit .env file**
   
   Open `.env` in your text editor and configure:

   ```bash
   # Backend API Settings
   BACKEND_API_URL=http://localhost:8000
   CLIENT_TOKEN=<paste_your_token_from_step_1>
   
   # GCP Storage (if using)
   GCP_CREDENTIALS_PATH=../credentials/learningdevops-455404-e1cd1646efa3.json
   GCP_BUCKET_NAME=cctv_feed
   GCP_PROJECT_ID=learningdevops-455404
   
   # Recording Settings
   RECORDING_BASE_DIR=./recordings
   CLEANUP_AFTER_UPLOAD=true
   KEEP_LOCAL_DAYS=1
   
   # Sync Settings
   SYNC_INTERVAL_SECONDS=30
   HEARTBEAT_INTERVAL_SECONDS=60
   
   # System Settings
   LOG_LEVEL=INFO
   MAX_CONCURRENT_RECORDINGS=4
   ```

3. **Important Configuration Notes**
   - `CLIENT_TOKEN`: **Required** - Must match token from Django Admin
   - `BACKEND_API_URL`: Should match your backend URL
   - `GCP_CREDENTIALS_PATH`: Only needed if uploading to Google Cloud Storage
   - Adjust paths for Windows (use `\` or escaped `\\` if needed)

## Step 4: Test Connection

Run the connection test script:

```bash
python test_connection.py
```

**Expected output:**
```
🔧 Local Client Connection Test
============================================================

1. Checking configuration...
   Backend URL: http://localhost:8000
   Client Token: ✓ Set
   Client ID: Not set (optional)
   ✓ Configuration valid

2. Testing backend connection...
   ✓ Backend connection successful

3. Testing authentication...
   ✓ Authentication successful
   ✓ Found 2 assigned camera(s)

   Assigned cameras:
   - Front Door Camera (ID: abc-123)
   - Parking Lot Camera (ID: def-456)

4. Testing schedule sync...
   ✓ Schedule sync successful
   ✓ Found 3 active schedule(s)

5. Testing API endpoints...
   ✓ Health check: OK
   ✓ CCTV API health: OK
   ✓ Main health check: OK

============================================================
✅ All tests passed! Local client is properly configured.
```

## Step 5: Create Recording Schedules

1. **Go to Django Admin**
   ```
   CCTV → Recording Schedules → Add Recording Schedule
   ```

2. **Create Schedule**
   - **Name**: Descriptive name (e.g., "Business Hours Recording")
   - **Camera**: Select a camera assigned to your local client
   - **Schedule type**: Choose (daily, weekly, once, continuous)
   - **Start time**: Recording start time
   - **End time**: Recording end time
   - **Is active**: Check this box
   - Click **Save**

3. **Schedule Types**
   - **Daily**: Repeats every day
   - **Weekly**: Repeats on specific days of the week
   - **Once**: Runs one time between start/end dates
   - **Continuous**: Records continuously 24/7

## Step 6: Run Local Client

### Development Mode

```bash
python main.py
```

The client will:
- Start on port 8001
- Sync schedules from backend
- Start recording based on schedules
- Upload recordings to GCP (if configured)
- Send heartbeat to backend every 60 seconds

### Production Mode (Linux/systemd)

1. **Copy service file**
   ```bash
   sudo cp cctv-client.service /etc/systemd/system/
   ```

2. **Edit service file** (update paths)
   ```bash
   sudo nano /etc/systemd/system/cctv-client.service
   ```

3. **Enable and start**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cctv-client
   sudo systemctl start cctv-client
   ```

4. **Check status**
   ```bash
   sudo systemctl status cctv-client
   sudo journalctl -u cctv-client -f
   ```

### Production Mode (Windows Service)

Use `install.bat` script:
```cmd
install.bat
```

## Step 7: Monitor and Verify

### Check Local Client Status

```bash
# Health check
curl http://localhost:8001/health

# Detailed status
curl http://localhost:8001/status
```

### Check Backend Dashboard

1. Go to **Django Admin → CCTV → Local Recording Clients**
2. View your client
3. Check:
   - **Status**: Should show "Online"
   - **Last heartbeat**: Should be recent (< 2 minutes)
   - **Active recordings**: Shows current recording count

### View Logs

```bash
# Tail logs in real-time
tail -f recordings/logs/client.log

# View recent errors
tail -100 recordings/logs/client.log | grep ERROR
```

### Check Recordings

```bash
# View recorded files
ls -lh recordings/recordings/

# Check by camera
ls -lh recordings/recordings/{camera-id}/
```

## API Endpoints Reference

### Backend Endpoints (for local client)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v0/api/local-client/health` | GET | Health check |
| `/v0/api/local-client/schedules` | GET | Fetch schedules |
| `/v0/api/local-client/cameras` | GET | Fetch assigned cameras |
| `/v0/api/local-client/recordings/register` | POST | Register new recording |
| `/v0/api/local-client/recordings/status` | POST | Update recording status |
| `/v0/api/local-client/heartbeat` | POST | Send heartbeat |

### Local Client Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `http://localhost:8001/health` | GET | Client health check |
| `http://localhost:8001/status` | GET | Current status and recordings |
| `http://localhost:8001/manual-record` | POST | Trigger manual recording |
| `http://localhost:8001/schedules` | GET | View synced schedules |

## Troubleshooting

### ❌ "CLIENT_TOKEN is required"

**Solution:**
1. Check `.env` file exists in `local_client/` directory
2. Verify `CLIENT_TOKEN=...` is set (no spaces around `=`)
3. Make sure token is copied correctly from Django Admin

### ❌ "Invalid client token"

**Solution:**
1. Verify token in Django Admin matches `.env` file exactly
2. Check client record exists and is active
3. Make sure you copied the entire token (no trailing/leading spaces)

### ❌ "Backend connection test failed"

**Solution:**
1. Check `BACKEND_API_URL` is correct
2. Verify backend server is running: `curl http://localhost:8000/health/`
3. Check firewall/network settings
4. Try with IP instead of hostname if DNS issues

### ❌ "No cameras assigned"

**Solution:**
1. Go to Django Admin → Local Recording Clients
2. Edit your client
3. Add cameras in "Assigned cameras" field
4. Make sure cameras have `recording_mode` = "Local Client Recording"

### ❌ "No active schedules"

**Solution:**
1. Create schedules in Django Admin → Recording Schedules
2. Make sure "Is active" is checked
3. Verify schedule camera is assigned to your local client
4. Check schedule times are valid

### ❌ Recording fails with OpenCV error

**Solution:**
1. Test OpenCV: `python -c "import cv2; print(cv2.__version__)"`
2. Check camera RTSP URL is accessible: `ffplay rtsp://...`
3. Verify camera credentials are correct
4. Check network connectivity to cameras

### ❌ GCP upload fails

**Solution:**
1. Verify `GCP_CREDENTIALS_PATH` points to valid JSON file
2. Check GCP bucket name and permissions
3. Test GCP access: `gsutil ls gs://your-bucket/`
4. Files will queue in `pending_uploads/` for retry

## Next Steps

After successful setup:

1. ✅ Monitor first few recordings to ensure quality
2. ✅ Check GCP uploads are working (if enabled)
3. ✅ Verify disk space monitoring
4. ✅ Set up log rotation
5. ✅ Configure backup strategy
6. ✅ Document camera-specific settings

## Support

For issues or questions:
- Check logs: `recordings/logs/client.log`
- Run connection test: `python test_connection.py`
- Review backend logs in Django Admin
- Contact system administrator

---

**Version:** 1.0  
**Last Updated:** 2025-10-28

