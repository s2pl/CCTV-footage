import React, { useState, useEffect } from 'react';
import { X, Save, Calendar, Clock, Repeat, CheckCircle } from 'lucide-react';
import { RecordingSchedule, Camera as CameraType } from '../../services/types';

interface ScheduleFormProps {
  schedule?: RecordingSchedule | null;
  onClose: () => void;
  onSubmit: (schedule: Omit<RecordingSchedule, 'id' | 'created_at' | 'updated_at'>) => void;
  cameras: CameraType[];
}

const ScheduleForm: React.FC<ScheduleFormProps> = ({ schedule, onClose, onSubmit, cameras }) => {
  const [formData, setFormData] = useState({
    camera: '',
    name: '',
    schedule_type: 'continuous' as 'once' | 'daily' | 'weekly' | 'continuous',
    start_date: '',
    end_date: '',
    start_time: '00:00',
    end_time: '23:59',
    days_of_week: [] as string[],
    is_active: true
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (schedule) {
      setFormData({
        camera: schedule.camera,
        name: schedule.name,
        schedule_type: schedule.schedule_type,
        start_date: schedule.start_date || '',
        end_date: schedule.end_date || '',
        start_time: schedule.start_time,
        end_time: schedule.end_time,
        days_of_week: schedule.days_of_week || [],
        is_active: schedule.is_active
      });
    } else {
      // Set default dates
      const today = new Date();
      const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, today.getDate());
      setFormData(prev => ({
        ...prev,
        start_date: today.toISOString().split('T')[0],
        end_date: nextMonth.toISOString().split('T')[0]
      }));
    }
  }, [schedule]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.camera) {
      newErrors.camera = 'Camera is required';
    }
    if (!formData.name.trim()) {
      newErrors.name = 'Schedule name is required';
    }
    if (formData.schedule_type === 'once' && !formData.start_date) {
      newErrors.start_date = 'Start date is required for one-time schedules';
    }
    if (formData.schedule_type === 'once' && !formData.end_date) {
      newErrors.end_date = 'End date is required for one-time schedules';
    }
    if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
      newErrors.end_date = 'End date must be after start date';
    }
    if (formData.start_time >= formData.end_time) {
      newErrors.end_time = 'End time must be after start time';
    }
    if ((formData.schedule_type === 'weekly') && formData.days_of_week.length === 0) {
      newErrors.days_of_week = 'At least one day must be selected for weekly schedules';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const scheduleData = {
        ...formData,
        camera_name: cameras.find(cam => cam.id === formData.camera)?.name || ''
      };

      await onSubmit(scheduleData);
      setSuccess('Schedule saved successfully!');
      
      // Close form after a short delay to show success message
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch {
      // Error handling is done by the parent component
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleDayToggle = (dayName: string) => {
    setFormData(prev => ({
      ...prev,
      days_of_week: prev.days_of_week.includes(dayName)
        ? prev.days_of_week.filter(d => d !== dayName)
        : [...prev.days_of_week, dayName]
    }));
    
    if (errors.days_of_week) {
      setErrors(prev => ({ ...prev, days_of_week: '' }));
    }
  };

  const dayLabels = [
    { short: 'Sun', full: 'sunday' },
    { short: 'Mon', full: 'monday' },
    { short: 'Tue', full: 'tuesday' },
    { short: 'Wed', full: 'wednesday' },
    { short: 'Thu', full: 'thursday' },
    { short: 'Fri', full: 'friday' },
    { short: 'Sat', full: 'saturday' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {schedule ? 'Edit Schedule' : 'New Schedule'}
            </h3>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mx-6 mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-4 py-3 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Camera Selection */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Camera *
              </label>
              <select
                name="camera"
                value={formData.camera}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                  errors.camera ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
              >
                <option value="">Select a camera</option>
                {cameras.map(camera => (
                  <option key={camera.id} value={camera.id}>
                    {camera.name} - {camera.location}
                  </option>
                ))}
              </select>
              {errors.camera && (
                <p className="text-sm text-red-600 mt-1">{errors.camera}</p>
              )}
            </div>

            {/* Schedule Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Schedule Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                  errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="e.g., Daily Recording, Maintenance Window"
              />
              {errors.name && (
                <p className="text-sm text-red-600 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Schedule Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Schedule Type *
              </label>
              <select
                name="schedule_type"
                value={formData.schedule_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="continuous">Continuous Recording</option>
                <option value="once">One-time Schedule</option>
                <option value="daily">Daily Schedule</option>
                <option value="weekly">Weekly Schedule</option>
              </select>
            </div>

            {/* Active Status */}
            <div className="flex items-center space-x-2 mt-8">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Schedule is active
              </span>
            </div>
          </div>

          {/* Date Range */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2" />
              Date Range
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Date *
                </label>
                <input
                  type="date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.start_date ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                />
                {errors.start_date && (
                  <p className="text-sm text-red-600 mt-1">{errors.start_date}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  End Date *
                </label>
                <input
                  type="date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.end_date ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                />
                {errors.end_date && (
                  <p className="text-sm text-red-600 mt-1">{errors.end_date}</p>
                )}
              </div>
            </div>
          </div>

          {/* Time Range */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Time Range
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Time *
                </label>
                <input
                  type="time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  End Time *
                </label>
                <input
                  type="time"
                  name="end_time"
                  value={formData.end_time}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.end_time ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                />
                {errors.end_time && (
                  <p className="text-sm text-red-600 mt-1">{errors.end_time}</p>
                )}
              </div>
            </div>
          </div>

          {/* Days of Week */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <Repeat className="w-5 h-5 mr-2" />
              Days of Week
            </h4>
            <div className="grid grid-cols-7 gap-2">
              {dayLabels.map((day, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleDayToggle(day.full)}
                  className={`p-3 text-sm font-medium rounded-lg border transition-colors ${
                    formData.days_of_week.includes(day.full)
                      ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700'
                      : 'bg-gray-50 text-gray-700 border-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                >
                  {day.short}
                </button>
              ))}
            </div>
            {errors.days_of_week && (
              <p className="text-sm text-red-600 mt-2">{errors.days_of_week}</p>
            )}
          </div>



          {/* Form Actions */}
          <div className="flex gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Saving...' : (schedule ? 'Update Schedule' : 'Create Schedule')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScheduleForm;
