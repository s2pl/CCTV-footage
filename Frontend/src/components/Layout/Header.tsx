import React, { useState, useEffect } from 'react';
import { Moon, Sun, User, LogOut, ChevronDown, Clock, RefreshCw } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  onNavigate?: (view: string) => void;
  onRefresh?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onNavigate, onRefresh }) => {
  const { theme, toggleTheme } = useTheme();
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Always call useAuth hook, but handle errors gracefully
  let user, logout;
  try {
    const authData = useAuth();
    user = authData.user;
    logout = authData.logout;
  } catch {
    // Auth context not available yet
    user = null;
    logout = () => {};
  }

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowProfileDropdown(false);
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleLogout = () => {
    if (confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  const handleProfileClick = () => {
    if (onNavigate) {
      onNavigate('profile');
    }
    setShowProfileDropdown(false);
  };

  const handleRefresh = async () => {
    if (onRefresh) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } finally {
        // Add a small delay to show the refresh animation
        setTimeout(() => {
          setIsRefreshing(false);
        }, 1000);
      }
    } else {
      // Fallback: reload the page
      window.location.reload();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Show loading state if auth is not available
  if (!user && !logout) {
    return (
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="text-center text-gray-500">Loading header...</div>
      </div>
    );
  }

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Security Dashboard
        </h2>
        
        {/* Real-time Clock */}
        <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
          <Clock className="w-4 h-4" />
          <div className="flex flex-col">
            <span className="font-mono font-semibold">{formatTime(currentTime)}</span>
            <span className="text-xs">{formatDate(currentTime)}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Refresh Button */}
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Refresh data"
        >
          <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>

        
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </button>
        
        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowProfileDropdown(!showProfileDropdown);
            }}
            className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="text-sm text-left hidden md:block">
              <div className="text-gray-900 dark:text-white font-medium">{user?.username || user?.email || 'User'}</div>
              <div className="text-gray-500 dark:text-gray-400">{user?.role || 'User'}</div>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          </button>

          {showProfileDropdown && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
              <div className="p-2">
                <button
                  onClick={handleProfileClick}
                  className="w-full flex items-center space-x-2 p-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <User className="w-4 h-4" />
                  <span>View Profile</span>
                </button>
                <hr className="my-2 border-gray-200 dark:border-gray-600" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 p-2 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;