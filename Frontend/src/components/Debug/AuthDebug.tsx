import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { logTokenStatus } from '../../utils/tokenUtils';

const AuthDebug: React.FC = () => {
  // Add safety check for auth context
  let authData;
  try {
    authData = useAuth();
  } catch (error) {
    // Auth context not available yet
    return (
      <div className="p-4 bg-yellow-100 rounded">
        <p className="text-yellow-800">Auth context initializing...</p>
      </div>
    );
  }

  const { user, isAuthenticated, isLoading, debugTokens } = authData;

  const handleRefreshToken = async () => {
    try {
      console.log('Manually refreshing token...');
      await debugTokens();
      // You can add manual refresh logic here if needed
    } catch (error) {
      console.error('Manual refresh failed:', error);
    }
  };

  const handleCheckTokens = () => {
    logTokenStatus();
  };

  if (isLoading) {
    return <div className="p-4 bg-yellow-100 rounded">Loading authentication...</div>;
  }

  return (
    <div className="p-4 bg-gray-100 rounded-lg border">
      <h3 className="text-lg font-semibold mb-4">Authentication Debug</h3>
      
      <div className="space-y-3">
        <div>
          <strong>Status:</strong> {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
        </div>
        
        {user && (
          <div>
            <strong>User:</strong> {user.username} ({user.email})
          </div>
        )}
        
        <div className="flex space-x-2">
          <button
            onClick={handleCheckTokens}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Check Token Status
          </button>
          
          <button
            onClick={handleRefreshToken}
            className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Debug Tokens
          </button>
        </div>
        
        <div className="text-sm text-gray-600">
          Check the browser console for detailed token information
        </div>
      </div>
    </div>
  );
};

export default AuthDebug;
