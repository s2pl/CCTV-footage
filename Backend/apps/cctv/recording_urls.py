"""
Additional views for recording URL generation and GCP integration
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


def get_recording_url_view(self, request, pk=None):
    """Get direct URL for recording (for programmatic access)"""
    recording = self.get_object()
    
    try:
        from .storage_service import storage_service
        
        logger.info(f"URL request for recording {recording.id}: {recording.name}")
        
        # Check if file exists in storage
        if not recording.file_exists:
            logger.error(f"Recording file not found: {recording.file_path}")
            return Response(
                {'error': 'Recording file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate appropriate URL based on storage type
        if recording.storage_type == 'gcp' or getattr(settings, 'GCP_STORAGE_USE_GCS', False):
            # Generate signed URL for GCP
            file_url = storage_service.get_file_url(
                recording.file_path, 
                signed=True, 
                expiration_minutes=120
            )
            
            if file_url:
                logger.info(f"✅ Generated URL for {recording.name}")
                return Response({
                    'url': file_url,
                    'storage_type': 'gcp',
                    'expires_in_minutes': 120,
                    'content_type': get_content_type_for_file(recording.file_path),
                    'file_size': recording.file_size,
                    'file_size_mb': recording.file_size_mb,
                    'recording_name': recording.name,
                    'camera_name': recording.camera.name,
                    'created_at': recording.created_at,
                    'duration': recording.duration.total_seconds() if recording.duration else None
                })
            else:
                logger.error(f"Failed to generate URL for {recording.file_path}")
                return Response(
                    {'error': 'Unable to generate URL from GCP storage'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Generate local URL
            file_url = storage_service.get_file_url(recording.file_path)
            
            return Response({
                'url': request.build_absolute_uri(file_url) if file_url else None,
                'storage_type': 'local',
                'expires_in_minutes': None,
                'content_type': get_content_type_for_file(recording.file_path),
                'file_size': recording.file_size,
                'file_size_mb': recording.file_size_mb,
                'recording_name': recording.name,
                'camera_name': recording.camera.name,
                'created_at': recording.created_at,
                'duration': recording.duration.total_seconds() if recording.duration else None
            })
            
    except Exception as e:
        logger.error(f"Error getting URL for recording {recording.id}: {str(e)}")
        return Response(
            {
                'error': str(e),
                'recording_id': str(recording.id),
                'storage_type': recording.storage_type
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_content_type_for_file(file_path):
    """Get content type based on file extension"""
    file_extension = os.path.splitext(file_path)[1].lower()
    content_type_map = {
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.flv': 'video/x-flv'
    }
    return content_type_map.get(file_extension, 'video/mp4')


def get_bulk_recording_urls_view(self, request):
    """Get URLs for multiple recordings at once"""
    try:
        from .storage_service import storage_service
        
        # Get recording IDs from request
        recording_ids = request.GET.getlist('ids', [])
        if not recording_ids:
            return Response(
                {'error': 'No recording IDs provided. Use ?ids=uuid1&ids=uuid2'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get recordings
        recordings = self.get_queryset().filter(id__in=recording_ids)
        
        results = []
        for recording in recordings:
            try:
                if not recording.file_exists:
                    results.append({
                        'recording_id': str(recording.id),
                        'error': 'File not found',
                        'url': None
                    })
                    continue
                
                # Generate URL based on storage type
                if recording.storage_type == 'gcp' or getattr(settings, 'GCP_STORAGE_USE_GCS', False):
                    file_url = storage_service.get_file_url(
                        recording.file_path, 
                        signed=True, 
                        expiration_minutes=120
                    )
                else:
                    file_url = storage_service.get_file_url(recording.file_path)
                    if file_url:
                        file_url = request.build_absolute_uri(file_url)
                
                results.append({
                    'recording_id': str(recording.id),
                    'recording_name': recording.name,
                    'camera_name': recording.camera.name,
                    'url': file_url,
                    'storage_type': recording.storage_type,
                    'content_type': get_content_type_for_file(recording.file_path),
                    'file_size': recording.file_size,
                    'file_size_mb': recording.file_size_mb,
                    'created_at': recording.created_at,
                    'duration': recording.duration.total_seconds() if recording.duration else None,
                    'expires_in_minutes': 120 if recording.storage_type == 'gcp' else None,
                    'error': None
                })
                
            except Exception as e:
                results.append({
                    'recording_id': str(recording.id),
                    'error': str(e),
                    'url': None
                })
        
        return Response({
            'recordings': results,
            'total_requested': len(recording_ids),
            'total_found': len(recordings),
            'generated_at': timezone.now() if 'timezone' in globals() else None
        })
        
    except Exception as e:
        logger.error(f"Error getting bulk recording URLs: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
