import os
import cv2
import boto3
import psutil
import json
import time
import logging
import threading
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt
from botocore.exceptions import BotoCoreError, ClientError

# ---------------- Configuration ----------------
CAMERA_ID = "CAMERA_01"
CAMERA_INDEX = 0
CHUNK_DURATION = 30  # seconds
OUTPUT_DIR = "video_chunks"
S3_BUCKET = "your-s3-bucket"
AWS_REGION = "ap-south-1"

# DynamoDB
DYNAMO_TABLE_NAME = "VideoUploadLogs"

# MQTT / AWS IoT
MQTT_ENABLED = True
MQTT_BROKER = "your-iot-endpoint.amazonaws.com"  # AWS IoT Core endpoint
MQTT_PORT = 8883
MQTT_TOPIC_STATUS = f"camera/{CAMERA_ID}/upload/status"
MQTT_TOPIC_HEALTH = f"camera/{CAMERA_ID}/health"
MQTT_CLIENT_ID = f"CameraUploader_{CAMERA_ID}"

# ThreadPool
MAX_WORKERS = 3

# ------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# AWS clients
s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
dynamo_client = boto3.client("dynamodb", region_name=AWS_REGION)

# MQTT setup
mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
if MQTT_ENABLED:
    try:
        mqtt_client.tls_set()  # Use AWS IoT Core certificates if required
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logging.info("📡 Connected to AWS IoT MQTT broker")
    except Exception as e:
        logging.error(f"[MQTT] Connection failed: {e}")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------- DynamoDB Setup ----------------
def ensure_dynamodb_table():
    """Create DynamoDB table if it doesn't exist."""
    existing = dynamo_client.list_tables()["TableNames"]
    if DYNAMO_TABLE_NAME not in existing:
        logging.info(f"🧱 Creating DynamoDB table '{DYNAMO_TABLE_NAME}' ...")
        try:
            table = dynamodb.create_table(
                TableName=DYNAMO_TABLE_NAME,
                KeySchema=[{"AttributeName": "filename", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "filename", "AttributeType": "S"}],
                ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            )
            table.wait_until_exists()
            logging.info(f"✅ DynamoDB table '{DYNAMO_TABLE_NAME}' created successfully.")
        except Exception as e:
            logging.error(f"❌ Failed to create DynamoDB table: {e}")
    else:
        logging.info(f"✅ DynamoDB table '{DYNAMO_TABLE_NAME}' already exists.")


def log_to_dynamodb(filename, s3_url, duration, status="success"):
    """Insert upload log into DynamoDB."""
    try:
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        record = {
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "camera_id": CAMERA_ID,
            "s3_url": s3_url,
            "duration_sec": duration,
            "status": status,
        }
        table.put_item(Item=record)
        logging.info(f"🪣 Logged upload to DynamoDB: {filename}")
    except Exception as e:
        logging.error(f"❌ DynamoDB log failed: {e}")


# ---------------- Upload Function ----------------
def upload_with_progress(file_path, bucket, key, retries=3):
    """Uploads file to S3 with retry logic and progress tracking."""
    file_size = os.path.getsize(file_path)
    progress = tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Uploading {key}", position=0)

    def callback(bytes_amount):
        progress.update(bytes_amount)

    for attempt in range(retries):
        try:
            s3.upload_file(file_path, bucket, key, Callback=callback)
            progress.close()

            s3_url = f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"
            log_to_dynamodb(key, s3_url, CHUNK_DURATION, "success")

            message = {
                "camera_id": CAMERA_ID,
                "status": "success",
                "file": key,
                "timestamp": datetime.utcnow().isoformat(),
                "s3_url": s3_url,
            }

            if MQTT_ENABLED:
                mqtt_client.publish(MQTT_TOPIC_STATUS, json.dumps(message))

            os.remove(file_path)
            return True

        except (BotoCoreError, ClientError) as e:
            progress.close()
            logging.error(f"❌ Upload failed ({attempt+1}/{retries}): {e}")
            time.sleep(2 ** attempt)

    log_to_dynamodb(key, "", CHUNK_DURATION, "failed")
    mqtt_client.publish(MQTT_TOPIC_STATUS, json.dumps({
        "camera_id": CAMERA_ID,
        "status": "failed",
        "file": key,
        "timestamp": datetime.utcnow().isoformat()
    }))
    return False


# ---------------- Health Monitoring ----------------
def publish_health_status():
    """Publish system health (CPU, RAM, uptime) to MQTT every 5 minutes."""
    start_time = time.time()
    while True:
        try:
            uptime = time.time() - start_time
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            mem_usage = memory.percent

            health_data = {
                "camera_id": CAMERA_ID,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": cpu_usage,
                "memory_usage": mem_usage,
                "uptime_sec": int(uptime),
                "status": "online",
            }

            if MQTT_ENABLED:
                mqtt_client.publish(MQTT_TOPIC_HEALTH, json.dumps(health_data))
            logging.info(f"💓 Health ping: CPU {cpu_usage}%, RAM {mem_usage}%, uptime {int(uptime)}s")

        except Exception as e:
            logging.error(f"❌ Health ping failed: {e}")

        time.sleep(300)  # 5 minutes


# ---------------- Video Recorder ----------------
def record_video_chunks():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    fps = int(cap.get(cv2.CAP_PROP_FPS) or 20)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = []

    if MQTT_ENABLED:
        mqtt_client.publish(MQTT_TOPIC_STATUS, json.dumps({"camera_id": CAMERA_ID, "status": "streaming"}))

    try:
        while True:
            filename = f"{CAMERA_ID}_chunk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
            filepath = os.path.join(OUTPUT_DIR, filename)
            out = cv2.VideoWriter(filepath, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

            start = time.time()
            while int(time.time() - start) < CHUNK_DURATION:
                ret, frame = cap.read()
                if not ret:
                    logging.warning("⚠️ Frame capture failed.")
                    break
                out.write(frame)
            out.release()
            logging.info(f"🎞 Saved {filename}")

            futures.append(executor.submit(upload_with_progress, filepath, S3_BUCKET, filename))
            futures = [f for f in futures if not f.done()]

    except KeyboardInterrupt:
        logging.info("🛑 Stopping capture.")
    finally:
        cap.release()
        executor.shutdown(wait=True)
        mqtt_client.publish(MQTT_TOPIC_STATUS, json.dumps({"camera_id": CAMERA_ID, "status": "stopped"}))
        mqtt_client.loop_stop()


# ---------------- Main ----------------
if __name__ == "__main__":
    ensure_dynamodb_table()

    # Start health ping thread
    threading.Thread(target=publish_health_status, daemon=True).start()

    # Start video recording
    record_video_chunks()