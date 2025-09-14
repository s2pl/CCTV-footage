import { useState, useCallback, useEffect } from 'react';
import userService, { User, UserCreateData, UserUpdateData } from '../services/userService';

export const useUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all users (admin only)
  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await userService.getUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new user
  const createUser = useCallback(async (userData: UserCreateData) => {
    try {
      setLoading(true);
      setError(null);
      const newUser = await userService.createUser(userData);
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
      console.error('Error creating user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update a user
  const updateUser = useCallback(async (userId: string, userData: UserUpdateData) => {
    try {
      setLoading(true);
      setError(null);
      const updatedUser = await userService.updateUser(userId, userData);
      setUsers(prev => prev.map(user => 
        user.id === userId ? updatedUser : user
      ));
      return updatedUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
      console.error('Error updating user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete a user
  const deleteUser = useCallback(async (userId: string) => {
    try {
      setLoading(true);
      setError(null);
      await userService.deleteUser(userId);
      setUsers(prev => prev.filter(user => user.id !== userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
      console.error('Error deleting user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Toggle user active status
  const toggleUserStatus = useCallback(async (userId: string, active: boolean) => {
    try {
      setLoading(true);
      setError(null);
      const updatedUser = await userService.updateUserActivation(userId, !active);
      setUsers(prev => prev.map(user => 
        user.id === userId ? updatedUser : user
      ));
      return updatedUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status');
      console.error('Error updating user status:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get user by ID
  const getUserById = useCallback((userId: string) => {
    return users.find(user => user.id === userId);
  }, [users]);

  // Get users by role
  const getUsersByRole = useCallback((role: string) => {
    return users.filter(user => user.role === role);
  }, [users]);

  // Get active users count
  const getActiveUsersCount = useCallback(() => {
    return users.filter(user => user.active).length;
  }, [users]);

  // Get total users count
  const getTotalUsersCount = useCallback(() => {
    return users.length;
  }, [users]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return {
    users,
    loading,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    toggleUserStatus,
    getUserById,
    getUsersByRole,
    getActiveUsersCount,
    getTotalUsersCount,
    clearError
  };
};
