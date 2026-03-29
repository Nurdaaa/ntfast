import { useState, useRef, useEffect } from 'react';
import { Home, LayoutDashboard, ScanSearch, SlidersHorizontal, LogOut, Moon, Sun, Languages } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { LogoIcon } from './ui/LogoIcon';

const languages = [
  { code: 'ru', name: 'RU', flag: '🇷🇺' },
  { code: 'kk', name: 'KZ', flag: '🇰🇿' },
  { code: 'en', name: 'EN', flag: '🇬🇧' },
];

export const FloatingNav = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const langMenuRef = useRef<HTMLDivElement>(null);

  const menuItems = [
    { icon: Home, label: t('sidebar.home'), path: '/' },
    { icon: LayoutDashboard, label: t('sidebar.dashboard'), path: '/dashboard' },
    { icon: ScanSearch, label: t('sidebar.analyses'), path: '/analyses' },
  ];

  const currentLang = languages.find(l => l.code === language) || languages[0];

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) setUserMenuOpen(false);
      if (langMenuRef.current && !langMenuRef.current.contains(e.target as Node)) setLangMenuOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="floating-nav">
      {/* Brand */}
      <div className="nav-brand" onClick={() => navigate('/')} style={{ display: 'flex', alignItems: 'center', padding: '0 4px' }}>
        <LogoIcon height={16} color="var(--accent)" />
      </div>

      <div className="nav-divider" />

      {/* Nav items */}
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path);
        return (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`nav-item ${isActive ? 'active' : ''}`}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Icon style={{ width: 15, height: 15 }} />
              {item.label}
            </span>
          </button>
        );
      })}

      <div className="nav-divider" />

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="nav-item"
        title={t('settings.darkMode')}
      >
        {theme === 'dark' ? <Sun style={{ width: 15, height: 15 }} /> : <Moon style={{ width: 15, height: 15 }} />}
      </button>

      {/* Language switcher */}
      <div className="relative" ref={langMenuRef}>
        <button
          onClick={() => setLangMenuOpen(!langMenuOpen)}
          className="nav-item"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
        >
          <Languages style={{ width: 14, height: 14 }} />
          <span style={{ fontSize: 12 }}>{currentLang.name}</span>
        </button>
        <AnimatePresence>
          {langMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="nav-dropdown"
              style={{ right: 0, minWidth: 140 }}
            >
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => { setLanguage(lang.code); setLangMenuOpen(false); }}
                  className={`nav-dropdown-item ${language === lang.code ? 'active' : ''}`}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.name}</span>
                  {language === lang.code && (
                    <span className="nav-dropdown-dot" />
                  )}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="nav-divider" />

      {/* User avatar */}
      <div className="relative" ref={userMenuRef}>
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="nav-avatar"
          title={user?.full_name || t('common.user')}
        >
          {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
        </button>
        <AnimatePresence>
          {userMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="nav-dropdown"
              style={{ right: 0, minWidth: 200 }}
            >
              <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
                  {user?.full_name || t('common.user')}
                </p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {user?.email}
                </p>
              </div>
              <div style={{ padding: 6 }}>
                <button
                  onClick={() => { setUserMenuOpen(false); navigate('/settings'); }}
                  className="nav-dropdown-item"
                >
                  <SlidersHorizontal style={{ width: 14, height: 14 }} />
                  <span>{t('sidebar.settings')}</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="nav-dropdown-item danger"
                >
                  <LogOut style={{ width: 14, height: 14 }} />
                  <span>{t('sidebar.logout')}</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
};
