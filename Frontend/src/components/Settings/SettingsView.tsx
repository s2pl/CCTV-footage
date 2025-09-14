import React, { useState, useEffect } from 'react';
import { Save, Shield, Bell, Database, Wifi, HardDrive, Eye } from 'lucide-react';

const SettingsView: React.FC = () => {
  const [settings, setSettings] = useState({
    // System Settings
    systemName: 'CCTV Portal',
    maxConcurrentStreams: 12,
    recordingRetentionDays: 30,
    autoBackup: true,
    backupFrequency: 'daily',
    backupTime: '02:00',
    
    // Security Settings
    sessionTimeout: 30,
    requireStrongPasswords: true,
    enableTwoFactor: false,
    maxFailedLogins: 5,
    passwordExpiryDays: 90,
    enableAuditLog: true,
    
    // Recording Settings
    defaultRecordingQuality: 'high',
    motionDetection: true,
    audioRecording: true,
    preRecordingBuffer: 5,
    postRecordingBuffer: 10,
    compressionLevel: 'medium',
    
    // Network Settings
    streamingPort: 8080,
    maxBandwidthPerStream: 10,
    enableSSL: true,
    enableHttps: true,
    maxConnections: 100,
    connectionTimeout: 30,
    
    // Notification Settings
    emailNotifications: true,
    systemAlerts: true,
    offlineAlerts: true,
    storageAlerts: true,
    motionAlerts: true,
    emailServer: 'smtp.gmail.com',
    emailPort: 587,
    emailUsername: '',
    emailPassword: '',
    
    // Display Settings
    defaultTheme: 'light',
    autoRefresh: true,
    refreshInterval: 30,
    showTimestamps: true,
    showCameraNames: true,
    gridLayout: '2x2'
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Load settings from localStorage or API
    const savedSettings = localStorage.getItem('cctv-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('Failed to parse saved settings:', error);
      }
    }
  }, []);

  const handleChange = (key: string, value: string | number | boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save settings to localStorage or API
      localStorage.setItem('cctv-settings', JSON.stringify(settings));
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setHasChanges(false);
      alert('Settings saved successfully!');
    } catch {
      alert('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to default values?')) {
      const defaultSettings = {
        systemName: 'CCTV Portal',
        maxConcurrentStreams: 12,
        recordingRetentionDays: 30,
        autoBackup: true,
        backupFrequency: 'daily',
        backupTime: '02:00',
        sessionTimeout: 30,
        requireStrongPasswords: true,
        enableTwoFactor: false,
        maxFailedLogins: 5,
        passwordExpiryDays: 90,
        enableAuditLog: true,
        defaultRecordingQuality: 'high',
        motionDetection: true,
        audioRecording: true,
        preRecordingBuffer: 5,
        postRecordingBuffer: 10,
        compressionLevel: 'medium',
        streamingPort: 8080,
        maxBandwidthPerStream: 10,
        enableSSL: true,
        enableHttps: true,
        maxConnections: 100,
        connectionTimeout: 30,
        emailNotifications: true,
        systemAlerts: true,
        offlineAlerts: true,
        storageAlerts: true,
        motionAlerts: true,
        emailServer: 'smtp.gmail.com',
        emailPort: 587,
        emailUsername: '',
        emailPassword: '',
        defaultTheme: 'light',
        autoRefresh: true,
        refreshInterval: 30,
        showTimestamps: true,
        showCameraNames: true,
        gridLayout: '2x2'
      };
      setSettings(defaultSettings);
      setHasChanges(true);
    }
  };

  const SettingGroup: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode }> = ({ title, icon, children }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center mb-4">
        {icon}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white ml-2">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );

  const SettingItem: React.FC<{ 
    label: string; 
    description?: string; 
    children: React.ReactNode;
  }> = ({ label, description, children }) => (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{description}</p>
        )}
      </div>
      <div className="ml-4">
        {children}
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Configure system preferences and security settings
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Reset to Default
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <SettingGroup 
          title="System Configuration" 
          icon={<Database className="w-5 h-5 text-blue-600" />}
        >
          <SettingItem label="System Name">
            <input
              type="text"
              value={settings.systemName}
              onChange={(e) => handleChange('systemName', e.target.value)}
              className="w-48 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>
          
          <SettingItem 
            label="Max Concurrent Streams"
            description="Maximum number of simultaneous video streams"
          >
            <input
              type="number"
              value={settings.maxConcurrentStreams}
              onChange={(e) => handleChange('maxConcurrentStreams', parseInt(e.target.value))}
              min="1"
              max="50"
              className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>
          
          <SettingItem 
            label="Recording Retention"
            description="Days to keep recorded footage"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.recordingRetentionDays}
                onChange={(e) => handleChange('recordingRetentionDays', parseInt(e.target.value))}
                min="1"
                max="365"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">days</span>
            </div>
          </SettingItem>
          
          <SettingItem label="Auto Backup">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoBackup}
                onChange={(e) => handleChange('autoBackup', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          {settings.autoBackup && (
            <>
              <SettingItem label="Backup Frequency">
                <select
                  value={settings.backupFrequency}
                  onChange={(e) => handleChange('backupFrequency', e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </SettingItem>
              
              <SettingItem label="Backup Time">
                <input
                  type="time"
                  value={settings.backupTime}
                  onChange={(e) => handleChange('backupTime', e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </SettingItem>
            </>
          )}
        </SettingGroup>

        <SettingGroup 
          title="Security Settings" 
          icon={<Shield className="w-5 h-5 text-red-600" />}
        >
          <SettingItem 
            label="Session Timeout"
            description="Minutes before automatic logout"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
                min="5"
                max="480"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">min</span>
            </div>
          </SettingItem>
          
          <SettingItem label="Require Strong Passwords">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.requireStrongPasswords}
                onChange={(e) => handleChange('requireStrongPasswords', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem label="Enable Two-Factor Authentication">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableTwoFactor}
                onChange={(e) => handleChange('enableTwoFactor', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem 
            label="Max Failed Login Attempts"
            description="Account lockout threshold"
          >
            <input
              type="number"
              value={settings.maxFailedLogins}
              onChange={(e) => handleChange('maxFailedLogins', parseInt(e.target.value))}
              min="3"
              max="10"
              className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>

          <SettingItem 
            label="Password Expiry Days"
            description="Days before password expires"
          >
            <input
              type="number"
              value={settings.passwordExpiryDays}
              onChange={(e) => handleChange('passwordExpiryDays', parseInt(e.target.value))}
              min="30"
              max="365"
              className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>

          <SettingItem label="Enable Audit Log">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableAuditLog}
                onChange={(e) => handleChange('enableAuditLog', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
        </SettingGroup>

        <SettingGroup 
          title="Recording Settings" 
          icon={<HardDrive className="w-5 h-5 text-green-600" />}
        >
          <SettingItem label="Default Recording Quality">
            <select
              value={settings.defaultRecordingQuality}
              onChange={(e) => handleChange('defaultRecordingQuality', e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="low">Low (720p)</option>
              <option value="medium">Medium (1080p)</option>
              <option value="high">High (4K)</option>
            </select>
          </SettingItem>
          
          <SettingItem label="Motion Detection">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.motionDetection}
                onChange={(e) => handleChange('motionDetection', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem label="Audio Recording">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.audioRecording}
                onChange={(e) => handleChange('audioRecording', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem 
            label="Pre-recording Buffer"
            description="Seconds to record before motion detection"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.preRecordingBuffer}
                onChange={(e) => handleChange('preRecordingBuffer', parseInt(e.target.value))}
                min="0"
                max="30"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
            </div>
          </SettingItem>

          <SettingItem 
            label="Post-recording Buffer"
            description="Seconds to record after motion detection"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.postRecordingBuffer}
                onChange={(e) => handleChange('postRecordingBuffer', parseInt(e.target.value))}
                min="5"
                max="60"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
            </div>
          </SettingItem>

          <SettingItem label="Compression Level">
            <select
              value={settings.compressionLevel}
              onChange={(e) => handleChange('compressionLevel', e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="low">Low (High Quality)</option>
              <option value="medium">Medium (Balanced)</option>
              <option value="high">High (Smaller Files)</option>
            </select>
          </SettingItem>
        </SettingGroup>

        <SettingGroup 
          title="Network Settings" 
          icon={<Wifi className="w-5 h-5 text-purple-600" />}
        >
          <SettingItem 
            label="Streaming Port"
            description="Port for video streaming service"
          >
            <input
              type="number"
              value={settings.streamingPort}
              onChange={(e) => handleChange('streamingPort', parseInt(e.target.value))}
              min="1024"
              max="65535"
              className="w-24 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>
          
          <SettingItem 
            label="Max Bandwidth Per Stream"
            description="Mbps limit per video stream"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.maxBandwidthPerStream}
                onChange={(e) => handleChange('maxBandwidthPerStream', parseInt(e.target.value))}
                min="1"
                max="100"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">Mbps</span>
            </div>
          </SettingItem>
          
          <SettingItem label="Enable SSL/TLS">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableSSL}
                onChange={(e) => handleChange('enableSSL', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem label="Enable HTTPS">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableHttps}
                onChange={(e) => handleChange('enableHttps', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem 
            label="Max Connections"
            description="Maximum concurrent connections"
          >
            <input
              type="number"
              value={settings.maxConnections}
              onChange={(e) => handleChange('maxConnections', parseInt(e.target.value))}
              min="10"
              max="1000"
              className="w-24 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </SettingItem>

          <SettingItem 
            label="Connection Timeout"
            description="Seconds before connection timeout"
          >
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={settings.connectionTimeout}
                onChange={(e) => handleChange('connectionTimeout', parseInt(e.target.value))}
                min="5"
                max="300"
                className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
            </div>
          </SettingItem>
        </SettingGroup>

        <SettingGroup 
          title="Display Settings" 
          icon={<Eye className="w-5 h-5 text-indigo-600" />}
        >
          <SettingItem label="Default Theme">
            <select
              value={settings.defaultTheme}
              onChange={(e) => handleChange('defaultTheme', e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </SettingItem>

          <SettingItem label="Auto Refresh">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoRefresh}
                onChange={(e) => handleChange('autoRefresh', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          {settings.autoRefresh && (
            <SettingItem 
              label="Refresh Interval"
              description="Seconds between auto-refresh"
            >
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  value={settings.refreshInterval}
                  onChange={(e) => handleChange('refreshInterval', parseInt(e.target.value))}
                  min="5"
                  max="300"
                  className="w-20 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
              </div>
            </SettingItem>
          )}

          <SettingItem label="Show Timestamps">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.showTimestamps}
                onChange={(e) => handleChange('showTimestamps', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem label="Show Camera Names">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.showCameraNames}
                onChange={(e) => handleChange('showCameraNames', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem label="Default Grid Layout">
            <select
              value={settings.gridLayout}
              onChange={(e) => handleChange('gridLayout', e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="1x1">1×1 (Single)</option>
              <option value="2x2">2×2 (Grid)</option>
              <option value="3x3">3×3 (Grid)</option>
              <option value="4x4">4×4 (Grid)</option>
            </select>
          </SettingItem>
        </SettingGroup>

        <SettingGroup 
          title="Notifications" 
          icon={<Bell className="w-5 h-5 text-yellow-600" />}
        >
          <SettingItem label="Email Notifications">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={(e) => handleChange('emailNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem label="System Alerts">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.systemAlerts}
                onChange={(e) => handleChange('systemAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem label="Camera Offline Alerts">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.offlineAlerts}
                onChange={(e) => handleChange('offlineAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>
          
          <SettingItem label="Storage Alerts">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.storageAlerts}
                onChange={(e) => handleChange('storageAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          <SettingItem label="Motion Detection Alerts">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.motionAlerts}
                onChange={(e) => handleChange('motionAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </SettingItem>

          {settings.emailNotifications && (
            <>
              <SettingItem label="SMTP Server">
                <input
                  type="text"
                  value={settings.emailServer}
                  onChange={(e) => handleChange('emailServer', e.target.value)}
                  className="w-48 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="smtp.gmail.com"
                />
              </SettingItem>
              
              <SettingItem label="SMTP Port">
                <input
                  type="number"
                  value={settings.emailPort}
                  onChange={(e) => handleChange('emailPort', parseInt(e.target.value))}
                  className="w-24 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </SettingItem>
              
              <SettingItem label="Email Username">
                <input
                  type="email"
                  value={settings.emailUsername}
                  onChange={(e) => handleChange('emailUsername', e.target.value)}
                  className="w-48 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="your-email@gmail.com"
                />
              </SettingItem>
              
              <SettingItem label="Email Password">
                <input
                  type="password"
                  value={settings.emailPassword}
                  onChange={(e) => handleChange('emailPassword', e.target.value)}
                  className="w-48 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="App password"
                />
              </SettingItem>
            </>
          )}
        </SettingGroup>
      </div>
    </div>
  );
};

export default SettingsView;