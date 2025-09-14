# Fix GCP Storage Permissions

## Issue
The service account `cctv-feed@learningdevops-455404.iam.gserviceaccount.com` doesn't have the required permissions to upload objects to the GCP bucket.

## Required Permissions
The service account needs these permissions:
- `storage.objects.create` - to upload video files
- `storage.objects.get` - to download/read video files  
- `storage.objects.delete` - to delete old recordings
- `storage.objects.list` - to list recordings

## Fix Options

### Option 1: Grant Storage Object Admin Role (Recommended)
```bash
# Run in Google Cloud Shell or with gcloud CLI
gcloud projects add-iam-policy-binding learningdevops-455404 \
    --member="serviceAccount:cctv-feed@learningdevops-455404.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### Option 2: Grant Bucket-Level Permissions
```bash
# Set bucket-level permissions
gsutil iam ch serviceAccount:cctv-feed@learningdevops-455404.iam.gserviceaccount.com:objectAdmin gs://cctv_feed
```

### Option 3: Use Google Cloud Console
1. Go to [Google Cloud Console IAM](https://console.cloud.google.com/iam-admin/iam?project=learningdevops-455404)
2. Find the service account: `cctv-feed@learningdevops-455404.iam.gserviceaccount.com`
3. Click "Edit" (pencil icon)
4. Click "Add Another Role"
5. Select "Storage Object Admin" role
6. Click "Save"

## Test After Fixing
After granting permissions, test the upload:
```bash
cd Backend
python test_gcp_storage.py
```

## Enable GCP Storage
Once permissions are fixed, enable GCP storage in settings:
```python
# In config/settings.py
GCP_STORAGE_USE_GCS = True
```
