import React, { useState, useEffect } from 'react';
import { X, Save, Shield, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useUsers } from '../../hooks/useUsers';
import { useCCTV } from '../../hooks/useCCTV';
import { useToast } from '../Common/ToastContainer';
import { User as UserType, Permission } from '../../services/userService';
import { USER_ROLES, UserRole } from '../../services/hierarchyTypes';

interface UserUpdateData {
  username?: string;
  email?: string;
  password?: string;
  password_confirm?: string;
  role?: string;
  active?: boolean;
  permissions?: Permission[];
}

interface UserFormProps {
  user?: UserType | null;
  onClose: () => void;
}

const UserForm: React.FC<UserFormProps> = ({ user, onClose }) => {
  const { createUser, updateUser } = useUsers();
  const { cameras } = useCCTV();
  const { showSuccess, showError } = useToast();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    role: USER_ROLES.VISITOR as UserRole,
    active: true
  });
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '', // Keep password empty for updates
        password_confirm: '',
        role: (user.role as UserRole) || USER_ROLES.VISITOR,
        active: user.active || user.is_active || false
      });
      setPermissions(user.permissions || []);
    } else {
      // Initialize permissions for new user - handle cameras safely
      const camerasArray = Array.isArray(cameras) ? cameras : [];
      setPermissions(camerasArray.map(camera => ({
        cameraId: camera.id,
        canView: false,
        canControl: false,
        canRecord: false
      })));
    }
  }, [user, cameras]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent duplicate submissions
    if (isSubmitting) {
      return;
    }
    
    // Validate password confirmation for new users
    if (!user && formData.password !== formData.password_confirm) {
      showError('Validation Error', 'Passwords do not match');
      return;
    }

    setIsSubmitting(true);

    try {
      if (user) {
        // For updates - backend expects different structure
        const updateData: Partial<UserUpdateData> = {
          username: formData.username,
          role: formData.role,
          active: formData.active
        };
        
        // Include permissions for non-admin users
        if (formData.role !== 'admin' && formData.role !== 'superadmin') {
          updateData.permissions = permissions;
        }
        
        await updateUser(user.id, updateData);
        showSuccess(
          'User Updated',
          `User "${formData.username}" has been updated successfully.`
        );
      } else {
        // For new users, send all required data including password confirmation
        const createData = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          password_confirm: formData.password_confirm,
          role: formData.role,
          permissions: formData.role === USER_ROLES.ADMIN || formData.role === USER_ROLES.SUPERADMIN ? [] : permissions
        };
        await createUser(createData);
        showSuccess(
          'User Created',
          `User "${formData.username}" has been created successfully.`
        );
      }
      
      onClose();
    } catch (error) {
      console.error('Error saving user:', error);
      showError(
        user ? 'Update Failed' : 'Creation Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred while saving the user.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handlePermissionChange = (cameraId: string, permission: keyof Permission, value: boolean) => {
    setPermissions(prev => prev.map(p => 
      p.cameraId === cameraId 
        ? { ...p, [permission]: value }
        : p
    ));
  };

  const getCameraName = (cameraId: string) => {
    const camerasArray = Array.isArray(cameras) ? cameras : [];
    return camerasArray.find(cam => cam.id === cameraId)?.name || 'Unknown Camera';
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {user ? 'Edit User' : 'Add New User'}
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
                Username *
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter email address"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Password {!user && '*'}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required={!user}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={user ? "Leave blank to keep current password" : "Enter password"}
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
              {user && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Leave blank to keep current password.
                </p>
              )}
            </div>

            {!user && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Confirm Password *
                </label>
                <div className="relative">
                  <input
                    type={showPasswordConfirm ? "text" : "password"}
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Confirm password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {showPasswordConfirm ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Role *
              </label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={USER_ROLES.VISITOR}>Visitor</option>
                <option value={USER_ROLES.DEV}>Developer</option>
                <option value={USER_ROLES.ADMIN}>Administrator</option>
                <option value={USER_ROLES.SUPERADMIN}>Super Administrator</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Administrators and Super Administrators have access to all cameras and settings
              </p>
            </div>

            <div>
              <label className="flex items-center space-x-2 mt-8">
                <input
                  type="checkbox"
                  name="active"
                  checked={formData.active}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  User is active
                </span>
              </label>
            </div>
          </div>

          {formData.role !== USER_ROLES.ADMIN && formData.role !== USER_ROLES.SUPERADMIN && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Camera Permissions
              </h3>
              
              <div className="space-y-4">
                {permissions.map((permission) => (
                  <div key={permission.cameraId} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                      {getCameraName(permission.cameraId)}
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={permission.canView}
                          onChange={(e) => handlePermissionChange(permission.cameraId, 'canView', e.target.checked)}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">View</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={permission.canControl}
                          onChange={(e) => handlePermissionChange(permission.cameraId, 'canControl', e.target.checked)}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">Control</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={permission.canRecord}
                          onChange={(e) => handlePermissionChange(permission.cameraId, 'canRecord', e.target.checked)}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">Record</span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
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
                  <span>{user ? 'Updating...' : 'Creating...'}</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>{user ? 'Update User' : 'Create User'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserForm;