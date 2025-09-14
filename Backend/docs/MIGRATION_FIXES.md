# GCP Migration Fixes

## Issues Fixed

The original migration was failing due to several issues:

### 1. **File Path Issues**
- **Problem**: Mixed path separators (forward slashes vs backslashes) on Windows
- **Fix**: Added `os.path.normpath()` to normalize file paths across platforms

### 2. **Missing Files**
- **Problem**: Migration failed when local files were missing
- **Fix**: Added proper file existence checks and `--skip-missing` option

### 3. **Temporary Files (.tmp)**
- **Problem**: Migration tried to upload incomplete `.tmp` files
- **Fix**: Added filtering to exclude `.tmp` files and `--cleanup-tmp` option

### 4. **Timeout Issues**
- **Problem**: GCP uploads timing out after 120 seconds
- **Fix**: Added configurable timeout (300s for small files, 600s for large files)

### 5. **Storage Type Not Updated**
- **Problem**: Successfully migrated files still showed as 'local' storage
- **Fix**: Added proper storage_type update to 'gcp' after successful migration

## Files Modified

### `storage_service.py`
- Added timeout parameter to `upload_file()` method
- Added file existence and `.tmp` file checks
- Added proper path normalization

### `migrate_to_gcp.py`
- Added `--skip-missing` flag to handle missing files gracefully
- Added `--cleanup-tmp` flag to remove temporary files
- Improved error handling and logging
- Added dynamic timeout based on file size
- Fixed storage_type update after successful migration
- Better progress reporting with full recording details

## New Helper Scripts

### `run_migration_fixed.py`
- Automated migration script with proper error handling
- Runs dry-run first to preview changes
- Checks GCP configuration before starting
- Shows before/after statistics

### `cleanup_failed_recordings.py`
- Helps clean up database entries for recordings with missing files
- Interactive script to identify and remove problematic records
- Safe deletion with confirmation prompts

## Usage

### 1. Run the Fixed Migration
```bash
cd Backend
python run_migration_fixed.py
```

### 2. Manual Migration with Options
```bash
cd Backend
python manage.py migrate_to_gcp --batch-size=3 --skip-missing --cleanup-tmp
```

### 3. Clean Up Failed Records (Optional)
```bash
cd Backend
python cleanup_failed_recordings.py
```

### 4. Dry Run to Preview
```bash
cd Backend
python manage.py migrate_to_gcp --dry-run
```

## Command Line Options

- `--dry-run`: Show what would be migrated without doing it
- `--batch-size=N`: Process N recordings at a time (default: 10)
- `--skip-missing`: Skip recordings with missing files instead of failing
- `--cleanup-tmp`: Remove .tmp files from recordings directory
- `--recording-id=UUID`: Migrate only a specific recording
- `--camera-id=UUID`: Migrate recordings for a specific camera

## Expected Results

After running the fixed migration:

✅ **Files that will be migrated successfully:**
- `SCHEDULED_test1_20250908_145800.mp4`
- `SCHEDULED_test1_20250909_163200.avi`
- `SCHEDULED_test1_20250909_164800.avi`
- Other valid `.mp4` and `.avi` files

⚠️ **Files that will be skipped:**
- `test1_20250908_144815.mp4` (missing)
- `SCHEDULED_test1_20250908_145200.mp4` (missing)
- `*.tmp` files (incomplete recordings)

## Troubleshooting

### If migration still fails:

1. **Check GCP permissions** (see `FIX_GCP_PERMISSIONS.md`)
2. **Verify credentials file exists**
3. **Check network connectivity to GCP**
4. **Review Django logs for specific errors**

### Common Error Messages:

- `"Local file not found"` → File missing from disk, use `--skip-missing`
- `"Timeout of 120.0s exceeded"` → Fixed with increased timeout
- `"Connection aborted"` → Network issue, check GCP connectivity
- `"Skipping .tmp file"` → Normal, temporary files are excluded

## Next Steps

1. Run the migration with the fixes applied
2. Verify recordings are accessible in GCP
3. Optionally clean up local files after successful migration
4. Update any hardcoded file paths in your application code
