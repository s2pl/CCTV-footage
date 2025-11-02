import React, { useState, useEffect } from 'react';
import { X, Save, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useCCTV } from '../../hooks/useCCTV';
import { useToast } from '../Common/ToastContainer';
import { Camera, CameraRegistration } from '../../services/types';

interface CameraFormProps {
  camera?: Camera | null;
  onClose: () => void;
}

const CameraForm: React.FC<CameraFormProps> = ({ camera, onClose }) => {
  const { createCamera, updateCamera } = useCCTV();
  const { showSuccess, showError } = useToast();
  const [formData, setFormData] = useState<CameraRegistration>({
    name: '',
    description: '',
    ip_address: '',
    port: undefined,
    username: '',
    password: '',
    rtsp_url: '',
    rtsp_url_sub: '',
    rtsp_path: '',
    camera_type: 'rtsp',
    location: '',
    auto_record: false,
    record_quality: 'medium',
    max_recording_hours: 24,
    is_public: false,
    start_recording: false
  });
  const [isFormReady, setIsFormReady] = useState(false);
  const [cameraId, setCameraId] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (camera && camera.id && camera.id !== cameraId) {
      console.log('Editing camera data:', camera);
      console.log('Camera fields available:', Object.keys(camera));
      
      const newFormData = {
        name: camera.name || '',
        description: camera.description || '',
        ip_address: camera.ip_address || '',
        port: camera.port,
        username: camera.username || '',
        password: camera.password || '',
        rtsp_url: camera.rtsp_url || '',
        rtsp_url_sub: camera.rtsp_url_sub || '',
        rtsp_path: camera.rtsp_path || '',
        camera_type: camera.camera_type || 'rtsp',
        location: camera.location || '',
        auto_record: camera.auto_record || false,
        record_quality: camera.record_quality || 'medium',
        max_recording_hours: camera.max_recording_hours || 24,
        is_public: camera.is_public || false,
        start_recording: false
        
      };
      
      setFormData(newFormData);
      setCameraId(camera.id);
      console.log('Form data set for editing:', newFormData);
      setIsFormReady(true);
    } else if (!camera) {
      console.log('No camera data provided - creating new camera');
      // Reset form for new camera
      const newFormData = {
        name: '',
        description: '',
        ip_address: '',
        port: undefined,
        username: '',
        password: '',
        rtsp_url: '',
        rtsp_url_sub: '',
        rtsp_path: '',
        camera_type: 'rtsp',
        location: '',
        auto_record: false,
        record_quality: 'medium',
        max_recording_hours: 24,
        is_public: false,
        start_recording: false
      };
      
      setFormData(newFormData);
      setCameraId(null);
      setIsFormReady(true);
    }
  }, [camera, cameraId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent duplicate submissions
    if (isSubmitting) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Auto-generate RTSP URL from components
      const auth = formData.username ? `${formData.username}${formData.password ? ':' + formData.password : ''}@` : '';
      const port = formData.port || 554;
      const path = formData.rtsp_path || '/stream1';
      const generatedRtspUrl = `rtsp://${auth}${formData.ip_address}:${port}${path}`;
      
      const submissionData = {
        ...formData,
        rtsp_url: generatedRtspUrl
      };
      
      if (camera) {
        await updateCamera(camera.id, submissionData);
        showSuccess(
          'Camera Updated',
          `Camera "${formData.name}" has been updated successfully.`
        );
      } else {
        await createCamera(submissionData);
        showSuccess(
          'Camera Created',
          `Camera "${formData.name}" has been created successfully.`
        );
      }
      onClose();
    } catch (error) {
      console.error('Error saving camera:', error);
      showError(
        camera ? 'Update Failed' : 'Creation Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred while saving the camera.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };



  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : 
               type === 'number' ? (value ? parseInt(value) : undefined) : value
    }));
  };



  if (!isFormReady) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {camera ? 'Edit Camera' : 'Add New Camera'}
          </h1>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading camera data...</div>
        </div>
      </div>
    );
  }

  // Debug log to see current form values
  console.log('Current form values being rendered:', {
    name: formData.name,
    ip_address: formData.ip_address,
    location: formData.location,
    camera_type: formData.camera_type
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {camera ? 'Edit Camera' : 'Add New Camera'}
        </h1>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Camera Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="e.g., Main Entrance"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Location *
              </label>
              <input
                type="text"
                name="location"
                value={formData.location || ''}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="e.g., Building A - Front Door"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                required
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Description for this camera"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                IP Address *
              </label>
              <input
                type="text"
                name="ip_address"
                value={formData.ip_address || ''}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="192.168.1.100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Port (Optional)
              </label>
              <input
                type="number"
                name="port"
                value={formData.port || ''}
                onChange={handleChange}
                min="1"
                max="65535"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="554 (default)"
              />
            </div>



            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Custom RTSP Path (Optional)
              </label>
              <input
                type="text"
                name="rtsp_path"
                value={formData.rtsp_path || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="/live/0/SUB or /stream1"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Custom path after IP:port (e.g., /live/0/SUB, /stream1, /cam/realmonitor)
              </p>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sub Stream RTSP URL (Optional)
              </label>
              <input
                type="url"
                name="rtsp_url_sub"
                value={formData.rtsp_url_sub || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="rtsp://192.168.1.100/live/0/SUB"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Lower quality stream for bandwidth optimization (optional)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Username
              </label>
              <input
                type="text"
                name="username"
                value={formData.username || ''}
                onChange={handleChange}
                autoComplete="username"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Camera username (optional)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password || ''}
                  onChange={handleChange}
                  autoComplete="current-password"
                  className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Camera password (optional)"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Camera Type
              </label>
              <select
                name="camera_type"
                value={formData.camera_type || 'rtsp'}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="rtsp">RTSP Camera</option>
                <option value="ip">IP Camera</option>
                <option value="webcam">Webcam</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recording Quality
              </label>
              <select
                name="record_quality"
                value={formData.record_quality || 'medium'}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="high">High Quality</option>
                <option value="medium">Medium Quality</option>
                <option value="low">Low Quality</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Recording Hours
              </label>
              <input
                type="number"
                name="max_recording_hours"
                value={formData.max_recording_hours || 24}
                onChange={handleChange}
                min="1"
                max="8760"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="24 (default)"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Maximum hours to keep recordings (1-8760)
              </p>
            </div>

            <div className="md:col-span-2 space-y-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_public"
                  checked={formData.is_public || false}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Make camera publicly accessible to basic users
                </span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="auto_record"
                  checked={formData.auto_record || false}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable automatic recording
                </span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_online"
                  checked={formData.is_online || false}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <span className="text-sm font-medium text-gray-300">
                  Mark camera as online/active
                </span>
              </label>

              {!camera && (
                <>
    

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      name="start_recording"
                      checked={formData.start_recording || false}
                      onChange={handleChange}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Start test recording after creating camera
                    </span>
                  </label>
                </>
              )}
            </div>
          </div>



          <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">


            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{camera ? 'Updating...' : 'Creating...'}</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>{camera ? 'Update Camera' : 'Add Camera'}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CameraForm;