// Token utility functions for debugging and management

export interface TokenInfo {
  isValid: boolean;
  expiresAt: Date;
  timeUntilExpiry: number; // in milliseconds
  userId?: string;
  username?: string;
}

export const parseToken = (token: string): TokenInfo | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    const expirationTime = payload.exp * 1000;
    
    return {
      isValid: payload.exp > currentTime,
      expiresAt: new Date(expirationTime),
      timeUntilExpiry: expirationTime - Date.now(),
      userId: payload.user_id,
      username: payload.username
    };
  } catch (error) {
    console.error('Error parsing token:', error);
    return null;
  }
};

export const getTokenStatus = (): {
  hasAccessToken: boolean;
  hasRefreshToken: boolean;
  accessTokenInfo: TokenInfo | null;
  refreshTokenInfo: TokenInfo | null;
} => {
  const accessToken = localStorage.getItem('accessToken');
  const refreshToken = localStorage.getItem('refreshToken');
  
  return {
    hasAccessToken: !!accessToken,
    hasRefreshToken: !!refreshToken,
    accessTokenInfo: accessToken ? parseToken(accessToken) : null,
    refreshTokenInfo: refreshToken ? parseToken(refreshToken) : null
  };
};

export const logTokenStatus = (): void => {
  const status = getTokenStatus();
  console.log('=== Token Status ===');
  console.log('Access Token:', status.hasAccessToken ? 'Present' : 'Missing');
  console.log('Refresh Token:', status.hasRefreshToken ? 'Present' : 'Missing');
  
  if (status.accessTokenInfo) {
    console.log('Access Token Info:', {
      isValid: status.accessTokenInfo.isValid,
      expiresAt: status.accessTokenInfo.expiresAt.toLocaleString(),
      timeUntilExpiry: `${Math.round(status.accessTokenInfo.timeUntilExpiry / 1000 / 60)} minutes`
    });
  }
  
  if (status.refreshTokenInfo) {
    console.log('Refresh Token Info:', {
      isValid: status.refreshTokenInfo.isValid,
      expiresAt: status.refreshTokenInfo.expiresAt.toLocaleString(),
      timeUntilExpiry: `${Math.round(status.refreshTokenInfo.timeUntilExpiry / 1000 / 60 / 60)} hours`
    });
  }
  console.log('===================');
};
