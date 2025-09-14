import { useState, useEffect } from 'react';

interface UsePageVisibilityOptions {
  onVisibilityChange?: (isVisible: boolean) => void;
  pauseOnHidden?: boolean;
}

export const usePageVisibility = (options: UsePageVisibilityOptions = {}) => {
  const [isVisible, setIsVisible] = useState(!document.hidden);
  const [isPageActive, setIsPageActive] = useState(true);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden;
      setIsVisible(visible);
      
      if (options.onVisibilityChange) {
        options.onVisibilityChange(visible);
      }
    };

    const handleFocus = () => setIsPageActive(true);
    const handleBlur = () => setIsPageActive(false);

    // Page Visibility API
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Window focus/blur events (backup)
    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [options.onVisibilityChange]);

  return {
    isVisible,
    isPageActive,
    isFullyVisible: isVisible && isPageActive
  };
};
