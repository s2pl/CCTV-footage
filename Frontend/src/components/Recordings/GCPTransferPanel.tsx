import React, { useState, useEffect } from 'react';
import { 
  Cloud, 
  Upload, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Trash2, 
  RefreshCw,
  Settings,
  Info,
  X,
  ExternalLink
} from 'lucide-react';
import { useGCPTransfer } from '../../hooks/useGCPTransfer';
import { GCPTransferStatus } from '../../services/types';

interface GCPTransferPanelProps {
  selectedRecordingIds: string[];
  onTransferComplete?: () => void;
}

const GCPTransferPanel: React.FC<GCPTransferPanelProps> = ({ 
  selectedRecordingIds, 
  onTransferComplete 
}) => {
  const {
    transfers,
    transferStats,
    loading,
    transferring,
    error,
    success,
    fetchTransfers,
    transferAllRecordings,
    transferSpecificRecordings,
    clearError,
    clearSuccess,
    hasActiveTransfers,
    getTransferProgress
  } = useGCPTransfer();

  const [isExpanded, setIsExpanded] = useState(false);
  const [batchSize, setBatchSize] = useState(5);
  const [showSettings, setShowSettings] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh transfers when there are active transfers
  useEffect(() => {
    if (autoRefresh && hasActiveTransfers()) {
      const interval = setInterval(() => {
        fetchTransfers();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh, hasActiveTransfers, fetchTransfers]);

  // Initial load
  useEffect(() => {
    fetchTransfers();
  }, [fetchTransfers]);

  // Auto-clear success message
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        clearSuccess();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [success, clearSuccess]);

  const handleTransferAll = async () => {
    const result = await transferAllRecordings(batchSize);
    if (result && onTransferComplete) {
      onTransferComplete();
    }
  };

  const handleTransferSelected = async () => {
    if (selectedRecordingIds.length === 0) {
      alert('Please select recordings to transfer');
      return;
    }
    
    const result = await transferSpecificRecordings(selectedRecordingIds, batchSize);
    if (result && onTransferComplete) {
      onTransferComplete();
    }
  };

  const getStatusIcon = (status: GCPTransferStatus['transfer_status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'uploading':
        return <Upload className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'cleanup_pending':
        return <Clock className="w-4 h-4 text-orange-500" />;
      case 'cleanup_completed':
        return <Trash2 className="w-4 h-4 text-gray-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: GCPTransferStatus['transfer_status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'uploading':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      case 'cleanup_pending':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300';
      case 'cleanup_completed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (sizeInMB: number) => {
    if (sizeInMB >= 1024) {
      return `${(sizeInMB / 1024).toFixed(2)} GB`;
    }
    return `${sizeInMB.toFixed(2)} MB`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <Cloud className="w-6 h-6 text-blue-500" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              GCP Cloud Storage
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Transfer recordings to Google Cloud Storage
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {transferStats && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {transferStats.completed_count}/{transferStats.total_count} completed
            </div>
          )}
          <RefreshCw 
            className={`w-5 h-5 text-gray-400 ${isExpanded ? 'rotate-180' : ''} transition-transform`} 
          />
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Error Message */}
          {error && (
            <div className="m-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                  <span className="text-red-800 dark:text-red-300 text-sm">{error}</span>
                </div>
                <button
                  onClick={clearError}
                  className="text-red-500 hover:text-red-700 dark:hover:text-red-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="m-4 p-3 bg-green-100 dark:bg-green-900/20 border border-green-300 dark:border-green-700 rounded-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                  <span className="text-green-800 dark:text-green-300 text-sm">{success}</span>
                </div>
                <button
                  onClick={clearSuccess}
                  className="text-green-500 hover:text-green-700 dark:hover:text-green-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Transfer Controls */}
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleTransferAll}
                  disabled={transferring}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {transferring ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  <span>Transfer All</span>
                </button>

                <button
                  onClick={handleTransferSelected}
                  disabled={transferring || selectedRecordingIds.length === 0}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {transferring ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  <span>Transfer Selected ({selectedRecordingIds.length})</span>
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={fetchTransfers}
                  disabled={loading}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Settings Panel */}
            {showSettings && (
              <div className="mt-4 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900 dark:text-white">Transfer Settings</h4>
                  <button
                    onClick={() => setShowSettings(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Batch Size
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={batchSize}
                      onChange={(e) => setBatchSize(parseInt(e.target.value) || 5)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Number of videos to process simultaneously (1-20)
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Auto Refresh
                    </label>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={autoRefresh}
                        onChange={(e) => setAutoRefresh(e.target.checked)}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                        Auto-refresh status every 5 seconds
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Transfer Statistics */}
          {transferStats && (
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {transferStats.total_count}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {transferStats.pending_count}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Pending</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {transferStats.uploading_count}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Uploading</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {transferStats.completed_count}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Completed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {transferStats.failed_count}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
                </div>
              </div>
            </div>
          )}

          {/* Transfer List */}
          <div className="max-h-96 overflow-y-auto">
            {loading && transfers.length === 0 ? (
              <div className="flex items-center justify-center p-8">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
                <span className="text-gray-500 dark:text-gray-400">Loading transfers...</span>
              </div>
            ) : transfers.length === 0 ? (
              <div className="text-center p-8 text-gray-500 dark:text-gray-400">
                <Cloud className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No transfers found</p>
                <p className="text-sm">Start a transfer to see status here</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {transfers.map((transfer) => (
                  <div key={transfer.transfer_id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          {getStatusIcon(transfer.transfer_status)}
                          <h4 className="font-medium text-gray-900 dark:text-white truncate">
                            {transfer.recording_name}
                          </h4>
                          <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(transfer.transfer_status)}`}>
                            {transfer.transfer_status.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500 dark:text-gray-400">
                          <div>
                            <span className="font-medium">Size:</span> {formatFileSize(transfer.file_size_mb)}
                          </div>
                          {transfer.upload_started_at && (
                            <div>
                              <span className="font-medium">Started:</span> {formatDateTime(transfer.upload_started_at)}
                            </div>
                          )}
                          {transfer.upload_completed_at && (
                            <div>
                              <span className="font-medium">Completed:</span> {formatDateTime(transfer.upload_completed_at)}
                            </div>
                          )}
                        </div>
                        
                        {transfer.error_message && (
                          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-800 dark:text-red-300">
                            <span className="font-medium">Error:</span> {transfer.error_message}
                            {transfer.retry_count > 0 && (
                              <span className="ml-2 text-xs">({transfer.retry_count} retries)</span>
                            )}
                          </div>
                        )}
                        
                        {transfer.cleanup_scheduled_at && (
                          <div className="mt-2 text-xs text-orange-600 dark:text-orange-400">
                            <Clock className="w-3 h-3 inline mr-1" />
                            Local cleanup scheduled: {formatDateTime(transfer.cleanup_scheduled_at)}
                          </div>
                        )}
                      </div>
                      
                      {transfer.gcp_public_url && (
                        <button
                          onClick={() => window.open(transfer.gcp_public_url, '_blank')}
                          className="ml-4 p-2 text-blue-500 hover:text-blue-700 dark:hover:text-blue-300 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20"
                          title="View in GCP"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GCPTransferPanel;
