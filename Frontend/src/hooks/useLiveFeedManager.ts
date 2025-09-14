import { useState, useCallback } from 'react';
import { usePageVisibility } from './usePageVisibility';

interface UseLiveFeedManagerOptions {
  isOnLiveFeedPage: boolean;
  autoPauseOnPageHidden?: boolean;
  bandwidthSaverMode?: boolean;
}

export const useLiveFeedManager = (options: UseLiveFeedManagerOptions) => {
  const [isManuallyPaused, setIsManuallyPaused] = useState(false);
  const [streamKey, setStreamKey] = useState(0);

  const { isFullyVisible } = usePageVisibility();

  // Determine if streaming should be active - simplified logic
  const shouldStream = options.isOnLiveFeedPage && !isManuallyPaused;
  const shouldStreamWithVisibility = shouldStream && (options.autoPauseOnPageHidden ? isFullyVisible : true);
  
  // Calculate pause state without storing it in state to avoid loops
  const isPaused = !shouldStreamWithVisibility;

  const togglePause = useCallback(() => {
    const newPausedState = !isManuallyPaused;
    setIsManuallyPaused(newPausedState);
    
    if (!newPausedState) {
      setStreamKey(prev => prev + 1); // Force refresh when resuming
    }
    
    console.log(newPausedState ? '⏸️ Manually paused streams' : '▶️ Manually resumed streams');
  }, [isManuallyPaused]);

  const refreshStreams = useCallback(() => {
    setStreamKey(prev => prev + 1);
    console.log('🔄 Refreshing streams');
  }, []);

  const forceResume = useCallback(() => {
    setIsManuallyPaused(false);
    setStreamKey(prev => prev + 1);
    console.log('▶️ Force resuming streams');
  }, []);

  return {
    // State
    isPaused,
    isManuallyPaused,
    shouldStream: shouldStreamWithVisibility,
    streamKey,
    isPageVisible: isFullyVisible,
    
    // Actions
    togglePause,
    refreshStreams,
    forceResume,
    
    // Status info
    pauseReason: isPaused ? (
      isManuallyPaused ? 'manually-paused' : 
      !options.isOnLiveFeedPage ? 'not-on-page' : 
      !isFullyVisible ? 'page-hidden' : 'unknown'
    ) : null
  };
};
