import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Camera, 
  Users, 
  Monitor, 
  Calendar, 
  BarChart3,
  Eye,
  LogOut
} from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, onViewChange }) => {
  const { logout } = useAuth();
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'cameras', label: 'Cameras', icon: Camera },
    { id: 'live-feed', label: 'Live Feed', icon: Monitor },
    // { id: 'access-control', label: 'Access Control', icon: Shield },
    { id: 'recordings', label: 'Recordings', icon: Eye },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'users', label: 'Users', icon: Users },
    // Remove settings from main menu, will show as bottom button
    // { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-screen flex flex-col shadow-lg">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          CCTV Portal
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Security Management
        </p>
      </div>
      
      <nav className="flex-1 mt-6 overflow-y-auto bg-white dark:bg-gray-800">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center px-6 py-3 text-left transition-colors ${
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-r-2 border-blue-700 dark:border-blue-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </button>
          );
        })}
      </nav>
      {/* Logout button at the bottom */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <button
          onClick={() => {
            if (confirm('Are you sure you want to logout?')) {
              logout();
            }
          }}
          className="w-full flex items-center px-6 py-3 text-left rounded-lg transition-colors text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          <LogOut className="w-5 h-5 mr-3" />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;