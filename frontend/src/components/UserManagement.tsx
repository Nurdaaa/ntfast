import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiUsers,
  FiSearch,
  FiRefreshCw,
  FiTrash2,
  FiUserCheck,
  FiChevronDown,
  FiCheck,
  FiWifi,
  FiClock,
  FiEye
} from 'react-icons/fi';
import { useActivity } from '../context/ActivityContext';
import { formatTimeAgo, formatExactTime } from '../hooks/useActivityMonitor';
import UserProfile from './UserProfile';
import { StatCardSkeleton, TableSkeleton } from './ui/Skeleton';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_online: boolean;
  created_at: string;
  last_login: string | null;
  last_activity: string | null;  // Last user activity timestamp (for monitoring)
  previous_login: string | null;  // SECURITY: Shows REAL last login (before current session)
  session_start: string | null;  // Current session start time
  total_online_time: number;  // Total time online in seconds
}

const UserManagement: React.FC = () => {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);
  const roleDropdownRef = useRef<HTMLDivElement>(null);
  const [openRoleDropdown, setOpenRoleDropdown] = useState<number | null>(null);
  const roleDropdownRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // WebSocket for real-time activity monitoring (global context from Layout)
  const { userStatuses, isConnected } = useActivity();

  // Stats
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_online).length,
    admins: users.filter(u => u.role === 'admin').length,
  };

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Error fetching current user:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/users/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // SECURITY: Preserve previous_login from localStorage for current user
      // This prevents previous_login from being overwritten with new values from backend
      const storedPreviousLogin = localStorage.getItem('previous_login');

      const usersData = response.data.map((user: User) => {
        // If this is current user and we have stored previous_login, use it
        if (currentUser && user.id === currentUser.id && storedPreviousLogin) {
          return {
            ...user,
            previous_login: storedPreviousLogin  // Override with localStorage value
          };
        }
        return user;
      });

      setUsers(usersData);
      setFilteredUsers(usersData);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
    fetchUsers();

    // Auto-refresh users list every 30 seconds
    const intervalId = setInterval(() => {
      fetchUsers();
    }, 30000); // 30 seconds

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Update time every second for real-time display
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000); // Update every second

    return () => clearInterval(timeInterval);
  }, []);

  // Merge WebSocket statuses with users
  // FIXED: Properly separate last_login (auth event) from last_activity (heartbeat)
  useEffect(() => {
    if (userStatuses.size > 0) {
      const storedPreviousLogin = localStorage.getItem('previous_login');

      setUsers(prevUsers => {
        return prevUsers.map(user => {
          const status = userStatuses.get(user.id);
          if (status) {
            const updatedUser = {
              ...user,
              is_online: status.is_online,
              // Only update last_login from WS if it was an actual login event
              last_login: status.last_login || user.last_login,
              // Always update last_activity from WS (heartbeat updates)
              last_activity: status.last_activity || user.last_activity,
            };

            // SECURITY: Preserve previous_login from localStorage for current user
            if (currentUser && user.id === currentUser.id && storedPreviousLogin) {
              updatedUser.previous_login = storedPreviousLogin;
            }

            return updatedUser;
          }
          return user;
        });
      });
    }
  }, [userStatuses, currentUser]);

  useEffect(() => {
    let filtered = users;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(user =>
        user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by role
    if (selectedRole) {
      filtered = filtered.filter(user => user.role === selectedRole);
    }

    setFilteredUsers(filtered);
  }, [searchTerm, selectedRole, users]);

  // Close filter dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (roleDropdownRef.current && !roleDropdownRef.current.contains(event.target as Node)) {
        setIsRoleDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close role change dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const clickedInside = Object.values(roleDropdownRefs.current).some(
        ref => ref && ref.contains(event.target as Node)
      );

      if (!clickedInside && openRoleDropdown !== null) {
        setOpenRoleDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [openRoleDropdown]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchUsers();
  };

  const handleChangeRole = async (userId: number, newRole: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.patch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/users/${userId}/role`,
        { role: newRole },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      fetchUsers();
      toast.success(t('userManagement.roleUpdateSuccess'));
    } catch (error) {
      console.error('Error updating role:', error);
      toast.error(t('userManagement.roleUpdateError'));
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm(t('userManagement.confirmDelete'))) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/users/${userId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      fetchUsers();
      toast.success(t('userManagement.deleteSuccess'));
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(t('userManagement.deleteError'));
    }
  };

  const handleViewProfile = (userId: number) => {
    setSelectedUserId(userId);
    setIsProfileOpen(true);
  };

  const handleCloseProfile = () => {
    setIsProfileOpen(false);
    setSelectedUserId(null);
  };

  // Use currentTime to trigger re-render every second
  const getTimeAgo = (lastLogin: string | null) => {
    return formatTimeAgo(lastLogin, t);
  };

  // Calculate session duration from session_start
  // SECURITY: Uses localStorage session_start to persist across page reloads
  const getSessionDuration = (sessionStart: string | null): string => {
    // PRIORITY: Use localStorage session_start (set ONLY on login)
    // This persists across page reloads and navigation
    const localSessionStart = localStorage.getItem('session_start');
    const effectiveSessionStart = localSessionStart || sessionStart;

    if (!effectiveSessionStart) return t('common.unknown');

    const start = new Date(effectiveSessionStart);
    const now = currentTime;
    const diffMs = now.getTime() - start.getTime();

    // Prevent negative durations (clock sync issues)
    if (diffMs < 0) return '0 сек';

    // Calculate total time components
    const totalSeconds = Math.floor(diffMs / 1000);
    const totalMinutes = Math.floor(totalSeconds / 60);
    const totalHours = Math.floor(totalMinutes / 60);
    const totalDays = Math.floor(totalHours / 24);

    // Calculate remaining components
    const remainingHours = totalHours % 24;
    const remainingMinutes = totalMinutes % 60;
    const remainingSeconds = totalSeconds % 60;

    // Format output based on duration
    if (totalDays > 0) {
      return `${totalDays} д ${remainingHours} ч ${remainingMinutes} мин`;
    } else if (totalHours > 0) {
      return `${totalHours} ч ${remainingMinutes} мин`;
    } else if (totalMinutes > 0) {
      return `${totalMinutes} мин`;
    } else {
      return `${remainingSeconds} сек`;
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-500/30';
      case 'analyst':
        return 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-500/30';
      case 'viewer':
        return 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-300 border-green-300 dark:border-green-500/30';
      default:
        return 'bg-gray-100 dark:bg-gray-500/20 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-500/30';
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Stats Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
        {/* Table Skeleton */}
        <div className="backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 rounded-xl overflow-hidden">
          <TableSkeleton rows={4} cols={6} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with Icon */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--accent)' }}>
            <FiUsers className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{t('userManagement.title')}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{t('userManagement.subtitle')}</p>
          </div>
        </div>

        {/* WebSocket Connection Status */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl backdrop-blur-xl border ${
            isConnected
              ? 'bg-green-50/50 dark:bg-green-900/20 border-green-200/50 dark:border-green-700/50'
              : 'bg-red-50/50 dark:bg-red-900/20 border-red-200/50 dark:border-red-700/50'
          } transition-all duration-300`}
        >
          <FiWifi className={`w-4 h-4 ${isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} />
          <span className={`text-sm font-medium ${isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {isConnected ? 'Real-time: ON' : 'Real-time: OFF'}
          </span>
        </motion.div>
      </div>

      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 p-6 hover:shadow-xl transition-all duration-300"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--accent)' }}>
              <FiUsers className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide mb-1">
                {t('userManagement.totalUsers')}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 p-6 hover:shadow-xl transition-all duration-300"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--success)' }}>
              <FiUserCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide mb-1">
                {t('userManagement.activeUsers')}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.active}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 p-6 hover:shadow-xl transition-all duration-300"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--accent)' }}>
              <FiUserCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide mb-1">
                {t('userManagement.administrators')}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.admins}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Search and Filter Bar */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <FiSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-5 h-5" />
            <input
              type="text"
              placeholder={t('userManagement.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-all duration-300 shadow-sm hover:shadow-md"
            />
          </div>

        {/* Custom Role Filter Dropdown */}
        <div className="relative min-w-[220px]" ref={roleDropdownRef}>
          <button
            onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
            className="w-full pl-12 pr-10 py-3 bg-white dark:bg-white/5 backdrop-blur-lg border border-gray-200 dark:border-white/10 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer hover:bg-gray-50 dark:hover:bg-white/10 transition-all duration-200 flex items-center justify-between shadow-lg"
          >
            <div className="flex items-center gap-3">
              <FiUsers className="text-gray-500 dark:text-gray-400" />
              <span className="text-sm font-medium">
                {selectedRole ? t(`userManagement.${selectedRole}`) : `${t('userManagement.role')}: All`}
              </span>
            </div>
            <motion.div
              animate={{ rotate: isRoleDropdownOpen ? 180 : 0 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              <FiChevronDown className="text-gray-500 dark:text-gray-400" />
            </motion.div>
          </button>

          {/* Dropdown Menu */}
          <AnimatePresence>
            {isRoleDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 backdrop-blur-xl border border-gray-200 dark:border-white/20 rounded-xl shadow-2xl overflow-hidden z-50"
              >
                {/* All Option */}
                <button
                  onClick={() => {
                    setSelectedRole(null);
                    setIsRoleDropdownOpen(false);
                  }}
                  className="w-full px-4 py-3 text-left text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors duration-150 flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    <FiUsers className="text-gray-500 dark:text-gray-400 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors" />
                    <span className="font-medium">{t('userManagement.role')}: All</span>
                  </div>
                  {selectedRole === null && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    >
                      <FiCheck className="text-blue-500 dark:text-blue-400" />
                    </motion.div>
                  )}
                </button>

                <div className="h-px bg-gray-200 dark:bg-white/10" />

                {/* Admin */}
                <button
                  onClick={() => {
                    setSelectedRole('admin');
                    setIsRoleDropdownOpen(false);
                  }}
                  className="w-full px-4 py-3 text-left text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors duration-150 flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-indigo-500 dark:bg-indigo-400"></div>
                    <span className="font-medium">{t('userManagement.admin')}</span>
                  </div>
                  {selectedRole === 'admin' && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    >
                      <FiCheck className="text-blue-500 dark:text-blue-400" />
                    </motion.div>
                  )}
                </button>

                <div className="h-px bg-gray-200 dark:bg-white/10" />

                {/* Analyst */}
                <button
                  onClick={() => {
                    setSelectedRole('analyst');
                    setIsRoleDropdownOpen(false);
                  }}
                  className="w-full px-4 py-3 text-left text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors duration-150 flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400"></div>
                    <span className="font-medium">{t('userManagement.analyst')}</span>
                  </div>
                  {selectedRole === 'analyst' && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    >
                      <FiCheck className="text-blue-500 dark:text-blue-400" />
                    </motion.div>
                  )}
                </button>

                <div className="h-px bg-gray-200 dark:bg-white/10" />

                {/* Viewer */}
                <button
                  onClick={() => {
                    setSelectedRole('viewer');
                    setIsRoleDropdownOpen(false);
                  }}
                  className="w-full px-4 py-3 text-left text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors duration-150 flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500 dark:bg-green-400"></div>
                    <span className="font-medium">{t('userManagement.viewer')}</span>
                  </div>
                  {selectedRole === 'viewer' && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    >
                      <FiCheck className="text-blue-500 dark:text-blue-400" />
                    </motion.div>
                  )}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

          <motion.button
            onClick={handleRefresh}
            disabled={refreshing}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            className="btn-gradient disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
          >
            <FiRefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {t('userManagement.refresh')}
          </motion.button>
        </div>
      </div>

      {/* Users Table */}
      <div className="relative">
        {/* Table Container */}
        <div className="relative backdrop-blur-xl bg-white/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.name')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.email')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.role')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.lastLogin')}
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.status')}
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {t('userManagement.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filteredUsers.map((user, index) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{user.full_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-700 dark:text-gray-300">{user.email}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="relative" ref={el => roleDropdownRefs.current[user.id] = el}>
                        <button
                          onClick={() => setOpenRoleDropdown(openRoleDropdown === user.id ? null : user.id)}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(user.role)} cursor-pointer hover:opacity-80 transition-opacity flex items-center gap-2`}
                        >
                          <span>{t(`userManagement.${user.role}`)}</span>
                          <motion.div
                            animate={{ rotate: openRoleDropdown === user.id ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <FiChevronDown className="w-3 h-3" />
                          </motion.div>
                        </button>

                        {/* Role Change Dropdown */}
                        <AnimatePresence>
                          {openRoleDropdown === user.id && (
                            <motion.div
                              initial={{ opacity: 0, y: -10, scale: 0.95 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              exit={{ opacity: 0, y: -10, scale: 0.95 }}
                              transition={{ duration: 0.15 }}
                              className="absolute left-0 mt-2 w-40 bg-white dark:bg-gray-800 backdrop-blur-xl border border-gray-200 dark:border-white/20 rounded-lg shadow-2xl overflow-hidden z-50"
                            >
                              {/* Admin */}
                              <button
                                onClick={() => {
                                  handleChangeRole(user.id, 'admin');
                                  setOpenRoleDropdown(null);
                                }}
                                className="w-full px-3 py-2 text-left text-xs text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors flex items-center gap-2"
                              >
                                <div className="w-2 h-2 rounded-full bg-indigo-500 dark:bg-indigo-400"></div>
                                <span>{t('userManagement.admin')}</span>
                                {user.role === 'admin' && <FiCheck className="ml-auto text-blue-500 dark:text-blue-400" />}
                              </button>

                              <div className="h-px bg-gray-200 dark:bg-white/10" />

                              {/* Analyst */}
                              <button
                                onClick={() => {
                                  handleChangeRole(user.id, 'analyst');
                                  setOpenRoleDropdown(null);
                                }}
                                className="w-full px-3 py-2 text-left text-xs text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors flex items-center gap-2"
                              >
                                <div className="w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400"></div>
                                <span>{t('userManagement.analyst')}</span>
                                {user.role === 'analyst' && <FiCheck className="ml-auto text-blue-500 dark:text-blue-400" />}
                              </button>

                              <div className="h-px bg-gray-200 dark:bg-white/10" />

                              {/* Viewer */}
                              <button
                                onClick={() => {
                                  handleChangeRole(user.id, 'viewer');
                                  setOpenRoleDropdown(null);
                                }}
                                className="w-full px-3 py-2 text-left text-xs text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors flex items-center gap-2"
                              >
                                <div className="w-2 h-2 rounded-full bg-green-500 dark:bg-green-400"></div>
                                <span>{t('userManagement.viewer')}</span>
                                {user.role === 'viewer' && <FiCheck className="ml-auto text-blue-500 dark:text-blue-400" />}
                              </button>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {currentUser && user.id === currentUser.id ? (
                        // Current user: Show session duration + previous login
                        <div className="space-y-1.5" title="Текущая сессия и предыдущий вход для мониторинга безопасности">
                          <div className="text-sm font-medium text-green-600 dark:text-green-400 flex items-center gap-2">
                            <FiClock className="w-3.5 h-3.5" />
                            Текущая сессия: {getSessionDuration(user.session_start)}
                          </div>
                          {(() => {
                            // SECURITY: ONLY use previous_login from localStorage
                            // NEVER fallback to backend value - localStorage is SINGLE source of truth
                            // This ensures the value is ABSOLUTELY FIXED during entire session
                            const storedPreviousLogin = localStorage.getItem('previous_login');

                            return storedPreviousLogin ? (
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Предыдущий вход: {formatExactTime(storedPreviousLogin)}
                              </div>
                            ) : (
                              <div className="text-xs text-gray-500 dark:text-gray-500 italic">
                                Первый вход в систему
                              </div>
                            );
                          })()}
                        </div>
                      ) : (
                        // Other users: Show last activity (real-time monitoring)
                        <div className="space-y-1" title={user.is_online ? "Последняя активность" : "Последний вход"}>
                          <div className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
                            <FiClock className="w-3.5 h-3.5 text-gray-400" />
                            {getTimeAgo(user.last_activity || user.last_login)}
                          </div>
                          {(user.last_activity || user.last_login) && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {formatExactTime(user.last_activity || user.last_login)}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${user.is_online ? 'bg-green-500 dark:bg-green-400' : 'bg-gray-400'}`} />
                        <span className={`text-sm ${user.is_online ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}>
                          {user.is_online ? t('userManagement.online') : t('userManagement.offline')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleViewProfile(user.id)}
                          className="p-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-500/10 rounded-lg transition-colors"
                          title={t('userManagement.viewProfile') || 'View Profile'}
                        >
                          <FiEye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="p-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-100 dark:hover:bg-red-500/10 rounded-lg transition-colors"
                          title={t('userManagement.delete')}
                        >
                          <FiTrash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-gray-600 dark:text-gray-400">
              {t('userManagement.noUsers')}
            </div>
          )}
          </div>
        </div>
      </div>

      {/* User Profile Modal */}
      {selectedUserId && (
        <UserProfile
          userId={selectedUserId}
          isOpen={isProfileOpen}
          onClose={handleCloseProfile}
        />
      )}
    </div>
  );
};

export default UserManagement;
