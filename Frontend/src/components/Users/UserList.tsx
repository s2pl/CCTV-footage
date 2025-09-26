import React, { useState } from 'react';
import { Plus, Edit, Trash2, UserCheck, UserX, Crown, RefreshCw } from 'lucide-react';
import { useUsers } from '../../hooks/useUsers';
import { useHierarchy } from '../../hooks/useHierarchy';
import { PermissionGuard } from '../Hierarchy/PermissionGuard';
import { User } from '../../services/userService';
import { USER_ROLES, UserRole } from '../../services/hierarchyTypes';
import UserForm from './UserForm';

const UserList: React.FC = () => {
  const { users, deleteUser, updateUser, fetchUsers, loading } = useUsers();
  const { 
    userRole, 
    canManageRole, 
    getRoleInfo 
  } = useHierarchy();
  
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  // Ensure users is an array before using array methods
  const usersArray = Array.isArray(users) ? users : [];

  // Filter users based on current user's permissions
  const filteredUsers = usersArray.filter(user => {
    if (!userRole || !user.role) return false;
    return canManageRole(user.role as UserRole);
  });

  const handleEdit = (user: User) => {
    // Check if user can manage this role
    if (!userRole || !user.role || !canManageRole(user.role as UserRole)) {
      alert('You do not have permission to edit this user.');
      return;
    }
    setEditingUser(user);
    setShowForm(true);
  };

  const handleDelete = (id: string, targetRole?: string) => {
    // Check if user can manage this role
    if (!userRole || !targetRole || !canManageRole(targetRole as UserRole)) {
      alert('You do not have permission to delete this user.');
      return;
    }
    
    if (confirm('Are you sure you want to delete this user?')) {
      deleteUser(id);
    }
  };

  const handleToggleActive = (id: string, active: boolean, targetRole?: string) => {
    // Check if user can manage this role
    if (!userRole || !targetRole || !canManageRole(targetRole as UserRole)) {
      alert('You do not have permission to modify this user.');
      return;
    }
    
    updateUser(id, { active: !active });
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingUser(null);
  };

  const handleRefresh = async () => {
    try {
      await fetchUsers();
    } catch (error) {
      console.error('Error refreshing users:', error);
    }
  };

  const getRoleIcon = (role: string) => {
    const roleInfo = getRoleInfo ? getRoleInfo(role as UserRole) : { icon: '👤' };
    return <span className="text-lg">{roleInfo.icon}</span>;
  };



  // Show loading state while data is being fetched
  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading users...</div>
        </div>
      </div>
    );
  }

  if (showForm) {
    return (
      <UserForm
        user={editingUser}
        onClose={handleCloseForm}
      />
    );
  }

  return (
    <div className="p-6">
      {/* Error Message */}
      {/* {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg">
          {error}
        </div>
      )} */}

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Users</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage user accounts and access permissions
          </p>
          {/* Show current user's role and permissions */}
          {/* {userRole && (
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm text-gray-500">Your role:</span>
              <span className={`px-2 py-1 text-xs rounded-full capitalize text-white`} style={getRoleStyle(userRole)}>
                {getRoleInfo(userRole).displayName}
              </span>
              <span className="text-sm text-gray-500">
                • Can create: {getCreatableRoles().map(r => getRoleInfo(r).displayName).join(', ') || 'None'}
              </span>
            </div>
          )} */}
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          {/* Only show Add User button if user can create users */}
          <PermissionGuard requiredFeature="user_management">
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add User</span>
            </button>
          </PermissionGuard>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Permissions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredUsers.map((user) => {
                const userRoleType = user.role as UserRole;
                const canManageThisUser = userRole && userRoleType && canManageRole(userRoleType);
                
                return (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {user.username}
                          {user.role === USER_ROLES.SUPERADMIN && (
                            <Crown className="inline w-4 h-4 ml-2 text-yellow-500" />
                          )}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {user.email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {getRoleIcon(user.role || 'user')}
                        <span 
                          className={`px-2 py-1 text-xs rounded-full capitalize text-white bg-blue-600`}
                          /* style={getRoleStyle(user.role || 'user')} */
                        >
                          {getRoleInfo ? getRoleInfo(userRoleType || USER_ROLES.VISITOR).displayName : (userRoleType || 'visitor')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {user.role === USER_ROLES.SUPERADMIN || user.role === USER_ROLES.ADMIN 
                        ? 'All features' 
                        : `${user.permissions?.length || 0} cameras`
                      }
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {user.active ? (
                          <UserCheck className="w-4 h-4 text-green-600" />
                        ) : (
                          <UserX className="w-4 h-4 text-red-600" />
                        )}
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user.active 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                        }`}>
                          {user.active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* View button - always visible */}
                        {/* <button
                          className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                          title="View user details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                         */}
                        {/* Edit button - only if can manage */}
                        {canManageThisUser && (
                          <button
                            onClick={() => handleEdit(user)}
                            className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                            title="Edit user"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                        
                        {/* Toggle status button - only if can manage */}
                        {canManageThisUser && (
                          <button
                            onClick={() => handleToggleActive(user.id, user.active || false, user.role)}
                            className={`p-1 transition-colors ${
                              user.active 
                                ? 'text-gray-400 hover:text-red-600' 
                                : 'text-gray-400 hover:text-green-600'
                            }`}
                            title={user.active ? 'Deactivate user' : 'Activate user'}
                          >
                            {user.active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                          </button>
                        )}
                        
                        {/* Delete button - only if can manage and not superadmin */}
                        {canManageThisUser && user.role !== USER_ROLES.SUPERADMIN && (
                          <button
                            onClick={() => handleDelete(user.id, user.role)}
                            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                            title="Delete user"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Show message if no users are visible due to permissions */}
        {filteredUsers.length === 0 && usersArray.length > 0 && (
          <div className="p-6 text-center text-gray-500">
            <p>You don't have permission to view any users with your current role.</p>
            <p className="text-sm mt-1">Contact an administrator to request additional permissions.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserList;