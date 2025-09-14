# GCP Video Transfer Cleanup Cron Setup

This document explains how to set up automatic cleanup of local video files after they have been transferred to GCP Cloud Storage.

## Overview

After videos are successfully uploaded to GCP, the system waits 24 hours before automatically deleting the local files to free up storage space. This cleanup process is handled by a Django management command that should be run periodically.

## Management Command

The cleanup is performed by the `cleanup_gcp_transfers` management command:

```bash
python manage.py cleanup_gcp_transfers
```

### Command Options

- `--dry-run`: Show what would be cleaned up without actually deleting files
- `--force`: Force cleanup even if not yet 24 hours old (use with caution)
- `--transfer-id <id>`: Clean up a specific transfer by ID

## Cron Job Setup

### Linux/Unix Systems

Add the following cron job to run cleanup every hour:

```bash
# Edit crontab
crontab -e

# Add this line to run cleanup every hour
0 * * * * cd /path/to/your/project/Backend && python manage.py cleanup_gcp_transfers >> /var/log/gcp_cleanup.log 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to run hourly
4. Set action to run:
   ```
   Program: python
   Arguments: manage.py cleanup_gcp_transfers
   Start in: C:\path\to\your\project\Backend
   ```

### Docker Environment

If running in Docker, add to your docker-compose.yml:

```yaml
services:
  cleanup-worker:
    build: .
    command: sh -c "while true; do python manage.py cleanup_gcp_transfers; sleep 3600; done"
    volumes:
      - ./media:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
    depends_on:
      - db
```

## Monitoring

### Log Files

The cleanup command logs its activities. Monitor these logs to ensure proper operation:

- Check for successful cleanups
- Monitor for failed cleanups
- Track space freed

### Database Monitoring

Monitor the `GCPVideoTransfer` table:

```sql
-- Check transfer status counts
SELECT transfer_status, COUNT(*) 
FROM cctv_gcpvideotransfer 
GROUP BY transfer_status;

-- Check cleanup due
SELECT COUNT(*) as cleanup_due
FROM cctv_gcpvideotransfer 
WHERE transfer_status = 'cleanup_pending' 
AND cleanup_scheduled_at <= NOW();
```

### Disk Space Monitoring

Monitor your media directory disk usage:

```bash
# Check disk usage of media directory
du -sh /path/to/media/recordings/

# Check available disk space
df -h /path/to/media
```

## Troubleshooting

### Files Not Being Cleaned Up

1. Check if GCP transfers completed successfully
2. Verify 24-hour waiting period has elapsed
3. Check file permissions
4. Review cleanup command logs

### Cleanup Failures

1. Check file permissions on media directory
2. Verify files haven't been moved or deleted manually
3. Check disk space and system resources
4. Review Django logs for errors

### Manual Cleanup

If needed, you can manually clean up specific transfers:

```bash
# Dry run to see what would be cleaned
python manage.py cleanup_gcp_transfers --dry-run

# Force cleanup of specific transfer
python manage.py cleanup_gcp_transfers --transfer-id <transfer-uuid> --force

# Clean up all due transfers immediately
python manage.py cleanup_gcp_transfers
```

## Best Practices

1. **Regular Monitoring**: Check cleanup logs regularly
2. **Disk Space Alerts**: Set up alerts when disk space is low
3. **Backup Strategy**: Ensure GCP uploads are successful before cleanup
4. **Testing**: Test cleanup in staging environment first
5. **Recovery Plan**: Have a plan for recovering files if needed

## Configuration

The cleanup behavior can be configured in your Django settings:

```python
# Custom cleanup settings (if implemented)
GCP_CLEANUP_DELAY_HOURS = 24  # Default: 24 hours
GCP_CLEANUP_BATCH_SIZE = 50   # Process in batches
GCP_CLEANUP_MAX_RETRIES = 3   # Max retry attempts
```

## Integration with Monitoring Systems

### Prometheus Metrics (Optional)

If using Prometheus, you can expose cleanup metrics:

```python
from prometheus_client import Counter, Gauge

cleanup_counter = Counter('gcp_cleanup_total', 'Total files cleaned up')
cleanup_errors = Counter('gcp_cleanup_errors_total', 'Total cleanup errors')
disk_space_freed = Gauge('gcp_cleanup_space_freed_bytes', 'Bytes freed by cleanup')
```

### Health Check Endpoint

Monitor cleanup health via API:

```
GET /api/v0/recordings/gcp-transfers/
```

This endpoint shows transfer statuses and can be used for monitoring.
