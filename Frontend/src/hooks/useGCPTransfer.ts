import { useState, useCallback } from 'react';
import recordingService from '../services/recordingService';
import { 
  GCPTransferRequest, 
  GCPTransferResponse, 
  GCPTransferListResponse,
  GCPTransferStatus 
} from '../services/types';
import { 
  ServiceError, 
  isNetworkError, 
  isAuthError, 
  isValidationError, 
  isServerError, 
  getErrorMessage 
} from '../services/errorHandler';

export const useGCPTransfer = () => {
  const [transfers, setTransfers] = useState<GCPTransferStatus[]>([]);
  const [transferStats, setTransferStats] = useState<{
    total_count: number;
    pending_count: number;
    uploading_count: number;
    completed_count: number;
    failed_count: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [transferring, setTransferring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'auth' | 'validation' | 'server' | 'unknown' | null>(null);

  // Helper function to handle errors
  const handleError = useCallback((err: unknown) => {
    if (err instanceof ServiceError) {
      setError(getErrorMessage(err));
      
      if (isNetworkError(err)) {
        setErrorType('network');
      } else if (isAuthError(err)) {
        setErrorType('auth');
      } else if (isValidationError(err)) {
        setErrorType('validation');
      } else if (isServerError(err)) {
        setErrorType('server');
      } else {
        setErrorType('unknown');
      }
    } else {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setErrorType('unknown');
    }
  }, []);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
    setErrorType(null);
  }, []);

  // Clear success state
  const clearSuccess = useCallback(() => {
    setSuccess(null);
  }, []);

  // Fetch GCP transfers
  const fetchTransfers = useCallback(async () => {
    setLoading(true);
    clearError();
    
    try {
      const response: GCPTransferListResponse = await recordingService.getGCPTransfers();
      setTransfers(response.transfers);
      setTransferStats({
        total_count: response.total_count,
        pending_count: response.pending_count,
        uploading_count: response.uploading_count,
        completed_count: response.completed_count,
        failed_count: response.failed_count,
      });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [handleError, clearError]);

  // Transfer recordings to GCP
  const transferToGCP = useCallback(async (transferData: GCPTransferRequest): Promise<GCPTransferResponse | null> => {
    setTransferring(true);
    clearError();
    clearSuccess();
    
    try {
      const response: GCPTransferResponse = await recordingService.transferToGCP(transferData);
      
      // Set success message
      setSuccess(response.message);
      
      // Refresh transfers list after a short delay to allow backend processing
      setTimeout(() => {
        fetchTransfers();
      }, 1000);
      
      return response;
    } catch (err) {
      handleError(err);
      return null;
    } finally {
      setTransferring(false);
    }
  }, [handleError, clearError, clearSuccess, fetchTransfers]);

  // Transfer all recordings
  const transferAllRecordings = useCallback(async (batchSize: number = 5): Promise<GCPTransferResponse | null> => {
    return transferToGCP({ batch_size: batchSize });
  }, [transferToGCP]);

  // Transfer specific recordings
  const transferSpecificRecordings = useCallback(async (
    recordingIds: string[], 
    batchSize: number = 5
  ): Promise<GCPTransferResponse | null> => {
    return transferToGCP({ 
      recording_ids: recordingIds, 
      batch_size: batchSize 
    });
  }, [transferToGCP]);

  // Get transfer status by ID
  const getTransferById = useCallback((transferId: string): GCPTransferStatus | undefined => {
    return transfers.find(transfer => transfer.transfer_id === transferId);
  }, [transfers]);

  // Get transfers by status
  const getTransfersByStatus = useCallback((status: GCPTransferStatus['transfer_status']): GCPTransferStatus[] => {
    return transfers.filter(transfer => transfer.transfer_status === status);
  }, [transfers]);

  // Check if any transfers are in progress
  const hasActiveTransfers = useCallback((): boolean => {
    return transfers.some(transfer => 
      transfer.transfer_status === 'pending' || 
      transfer.transfer_status === 'uploading'
    );
  }, [transfers]);

  // Get transfer progress percentage
  const getTransferProgress = useCallback((): number => {
    if (!transferStats || transferStats.total_count === 0) return 0;
    
    const completedCount = transferStats.completed_count;
    const totalCount = transferStats.total_count;
    
    return Math.round((completedCount / totalCount) * 100);
  }, [transferStats]);

  return {
    // Data
    transfers,
    transferStats,
    
    // State
    loading,
    transferring,
    error,
    success,
    errorType,
    
    // Actions
    fetchTransfers,
    transferToGCP,
    transferAllRecordings,
    transferSpecificRecordings,
    clearError,
    clearSuccess,
    
    // Utilities
    getTransferById,
    getTransfersByStatus,
    hasActiveTransfers,
    getTransferProgress,
  };
};
