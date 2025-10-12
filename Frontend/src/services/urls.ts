// Centralized API URLs for all services
export const API_URLS = {
  // Base API URL
  BASE: import.meta.env.VITE_API_BASE_URL || 'https://cctvapi.suvidhaen.com/v0/api',
  
  // JWT Token endpoints (Django Simple JWT)
  TOKEN: {
    OBTAIN: '/token/',
    REFRESH: '/token/refresh/',
  },

  // User Management (Django Ninja API)
  USERS: {
    // Authentication endpoints
    AUTH: {
      LOGIN: '/users/auth/login/',
      LOGOUT: '/users/auth/logout/',
      REFRESH: '/users/auth/refresh/',
      CHANGE_PASSWORD: '/users/auth/change-password/',
      REQUEST_PASSWORD_RESET: '/users/auth/request-password-reset/',
      VERIFY_PASSWORD_RESET: '/users/auth/verify-password-reset/',
    },
    
    // User management endpoints
    LIST_USERS: '/users/users/',
    CREATE_USER: '/users/users/',
    GET_USER: (userId: string | number) => `/users/users/${userId}/`,
    UPDATE_USER: (userId: string | number) => `/users/users/${userId}/`,
    DELETE_USER: (userId: string | number) => `/users/users/${userId}/`,
    TOGGLE_USER_ACTIVATION: (userId: string | number) => `/users/users/${userId}/activate/`,
    ACTIVATE_USER: (userId: string | number) => `/users/users/${userId}/activate/`,
    DEACTIVATE_USER: (userId: string | number) => `/users/users/${userId}/activate/`,
    CHANGE_USER_ROLE: (userId: string | number) => `/users/users/${userId}/change-role/`,
    
    // Profile endpoints
    GET_PROFILE: '/users/profile/',
    UPDATE_PROFILE: '/users/profile/',
    
    // Activity and session management
    GET_ACTIVITIES: '/users/activities/',
    GET_SESSIONS: '/users/sessions/',
    REVOKE_ALL_SESSIONS: '/users/sessions/revoke-all/',
    REVOKE_USER_SESSIONS: (userId: string | number) => `/users/sessions/revoke-all/?user_id=${userId}`,
    
    // Django REST Framework endpoints (DRF - Legacy)
    DRF: {
      ROOT: '/users/drf/',
      AUTH: '/users/drf/auth/',
      USERS: '/users/drf/users/',
      SESSIONS: '/users/drf/sessions/',
      ACTIVITIES: '/users/drf/activities/',
      CREATE_USER: '/users/drf/create-user/',
    },
  },

  // CCTV Management (Django Ninja API)
  CCTV: {
    // Health check
    HEALTH: '/cctv/health',
    
    CAMERAS: {
      // Main camera endpoints (Django Ninja)
      LIST_CAMERAS: '/cctv/cameras/',
      CREATE_CAMERA: '/cctv/cameras/register/',
      GET_CAMERA: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
      UPDATE_CAMERA: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
      DELETE_CAMERA: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
      
      // Recording control
      START_RECORDING: (cameraId: string) => `/cctv/cameras/${cameraId}/start_recording/`,
      STOP_RECORDING: (cameraId: string) => `/cctv/cameras/${cameraId}/stop_recording/`,
      RECORDING_STATUS: (cameraId: string) => `/cctv/cameras/${cameraId}/recording_status/`,
      RECORDING_OVERVIEW: '/cctv/cameras/recording_overview/',
      
      // Streaming
      STREAM_LIVE: (cameraId: string) => `/cctv/cameras/${cameraId}/stream/`,
      STREAM_INFO: (cameraId: string) => `/cctv/cameras/${cameraId}/stream/info/`,
      STREAM_WITH_QUALITY: (cameraId: string, quality: string) => `/cctv/cameras/${cameraId}/stream/?quality=${quality}`,
      STREAM_THUMBNAIL: (cameraId: string) => `/cctv/cameras/${cameraId}/stream/thumbnail/`,
      STREAM_SNAPSHOT: (cameraId: string) => `/cctv/cameras/${cameraId}/stream/snapshot/`,
      
      // Stream Management
      ACTIVATE_STREAM: (cameraId: string) => `/cctv/cameras/${cameraId}/activate_stream/`,
      DEACTIVATE_STREAM: (cameraId: string) => `/cctv/cameras/${cameraId}/deactivate_stream/`,
      STREAM_STATUS: (cameraId: string) => `/cctv/cameras/${cameraId}/stream_status/`,
      STREAM_HEALTH: (cameraId: string) => `/cctv/cameras/${cameraId}/stream_health/`,
      
      // Camera Recovery
      SET_CAMERA_ONLINE: (cameraId: string) => `/cctv/cameras/${cameraId}/set_online/`,
      
      // Django REST Framework viewset endpoints (DRF - Legacy)
      DRF: {
        LIST: '/cctv/cameras/',
        CREATE: '/cctv/cameras/',
        RETRIEVE: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
        UPDATE: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
        DELETE: (cameraId: string) => `/cctv/cameras/${cameraId}/`,
        TEST_CONNECTION: (cameraId: string) => `/cctv/cameras/${cameraId}/test-connection/`,
        STREAM: (cameraId: string) => `/cctv/cameras/${cameraId}/stream/`,
        START_RECORDING: (cameraId: string) => `/cctv/cameras/${cameraId}/start-recording/`,
        STOP_RECORDING: (cameraId: string) => `/cctv/cameras/${cameraId}/stop-recording/`,
        SNAPSHOT: (cameraId: string) => `/cctv/cameras/${cameraId}/snapshot/`,
        STATUS: (cameraId: string) => `/cctv/cameras/${cameraId}/status/`,
        STREAM_HEALTH: (cameraId: string) => `/cctv/cameras/${cameraId}/stream_health/`,
        TEST_RECORDING: (cameraId: string) => `/cctv/cameras/${cameraId}/test_recording/`,
      },
    },
    
    STREAMS: {
      // Django Ninja endpoints
      LIST_STREAMS: '/cctv/streams/',
      GET_ACTIVE_STREAMS: '/cctv/streams/active/',
      
      // New Live Stream Activation endpoints (Django Ninja)
      ACTIVATE_STREAM: (cameraId: string) => `/cctv/cameras/${cameraId}/activate_stream/`,
      DEACTIVATE_STREAM: (cameraId: string) => `/cctv/cameras/${cameraId}/deactivate_stream/`,
      GET_STREAM_STATUS: (cameraId: string) => `/cctv/cameras/${cameraId}/stream_status/`,
      
      // Django REST Framework endpoints (DRF - Legacy)
      DRF: {
        LIST: '/cctv/live-streams/',
        CREATE: '/cctv/live-streams/',
        RETRIEVE: (streamId: string) => `/cctv/live-streams/${streamId}/`,
        UPDATE: (streamId: string) => `/cctv/live-streams/${streamId}/`,
        DELETE: (streamId: string) => `/cctv/live-streams/${streamId}/`,
        START: (streamId: string) => `/cctv/live-streams/${streamId}/start/`,
        STOP: (streamId: string) => `/cctv/live-streams/${streamId}/stop/`,
      },
      
      // Media streaming endpoints (DRF)
      STREAM_VIDEO: (streamId: string) => `/cctv/stream/${streamId}/`,
      STREAM_VIDEO_QUALITY: (streamId: string, quality: string) => `/cctv/stream/${streamId}/${quality}/`,
    },
    
    RECORDINGS: {
      // Django Ninja endpoints
      LIST_RECORDINGS: '/cctv/recordings/',
      GET_RECORDING: (recordingId: string) => `/cctv/recordings/${recordingId}/`,
      GET_STATS: '/cctv/recordings/stats/',
      
      // GCP Transfer endpoints
      TRANSFER_TO_GCP: '/cctv/recordings/transfer-to-gcp/',
      GCP_TRANSFERS: '/cctv/recordings/gcp-transfers/',
      
      // Django REST Framework endpoints (DRF - Legacy)
      DRF: {
        LIST: '/cctv/recordings/',
        CREATE: '/cctv/recordings/',
        RETRIEVE: (recordingId: string) => `/cctv/recordings/${recordingId}/`,
        UPDATE: (recordingId: string) => `/cctv/recordings/${recordingId}/`,
        DELETE: (recordingId: string) => `/cctv/recordings/${recordingId}/`,
        DOWNLOAD: (recordingId: string) => `/cctv/recordings/${recordingId}/download/`,
        THUMBNAIL: (recordingId: string) => `/cctv/recordings/${recordingId}/thumbnail/`,
        DELETE_FILE: (recordingId: string) => `/cctv/recordings/${recordingId}/delete-file/`,
      },
      
      // Playback endpoints (DRF)
      PLAYBACK: (recordingId: string) => `/cctv/playback/${recordingId}/`,
      PLAYBACK_QUALITY: (recordingId: string, quality: string) => `/cctv/playback/${recordingId}/${quality}/`,
    },
    
    SCHEDULES: {
      // Django Ninja endpoints
      LIST_SCHEDULES: '/cctv/schedules/',
      CREATE_SCHEDULE: '/cctv/schedules/',
      GET_SCHEDULE: (scheduleId: string) => `/cctv/schedules/${scheduleId}/`,
      UPDATE_SCHEDULE: (scheduleId: string) => `/cctv/schedules/${scheduleId}/`,
      DELETE_SCHEDULE: (scheduleId: string) => `/cctv/schedules/${scheduleId}/`,
      ACTIVATE_SCHEDULE: (scheduleId: string) => `/cctv/schedules/${scheduleId}/activate/`,
      DEACTIVATE_SCHEDULE: (scheduleId: string) => `/cctv/schedules/${scheduleId}/deactivate/`,
      GET_SCHEDULE_STATUS: (scheduleId: string) => `/cctv/schedules/${scheduleId}/status/`,
      
      // Django REST Framework endpoints (DRF - Legacy)
      DRF: {
        LIST: '/cctv/recording-schedules/',
        CREATE: '/cctv/recording-schedules/',
        RETRIEVE: (scheduleId: string) => `/cctv/recording-schedules/${scheduleId}/`,
        UPDATE: (scheduleId: string) => `/cctv/recording-schedules/${scheduleId}/`,
        DELETE: (scheduleId: string) => `/cctv/recording-schedules/${scheduleId}/`,
        ACTIVATE: (scheduleId: string) => `/cctv/recording-schedules/${scheduleId}/activate/`,
        DEACTIVATE: (scheduleId: string) => `/cctv/recording-schedules/${scheduleId}/deactivate/`,
      },
    },
    
    DASHBOARD: {
      // Django Ninja endpoints
      GET_ANALYTICS: '/cctv/dashboard/analytics',
      GET_RECENT_ACTIVITY: '/cctv/dashboard/activity',
      GET_ACTIVITY_WITH_LIMIT: (limit: number) => `/cctv/dashboard/activity?limit=${limit}`,
    },
    
    ACCESS: {
      // Django REST Framework endpoints (DRF - Legacy)
      DRF: {
        LIST: '/cctv/camera-access/',
        CREATE: '/cctv/camera-access/',
        RETRIEVE: (accessId: string) => `/cctv/camera-access/${accessId}/`,
        UPDATE: (accessId: string) => `/cctv/camera-access/${accessId}/`,
        DELETE: (accessId: string) => `/cctv/camera-access/${accessId}/`,
        GRANT_ACCESS: (accessId: string) => `/cctv/camera-access/${accessId}/grant/`,
        REVOKE_ACCESS: (accessId: string) => `/cctv/camera-access/${accessId}/revoke/`,
      },
    },
    
    // System status endpoints (DRF)
    STATUS: {
      OVERVIEW: '/cctv/status/overview/',
      CAMERAS: '/cctv/status/cameras/',
      RECORDINGS: '/cctv/status/recordings/',
      TEST_CONNECTION: '/cctv/test-connection/',
    },
  },

  // Mailer Service (Django Ninja API)
  MAILER: {
    // Public endpoints (no authentication required)
    PUBLIC: {
      REQUEST_PASSWORD_RESET: '/mail/request-password-reset',
      VERIFY_OTP: '/mail/verify-otp',
      RESEND_OTP: '/mail/resend-otp',
    },
    
    // Authenticated endpoints
    AUTH: {
      SEND_EMAIL: '/mail/auth/send-email',
      GENERATE_OTP: '/mail/auth/generate-otp',
      VERIFY_OTP_AUTH: '/mail/auth/verify-otp-auth',
      SEND_WELCOME_EMAIL: '/mail/auth/send-welcome-email',
      SEND_BULK_EMAIL: '/mail/auth/send-bulk-email',
      SEND_EMAIL_ATTACHMENT: '/mail/auth/send-email-attachment',
      SEND_BULK_CREATOR_MAIL: '/mail/auth/send-bulk-creator-mail',
      SEND_GENERAL_BULK_MAIL: '/mail/auth/send-general-bulk-mail',
      GET_CREATOR_MAIL_STATUS: (campaignId: string | number) => `/mail/auth/creator-mail-status/${campaignId}`,
      GET_GENERAL_MAIL_STATUS: (campaignId: string | number) => `/mail/auth/general-mail-status/${campaignId}`,
      GET_RECENT_CAMPAIGNS: '/mail/auth/recent-campaigns',
      GET_CAMPAIGN_DETAILS: (campaignId: string | number) => `/mail/auth/campaign-details/${campaignId}`,
      PREVIEW_TEMPLATE: '/mail/auth/preview-template',
    },
  },

  // Admin Service (Django Ninja API)
  ADMIN: {
    // Main admin panel endpoints
    PANELS: {
      LIST: '/admin/panels',
      CREATE: '/admin/panels',
      GET_PANEL: (panelId: string | number) => `/admin/panels/${panelId}`,
      DELETE_PANEL: (panelId: string | number) => `/admin/panels/${panelId}`,
    },
    CSRF_TOKEN: '/admin/csrf-token',
    
    // Custom admin endpoints (DRF - from admin app urls.py)
    CUSTOM: {
      VIEW_DETAILS: (id: number) => `/admin/view/${id}/`,
      PROCESS_ITEM: (id: number) => `/admin/process/${id}/`,
    },
  },

  // General Service (Django Ninja API) 
  // NOTE: This app exists but is NOT included in main URL configuration
  // To use these endpoints, you need to add the general app to config/urls.py
  GENERAL: {
    // Available endpoints (if general app is added to main URLs)
    UPLOAD_CSV: '/general/upload-csv',
    DASHBOARD: '/general/dashboard', 
    SETTINGS: '/general/settings',
  },
};

// Helper function to build full URLs
export const buildUrl = (endpoint: string): string => {
  return `${API_URLS.BASE}${endpoint}`;
};

// Helper function to build URLs with parameters
export const buildUrlWithParams = (endpoint: string, params: Record<string, string | number>): string => {
  let url = `${API_URLS.BASE}${endpoint}`;
  
  // Replace path parameters
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`:${key}`, String(value));
  });
  
  return url;
};

// Helper function to build URLs with query parameters
export const buildUrlWithQuery = (endpoint: string, queryParams: Record<string, string | number | boolean>): string => {
  let url = `${API_URLS.BASE}${endpoint}`;
  
  const searchParams = new URLSearchParams();
  Object.entries(queryParams).forEach(([key, value]) => {
    searchParams.append(key, String(value));
  });
  
  const queryString = searchParams.toString();
  if (queryString) {
    url += `?${queryString}`;
  }
  
  return url;
};

// API endpoint categories for easy access
export const API_CATEGORIES = {
  AUTH: 'Authentication & Authorization',
  USERS: 'User Management', 
  CCTV: 'CCTV & Surveillance',
  MAILER: 'Email & Communications',
  ADMIN: 'Administration',
  GENERAL: 'General System (Not Active)',
  TOKEN: 'JWT Token Management',
} as const;

// Export types for better TypeScript support
export type ApiCategory = keyof typeof API_CATEGORIES;
export type ApiUrls = typeof API_URLS;

// Missing endpoints that may need to be created
export const MISSING_ENDPOINTS = {
  // These endpoints were referenced in the old URLs but don't exist in the backend
  USERS: {
    // Legacy endpoints that don't exist in the current implementation
    CHECK_USERNAME: '/users/check-username/',
    UPDATE_USERNAME: '/users/update-username',
    UPLOAD_AVATAR: (userId: string | number) => `/users/upload-avatar/${userId}`,
    SIGNUP: '/users/signup/',
  },
  
  GENERAL: {
    // General app endpoints exist but app is not included in main URLs
    // To activate, add this line to config/urls.py:
    // path(f'{version}{sub}/general/', include('apps.general.urls')),
    NOTE: 'General app exists but not included in main URL configuration',
  },
  
  ADMIN: {
    // Extended admin endpoints that were planned but not implemented
    SYSTEM_HEALTH: '/admin/system/health/',
    SYSTEM_LOGS: '/admin/system/logs/', 
    USER_ACTIVITY: '/admin/system/user-activity/',
    SYSTEM_STATS: '/admin/system/stats/',
  },
} as const;