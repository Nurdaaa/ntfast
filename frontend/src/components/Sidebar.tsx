import { useState } from 'react';
import { LayoutDashboard, ScanSearch, LogOut, Moon, Sun, ChevronDown, SlidersHorizontal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNavigate, useLocation } from 'react-router-dom';
import LanguageSwitcher from './LanguageSwitcher';

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const { t } = useTranslation();

  const menuItems = [
    { icon: LayoutDashboard, label: t('sidebar.dashboard'), path: '/' },
    { icon: ScanSearch, label: t('sidebar.analyses'), path: '/analyses' },
  ];

  return (
    <aside className="w-64 h-screen backdrop-blur-xl bg-white/80 dark:bg-gray-900/80 border-r border-gray-200/50 dark:border-gray-800/50 flex flex-col transition-colors duration-300 shadow-xl">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="px-5 py-6 border-b border-gray-200/50 dark:border-gray-800/50">
          <div className="cursor-default">
            <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-blue-600 via-blue-500 to-blue-700 dark:from-blue-400 dark:via-blue-300 dark:to-blue-500 bg-clip-text text-transparent leading-none">
              ntFAST
            </h1>
            <p className="text-[10px] font-semibold text-indigo-400/70 dark:text-indigo-500/70 uppercase tracking-widest mt-1">AI v2.0</p>
            <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-2 leading-relaxed">
              Financial Analysis System<br />for Transactions
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`
                  group relative w-full flex items-center space-x-3 px-4 py-3 rounded-xl
                  transition-all duration-300 ease-in-out
                  ${isActive
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/30'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50'
                  }
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl"
                    transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                  />
                )}
                <Icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-white' : ''}`} />
                <span className={`relative z-10 font-medium text-sm ${isActive ? 'text-white' : ''}`}>
                  {item.label}
                </span>
                {isActive && (
                  <span className="absolute right-2 w-2 h-2 bg-white rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Theme & Language Toggle */}
        <div className="p-4 border-t border-gray-200/50 dark:border-gray-800/50 space-y-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="relative group w-full flex items-center justify-between px-4 py-3 rounded-xl bg-white/80 dark:bg-gray-900/80 border border-gray-200/50 dark:border-gray-800/50 hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-colors duration-300 shadow-lg"
          >
            <div className="flex items-center space-x-3">
              {theme === 'dark' ? (
                <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300" />
              ) : (
                <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300" />
              )}
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
                {t('settings.darkMode')}
              </span>
            </div>
            <div className={`relative w-11 h-6 rounded-full transition-colors duration-300 ${theme === 'dark' ? 'bg-blue-600' : 'bg-gray-300'}`}>
              <div
                className="w-5 h-5 bg-white rounded-full shadow-md mt-0.5 transition-transform duration-300"
                style={{ transform: `translateX(${theme === 'dark' ? 20 : 2}px)` }}
              />
            </div>
          </button>

          {/* Language Switcher */}
          <LanguageSwitcher />
        </div>

        {/* User Profile Card */}
        <div className="p-4 border-t border-gray-200/50 dark:border-gray-800/50">
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="group w-full flex items-center space-x-3 p-3 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-800/30 hover:shadow-lg transition-shadow duration-300 border border-gray-200/50 dark:border-gray-700/50"
            >
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <span className="text-white font-semibold text-sm">
                    {user?.full_name?.charAt(0) || 'T'}
                  </span>
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-900" />
              </div>
              <div className="flex-1 text-left min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {user?.full_name || t('common.user')}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.role === 'admin' ? t('sidebar.administrator') : user?.role === 'analyst' ? t('userManagement.analyst') : t('userManagement.viewer')}
                </p>
              </div>
              <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-300 ${userMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            <AnimatePresence>
              {userMenuOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="absolute bottom-full left-0 right-0 mb-2 bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden"
                >
                  <div className="p-2 space-y-1">
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        navigate('/settings');
                      }}
                      className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors duration-200"
                    >
                      <SlidersHorizontal className="w-4 h-4" />
                      <span>{t('sidebar.settings')}</span>
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-200"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>{t('sidebar.logout')}</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </aside>
  );
};
