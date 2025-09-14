export interface Camera {
  id: string;
  name: string;
  description?: string;
  ip_address: string;
  port?: number;
  username?: string;
  password?: string;
  rtsp_url?: string;
  rtsp_url_sub?: string;
  rtsp_path?: string;
  camera_type?: string;
  status: string;
  location?: string;
  auto_record?: boolean;
  record_quality?: string;
  max_recording_hours?: number;
  is_public?: boolean;
  is_online: boolean;
  last_seen?: string | null;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
  recording_count?: number;
}

export interface CameraRegistration {
  name: string;
  description?: string;
  ip_address?: string;
  port?: number;
  username?: string;
  password?: string;
  rtsp_url: string;
  rtsp_url_sub?: string;
  rtsp_path?: string;
  camera_type?: string;
  location?: string;
  auto_record?: boolean;
  record_quality?: string;
  max_recording_hours?: number;
  is_public?: boolean;
  test_connection?: boolean;
  start_recording?: boolean;
  is_online?: boolean;
}

export interface RecordingSchedule {
  id: string;
  camera: string;
  camera_name?: string;
  name: string;
  schedule_type: 'once' | 'daily' | 'weekly' | 'continuous';
  start_time: string;
  end_time: string;
  start_date?: string;
  end_date?: string;
  days_of_week?: string[];
  recording_quality?: string;
  is_active: boolean;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SchedulesListResponse {
  total_schedules: number;
  active_schedules: number;
  schedules: RecordingSchedule[];
}

export interface Recording {
  id: string;
  camera: string;
  camera_name?: string;
  schedule?: string | null;
  schedule_name?: string | null;
  name: string;
  status: 'recording' | 'completed' | 'failed' | 'paused';
  start_time: string;
  end_time?: string;
  duration?: string;
  duration_seconds?: number;
  file_size?: number;
  file_size_mb?: number;
  file_path?: string;
  file_url?: string;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
  error_message?: string | null;
  resolution?: string;
  frame_rate?: number;
  codec?: string;
  is_active?: boolean;
  file_exists?: boolean;
  absolute_file_path?: string;
}

export interface RecordingControl {
  duration_minutes?: number;
  recording_name?: string;
  quality?: string;
}

export interface RecordingStatus {
  camera_id: string;
  camera_name: string;
  is_recording: boolean;
  recording_info?: {
    recording_id: string;
    recording_name: string;
    start_time: string;
    elapsed_seconds: number;
    elapsed_formatted: string;
    frame_count: number;
    duration_minutes?: number;
    estimated_end_time?: string;
  };
  recent_recordings: Array<{
    id: string;
    name: string;
    status: string;
    start_time: string;
    duration?: string;
    file_size_mb: number;
  }>;
}

export interface StreamInfo {
  camera_id: string;
  camera_name: string;
  camera_status: string;
  is_online: boolean;
  is_streaming: boolean;
  stream_info?: any;
  active_session?: {
    session_id: string;
    start_time: string;
    duration_seconds: number;
    user: string;
  };
  stream_urls: {
    main: string;
    sub: string;
  };
  supported_qualities: string[];
}

export interface RecordingStats {
  total_recordings: number;
  completed_recordings: number;
  failed_recordings: number;
  active_recordings?: number;
  total_size_bytes?: number;
  total_size_gb?: number;
  total_duration_seconds?: number;
  total_duration_hours?: number;
  success_rate?: number;
}

export interface RecordingsListResponse {
  total_recordings: number;
  completed_recordings: number;
  failed_recordings: number;
  recordings: Recording[];
}

export interface ActiveStream {
  stream_key: string;
  camera_id: string;
  camera_name: string;
  quality: string;
  start_time: string;
  frame_count: number;
  is_healthy: boolean;
}

export interface ActiveStreamsResponse {
  total_active_streams: number;
  streams: ActiveStream[];
}

export interface CameraAccess {
  id: string;
  camera: string;
  user: number;
  can_view: boolean;
  can_control: boolean;
  can_record: boolean;
  created_at: string;
  updated_at: string;
}

export interface LiveStream {
  id: string;
  camera: string;
  camera_name?: string;
  user: number;
  user_username?: string;
  session_id: string;
  client_ip: string;
  user_agent: string;
  start_time: string;
  end_time?: string;
  is_active: boolean;
  duration_seconds?: number;
}

export interface StreamActivationResponse {
  success: boolean;
  message: string;
  stream_info: {
    session_id: string;
    camera_id: string;
    camera_name: string;
    quality: string;
    stream_url: string;
    rtsp_url: string;
    start_time: string;
  };
}

export interface StreamStatusResponse {
  camera_id: string;
  camera_name: string;
  stream_status: {
    is_active: boolean;
    session_id?: string;
    start_time?: string;
    duration_seconds?: number;
    quality?: string;
    client_ip?: string;
    user_agent?: string;
  };
  stream_manager_status: {
    is_streaming: boolean;
    frame_count?: number;
    last_frame_time?: string;
    stream_health?: string;
  };
}

export interface StreamHealthResponse {
  camera_id: string;
  camera_name: string;
  health_status: string;
  health_details: {
    connection_status: string;
    frame_rate: number;
    last_frame_time: string;
    frame_drops: number;
    buffer_health: string;
    stream_quality: string;
  };
  performance_metrics: {
    average_frame_time_ms: number;
    total_frames: number;
    dropped_frames: number;
    uptime_seconds: number;
  };
}

export interface SnapshotResponse {
  message: string;
  snapshot_id: string;
  file_path: string;
  file_url: string;
  captured_at: string;
  camera_name: string;
}

export interface ScheduleStatusResponse {
  schedule_id: string;
  schedule_name: string;
  camera_name: string;
  schedule_type: string;
  scheduler_info: {
    is_active: boolean;
    next_run_time?: string;
    last_run_time?: string;
    total_runs: number;
    missed_runs: number;
  };
  schedule_details: {
    start_time: string;
    end_time: string;
    start_date?: string;
    end_date?: string;
    days_of_week: string[];
    is_active: boolean;
  };
}

export interface ApiResponse {
  message: string;
  success?: boolean;
  [key: string]: string | number | boolean | undefined;
}

export interface CameraRegistrationResponse {
  message: string;
  camera: {
    id: string;
    name: string;
    ip_address: string;
    rtsp_url: string;
    rtsp_path?: string;
    status: string;
    location?: string;
  };
  recording?: {
    id: string;
    name: string;
    duration_minutes: number;
    estimated_end_time: string;
  };
  warning?: string;
}

export interface SetCameraOnlineResponse {
  success: boolean;
  message: string;
  camera_id: string;
  camera_name: string;
  previous_status: string;
  current_status: string;
  is_online: boolean;
  last_seen: string | null;
  stream_auto_started: boolean;
  stream_urls: {
    main: string;
    sub: string | null;
  };
  timestamp: string;
}

export interface ScheduleResponse {
  message: string;
  schedule_id: string;
}

export interface RecordingOverview {
  total_cameras: number;
  recording_cameras: number;
  online_cameras: number;
  cameras: Array<{
    camera_id: string;
    camera_name: string;
    ip_address: string;
    status: string;
    is_online: boolean;
    is_recording: boolean;
    total_recordings: number;
    last_recording?: {
      id: string;
      name: string;
      start_time: string;
      status: string;
    };
  }>;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
  features: string[];
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  status: string;
  connection_time_ms?: number;
  rtsp_url: string;
  tested_at: string;
}

export interface MultiStreamDashboardResponse {
  total_cameras: number;
  online_cameras: number;
  recording_cameras: number;
  cameras: Array<{
    camera_id: string;
    camera_name: string;
    status: string;
    is_online: boolean;
    is_streaming: boolean;
    stream_health: any;
    stream_urls: {
      main: string;
      sub?: string;
    };
    location: string;
    last_seen?: string;
    rtsp_url: string;
    supported_qualities: string[];
  }>;
}

export interface StreamSystemStatusResponse {
  message: string;
  timestamp: string;
  status: string;
  note: string;
}

// Dashboard Analytics Types
export interface CameraStatusDistribution {
  status: string;
  count: number;
}

export interface RecordingActivity {
  date: string;
  day: string;
  recordings: number;
}

export interface HourlyActivity {
  hour: string;
  recordings: number;
}

export interface ScheduleTypeDistribution {
  schedule_type: string;
  count: number;
}

export interface StorageUsage {
  date: string;
  storage_gb: number;
}

export interface SystemMetrics {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  total_recordings: number;
  total_schedules: number;
  active_schedules: number;
  uptime_percentage: number;
}

export interface DashboardAnalytics {
  camera_status_distribution: CameraStatusDistribution[];
  recording_activity_7_days: RecordingActivity[];
  hourly_activity_today: HourlyActivity[];
  schedule_type_distribution: ScheduleTypeDistribution[];
  storage_usage_30_days: StorageUsage[];
  system_metrics: SystemMetrics;
}

// Recent Activity Types
export interface RecentActivity {
  id: string;
  type: 'recording' | 'schedule' | 'camera';
  title: string;
  description: string;
  camera_name: string;
  camera_id: string;
  timestamp: string;
  status: string;
  metadata: Record<string, any>;
}

export interface RecentActivityResponse {
  activities: RecentActivity[];
  total_count: number;
  last_updated: string;
}

// GCP Video Transfer Types
export interface GCPTransferRequest {
  recording_ids?: string[];
  batch_size?: number;
}

export interface GCPTransferResponse {
  message: string;
  total_recordings: number;
  initiated_transfers: number;
  already_transferred: number;
  failed_initiations: number;
  transfer_ids: string[];
}

export interface GCPTransferStatus {
  transfer_id: string;
  recording_name: string;
  transfer_status: 'pending' | 'uploading' | 'completed' | 'failed' | 'cleanup_pending' | 'cleanup_completed';
  file_size_mb: number;
  gcp_storage_path?: string;
  gcp_public_url?: string;
  upload_started_at?: string;
  upload_completed_at?: string;
  cleanup_scheduled_at?: string;
  cleanup_completed_at?: string;
  error_message?: string;
  retry_count: number;
}

export interface GCPTransferListResponse {
  transfers: GCPTransferStatus[];
  total_count: number;
  pending_count: number;
  uploading_count: number;
  completed_count: number;
  failed_count: number;
}