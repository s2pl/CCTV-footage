
# ---------------- Configuration ----------------
CAMERA_INDEX = 0
CHUNK_DURATION = 30  # seconds
OUTPUT_DIR = "video_chunks"
S3_BUCKET = "aws-cctv"
AWS_REGION = "ap-south-1"

# DynamoDB Configuration
DYNAMO_TABLE_NAME = "VideoUploadLogs"

# MQTT Configuration
MQTT_ENABLED = True
MQTT_BROKER = "your-iot-endpoint.amazonaws.com"
MQTT_PORT = 8883
MQTT_TOPIC = "camera/upload/status"
MQTT_CLIENT_ID = "CameraUploader"

# SNS (optional)
SNS_ENABLED = False
SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:123456789012:CameraUploadStatus"
