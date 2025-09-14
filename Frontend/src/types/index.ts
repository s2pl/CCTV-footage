// Re-export all types from services for convenience
export type {
  // Auth types
  LoginCredentials,
  AuthResponse,
  RegisterData,
  PasswordResetRequest,
  PasswordResetConfirm,
} from '../services/authService';

export type {
  // User types
  User,
  Permission,
  UserCreateData,
  UserUpdateData,
  UserRoleUpdate,
  UserActivationUpdate,
} from '../services/userService';

export type {
  // CCTV types
  Camera,
  CameraRegistration,
  RecordingSchedule,
  Recording,
  RecordingControl,
  RecordingStatus,
  StreamInfo,
  ActiveStream,
  RecordingStats,
} from '../services/cctvService';

export type {
  // Mailer types
  EmailData,
  OTPRequest,
  OTPVerify,
  WelcomeEmail,
  PasswordResetRequest as MailerPasswordResetRequest,
  ResendOTP,
  Recipient,
  CreatorBulkMail,
  GeneralBulkMail,
  TemplatePreview,
  CampaignStatus,
  CampaignDetails,
} from '../services/mailerService';

export type {
  // General types
  ScraperData,
  CSVUploadResponse,
} from '../services/generalService';

export type {
  // Admin types
  AdminPanel,
  AdminPanelCreate,
  CSRFResponse,
} from '../services/adminService';

// Re-export hierarchy types
export type {
  UserRole,
  USER_ROLES,
  ROLE_HIERARCHY,
  ROLE_CREATION_PERMISSIONS,
  ROLE_MANAGEMENT_PERMISSIONS,
  hierarchyUtils
} from '../services/api';

// Hierarchy-specific types
export interface RoleHierarchyNode {
  role: string;
  level: number;
  canCreate: string[];
  canManage: string[];
  displayName: string;
  description: string;
  icon: string;
  color: string;
}

export interface HierarchyValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface FeatureAccess {
  feature: string;
  accessible: boolean;
  requiredRole: string;
}

export interface UserRoleInfo {
  role: string;
  displayName: string;
  description: string;
  icon: string;
  color: string;
  permissions: {
    canCreate: string[];
    canManage: string[];
    accessibleFeatures: string[];
  };
}

// Common UI types
export interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
}

export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success: boolean;
  error?: string;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: unknown;
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox' | 'file';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: unknown) => string | null;
  };
}

export interface FormData {
  [key: string]: unknown;
}

export interface FormErrors {
  [key: string]: string;
}

// Navigation types
export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  children?: NavigationItem[];
  requiresAuth?: boolean;
  requiresAdmin?: boolean;
  badge?: string | number;
}

export interface BreadcrumbItem {
  label: string;
  path: string;
  active?: boolean;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
}

// Modal types
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

export interface ConfirmDialogProps extends ModalProps {
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel?: () => void;
  type?: 'danger' | 'warning' | 'info';
}

// Table types
export interface TableColumn<T = unknown> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  render?: (value: unknown, row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
}

export interface TableSort {
  key: string;
  direction: 'asc' | 'desc';
}

export interface TableFilter {
  key: string;
  value: unknown;
  operator: 'equals' | 'contains' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan';
}

// Chart types
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    tooltip?: {
      enabled?: boolean;
    };
  };
  scales?: {
    y?: {
      beginAtZero?: boolean;
    };
  };
}

// File types
export interface FileInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  uploadedAt: string;
  uploadedBy?: string;
}

export interface FileUploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

// Search types
export interface SearchResult<T = unknown> {
  item: T;
  score: number;
  highlights?: Array<{
    field: string;
    snippet: string;
  }>;
}

export interface SearchOptions {
  query: string;
  filters?: Record<string, unknown>;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

// Theme types
export interface Theme {
  name: string;
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}

// Settings types
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  privacy: {
    profileVisibility: 'public' | 'private' | 'friends';
    showEmail: boolean;
    showPhone: boolean;
  };
}

// Dashboard types
export interface DashboardWidget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'list' | 'custom';
  title: string;
  size: 'small' | 'medium' | 'large';
  position: { x: number; y: number };
  config: Record<string, unknown>;
}

export interface DashboardMetric {
  label: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
    period: string;
  };
  icon?: string;
  color?: string;
}

// Export all types
export * from '../services';