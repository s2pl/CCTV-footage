import { useState, useEffect, Component, ReactNode } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import DashboardView from './components/Dashboard/DashboardView';
import CameraList from './components/Cameras/CameraList';
import LiveFeedView from './components/LiveFeed/LiveFeedView';
import HttpLiveFeedView from './components/LiveFeed/HttpLiveFeedView';
import UserList from './components/Users/UserList';
import AccessControlView from './components/AccessControl/AccessControlView';
import RecordingsView from './components/Recordings/RecordingsView';
import ScheduleView from './components/Schedule/ScheduleView';
import SettingsView from './components/Settings/SettingsView';
import ProfileView from './components/Profile/ProfileView';
import LoginView from './components/Auth/LoginView';

// Error Boundary for handling hot reload errors
class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.warn('Error boundary caught error during hot reload:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Reloading...</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

function AppContent() {
  const [activeView, setActiveView] = useState('dashboard');
  
  // Always call useAuth hook - let the AuthProvider handle errors
  const authContext = useAuth();
  const { isAuthenticated, isLoading, login } = authContext;

  // Debug authentication state changes
  useEffect(() => {
    console.log('Authentication state changed:', { isAuthenticated, isLoading });
  }, [isAuthenticated, isLoading]);

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <DashboardView onNavigate={setActiveView} />;
      case 'cameras': return <CameraList />;
      case 'live-feed': return <LiveFeedView isActivePage={true} />;
      case 'http-live-feed': return <HttpLiveFeedView isActivePage={true} />;
      case 'users': return <UserList />;
      case 'access-control': return <AccessControlView />;
      case 'recordings': return <RecordingsView />;
      case 'schedule': return <ScheduleView />;
      case 'settings': return <SettingsView />;
      case 'profile': return <ProfileView />;
      default: return <DashboardView onNavigate={setActiveView} />;
    }
  };

  const handleLogin = async (formData: { username?: string; email?: string; password: string }) => {
    // Prepare credentials for the auth context
    const credentials: { username?: string; email?: string; password: string } = {
      password: formData.password
    };
    
    if (formData.email) {
      credentials.email = formData.email;
    } else if (formData.username) {
      credentials.username = formData.username;
    }
    
    await login(credentials);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading...</p>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return (
      <ThemeProvider>
        <LoginView onLogin={handleLogin} />
      </ThemeProvider>
    );
  }

  // Show main app if authenticated
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex">
        {/* Sticky Sidebar */}
        <div className="sticky top-0 left-0 h-screen z-30">
          <Sidebar activeView={activeView} onViewChange={setActiveView} />
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Sticky Header */}
          <div className="sticky top-0 z-20">
            <Header onNavigate={setActiveView} />
          </div>
          
          {/* Scrollable Main Content */}
          <main className="flex-1 overflow-auto">
            {renderView()}
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;