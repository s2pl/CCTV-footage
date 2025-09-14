# GCP Cloud Storage Setup Guide

This guide will help you set up Google Cloud Platform (GCP) Cloud Storage for storing video recordings instead of local storage.

## Prerequisites

1. A Google Cloud Platform account
2. A GCP project with billing enabled
3. Python environment with the required packages

## Step 1: Create a GCP Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note down your **Project ID** (you'll need this later)

## Step 2: Enable Cloud Storage API

1. In the GCP Console, go to **APIs & Services** > **Library**
2. Search for "Cloud Storage API"
3. Click on it and press **Enable**

## Step 3: Create a Storage Bucket

1. Go to **Cloud Storage** > **Buckets**
2. Click **Create Bucket**
3. Choose a globally unique bucket name (e.g., `your-project-recordings`)
4. Select a location (choose the closest to your users)
5. Choose storage class (Standard is recommended for frequent access)
6. Choose access control (Uniform is recommended)
7. Click **Create**

## Step 4: Create a Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Enter a name (e.g., `cctv-storage-service`)
4. Add a description (e.g., `Service account for CCTV recording storage`)
5. Click **Create and Continue**
6. Grant the following roles:
   - **Storage Object Admin** (for full control over objects in the bucket)
   - **Storage Legacy Bucket Reader** (for bucket access) - *Note: If this role is not available, use **Storage Object Viewer** instead*
7. Click **Continue** and then **Done**

## Step 5: Generate Service Account Key

1. Find your newly created service account in the list
2. Click on it to open details
3. Go to the **Keys** tab
4. Click **Add Key** > **Create New Key**
5. Choose **JSON** format
6. Click **Create**
7. The JSON key file will be downloaded automatically
8. **Important**: Store this file securely and never commit it to version control

## Step 6: Configure Environment Variables

1. Copy the downloaded JSON key file to your project directory (e.g., `Backend/credentials/gcp-service-account.json`)
2. Update your `.env` file with the following variables:

```env
# GCP Cloud Storage Configuration
GCP_STORAGE_USE_GCS=True
GCP_STORAGE_PROJECT_ID=your-actual-project-id
GCP_STORAGE_BUCKET_NAME=your-actual-bucket-name
GCP_STORAGE_CREDENTIALS_PATH=/path/to/your/service-account-key.json
```

### Alternative: Use Environment Variable for Credentials

Instead of using a file path, you can set the credentials as an environment variable:

1. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file
2. Or set the `GCP_STORAGE_CREDENTIALS_PATH` to the file path

## Step 7: Install Required Packages

Make sure you have the required GCP packages installed:

```bash
pip install google-cloud-storage google-cloud-core
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

## Step 8: Test the Configuration

1. Start your Django application
2. Try recording a video from a camera
3. Check the logs to see if the file is being uploaded to GCP Storage
4. Verify the file appears in your GCP Storage bucket

## Step 9: Configure CORS (Optional)

If you need to access files directly from a web browser, configure CORS for your bucket:

1. Go to your bucket in the GCP Console
2. Click on the **Permissions** tab
3. Click **Add Entry**
4. Add CORS configuration:

```json
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Range"],
    "maxAgeSeconds": 3600
  }
]
```

## Step 10: Set Up Bucket Lifecycle (Optional)

To automatically delete old recordings, set up a lifecycle policy:

1. Go to your bucket in the GCP Console
2. Click on the **Lifecycle** tab
3. Click **Add a Rule**
4. Configure the rule to delete objects older than a certain number of days

## Security Best Practices

1. **Never commit service account keys to version control**
2. **Use IAM roles with minimal required permissions**
3. **Enable audit logging for your bucket**
4. **Consider using signed URLs for temporary access**
5. **Set up bucket versioning if needed**
6. **Use bucket-level permissions for additional security**

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure your service account key is valid and has the correct permissions
2. **Bucket Not Found**: Verify the bucket name and that it exists in the correct project
3. **Permission Denied**: Ensure the service account has the required roles
4. **File Upload Fails**: Check your internet connection and GCP quotas

### Debug Mode

To enable debug logging for GCP operations, add this to your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'google.cloud': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Cost Optimization

1. **Choose the right storage class**: Standard for frequent access, Nearline/Coldline for archival
2. **Set up lifecycle policies**: Automatically move or delete old files
3. **Monitor usage**: Use GCP Cost Management tools
4. **Consider regional storage**: Choose storage location close to your users

## Migration from Local Storage

If you're migrating existing recordings from local storage to GCP:

1. Keep `GCP_STORAGE_USE_GCS=False` initially
2. Upload existing files to GCP Storage manually or using a migration script
3. Update the database records with the new GCP paths
4. Set `GCP_STORAGE_USE_GCS=True` to use GCP for new recordings

## Support

For issues related to:
- **GCP Setup**: Check the [GCP Documentation](https://cloud.google.com/docs)
- **Django Integration**: Check the application logs and this guide
- **Storage Service**: Review the `storage_service.py` file for implementation details
