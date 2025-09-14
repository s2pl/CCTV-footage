// Error handling utility for consistent error management across services

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

export interface BackendError {
  error?: string;
  message?: string;
  detail?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
}

export class ServiceError extends Error {
  public status?: number;
  public code?: string;
  public details?: unknown;

  constructor(message: string, status?: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'ServiceError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const handleApiError = (error: unknown): ServiceError => {
  console.error('API Error:', error);

  // Handle axios errors
  if (error && typeof error === 'object' && 'response' in error && error.response) {
    const { status, data } = error.response as { status: number; data: unknown };
    const backendError = data as BackendError;
    
    // Extract error message from backend response
    let message = 'An error occurred';
    
    if (backendError.error) {
      message = backendError.error;
    } else if (backendError.message) {
      message = backendError.message;
    } else if (backendError.detail) {
      message = backendError.detail;
    } else if (backendError.non_field_errors && backendError.non_field_errors.length > 0) {
      message = backendError.non_field_errors[0];
    } else if (typeof backendError === 'string') {
      message = backendError;
    } else if (typeof data === 'string') {
      message = data;
    }

    // Handle specific HTTP status codes
    switch (status) {
      case 400:
        message = `Bad Request: ${message}`;
        break;
      case 401:
        message = `Unauthorized: ${message}`;
        break;
      case 403:
        message = `Forbidden: ${message}`;
        break;
      case 404:
        message = `Not Found: ${message}`;
        break;
      case 409:
        message = `Conflict: ${message}`;
        break;
      case 422:
        message = `Validation Error: ${message}`;
        break;
      case 429:
        message = `Too Many Requests: ${message}`;
        break;
      case 500:
        message = `Internal Server Error: ${message}`;
        break;
      case 502:
        message = `Bad Gateway: ${message}`;
        break;
      case 503:
        message = `Service Unavailable: ${message}`;
        break;
      default:
        message = `Error ${status}: ${message}`;
    }

    return new ServiceError(message, status, undefined, backendError);
  }

  // Handle network errors
  if (error && typeof error === 'object' && 'request' in error && error.request) {
    return new ServiceError(
      'Network error: Unable to connect to the server. Please check your internet connection.',
      0,
      'NETWORK_ERROR'
    );
  }

  // Handle other errors
  if (error instanceof ServiceError) {
    return error;
  }

  if (error instanceof Error) {
    return new ServiceError(error.message, undefined, undefined, error);
  }

  // Handle unknown errors
  return new ServiceError(
    'An unexpected error occurred. Please try again.',
    undefined,
    'UNKNOWN_ERROR',
    error
  );
};

export const isNetworkError = (error: ServiceError): boolean => {
  return error.code === 'NETWORK_ERROR' || error.status === 0;
};

export const isAuthError = (error: ServiceError): boolean => {
  return error.status === 401 || error.status === 403;
};

export const isValidationError = (error: ServiceError): boolean => {
  return error.status === 400 || error.status === 422;
};

export const isServerError = (error: ServiceError): boolean => {
  return error.status && error.status >= 500;
};

export const getErrorMessage = (error: ServiceError): string => {
  if (isNetworkError(error)) {
    return 'Connection failed. Please check your internet connection and try again.';
  }
  
  if (isAuthError(error)) {
    return 'Authentication failed. Please log in again.';
  }
  
  if (isValidationError(error)) {
    return error.message;
  }
  
  if (isServerError(error)) {
    return 'Server error. Please try again later.';
  }
  
  return error.message || 'An unexpected error occurred.';
};

export const logError = (error: ServiceError, context: string): void => {
  console.error(`[${context}] Error:`, {
    message: error.message,
    status: error.status,
    code: error.code,
    details: error.details,
    stack: error.stack
  });
};
