import { useState } from 'react';
import type { FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { Moon, Sun, Loader2, AlertCircle, Fingerprint, ArrowRight, AtSign, KeyRound } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ username: email, password });
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.loginError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background with blobs */}
      <div className="absolute inset-0" style={{ background: 'var(--bg)' }} />
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div style={{ position: 'absolute', width: 500, height: 500, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.3, background: 'radial-gradient(circle, #bbf7d0, transparent 70%)', top: '-10%', left: '-5%', animation: 'float 25s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.25, background: 'radial-gradient(circle, #d1fae5, transparent 70%)', bottom: '-5%', right: '-8%', animation: 'float 25s ease-in-out infinite', animationDelay: '-10s' }} />
        <div style={{ position: 'absolute', width: 350, height: 350, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.3, background: 'radial-gradient(circle, #a7f3d0, transparent 70%)', top: '50%', left: '60%', animation: 'float 25s ease-in-out infinite', animationDelay: '-5s' }} />
      </div>

      {/* Theme Toggle */}
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        whileHover={{ scale: 1.05, y: -2 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleTheme}
        style={{ backdropFilter: 'blur(24px) saturate(180%)', background: 'var(--card)', border: '1px solid var(--card-border)' }}
        className="absolute top-8 right-8 p-3 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 z-20"
      >
        <motion.div
          initial={false}
          animate={{ rotate: theme === 'dark' ? 180 : 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
          ) : (
            <Moon className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
          )}
        </motion.div>
      </motion.button>

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="relative" style={{
          backdropFilter: 'blur(40px) saturate(200%)',
          background: 'var(--card)',
          border: '1px solid var(--card-border)',
          borderRadius: 20,
          boxShadow: '0 16px 64px var(--shadow-strong), 0 1px 0 rgba(255,255,255,0.1) inset',
          padding: '40px 36px',
        }}>
          {/* Top glass shine */}
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)', borderRadius: '20px 20px 0 0' }} />

          {/* Logo */}
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-col items-center mb-10"
          >
            <motion.div
              whileHover={{ scale: 1.08, rotate: 3 }}
              transition={{ duration: 0.3 }}
              style={{
                width: 72,
                height: 72,
                borderRadius: 18,
                background: 'linear-gradient(135deg, var(--accent), #4285f4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 32px var(--accent-glow)',
                marginBottom: 24,
              }}
            >
              <Fingerprint className="w-9 h-9 text-white" />
            </motion.div>
            <h1 style={{ fontSize: 28, fontWeight: 600, color: 'var(--text)', marginBottom: 8, letterSpacing: '-0.03em' }}>
              {t('common.welcome')}
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>
              {t('common.loginPrompt')}
            </p>
          </motion.div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                style={{
                  marginBottom: 24,
                  padding: 14,
                  borderRadius: 14,
                  background: 'var(--danger-bg)',
                  border: '1px solid rgba(239,68,68,0.2)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                  backdropFilter: 'blur(8px)',
                }}
              >
                <AlertCircle style={{ width: 18, height: 18, color: 'var(--danger)', flexShrink: 0, marginTop: 1 }} />
                <p style={{ fontSize: 13, color: 'var(--danger)' }}>{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Email
              </label>
              <div className="relative">
                <AtSign style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 18, height: 18, color: 'var(--text-faint)' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="glass-input"
                  style={{ width: '100%', paddingLeft: 42, paddingTop: 14, paddingBottom: 14 }}
                  placeholder="example@mail.com"
                  disabled={loading}
                  required
                />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>
                {t('common.password')}
              </label>
              <div className="relative">
                <KeyRound style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 18, height: 18, color: 'var(--text-faint)' }} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="glass-input"
                  style={{ width: '100%', paddingLeft: 42, paddingTop: 14, paddingBottom: 14 }}
                  placeholder={t('common.passwordHolder')}
                  disabled={loading}
                  required
                />
              </div>
            </motion.div>

            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="btn-gradient"
              style={{ width: '100%', padding: '14px 24px', justifyContent: 'center', marginTop: 8 }}
            >
              <span className="flex items-center gap-2">
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    {t('common.loggingIn')}
                  </>
                ) : (
                  <>
                    {t('common.loginBtn')}
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </span>
            </motion.button>

            {/* Forgot Password Link */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.65 }}
              className="text-center"
            >
              <Link
                to="/forgot-password"
                style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-muted)', transition: 'color 0.2s' }}
                className="hover:!text-[var(--accent)]"
              >
                {t('login.forgotPassword', 'Забыли пароль?')}
              </Link>
            </motion.div>

            {/* Register Link */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="text-center pt-2"
            >
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                {t('login.noAccount')}{' '}
                <Link
                  to="/register"
                  style={{ fontWeight: 600, color: 'var(--accent)', transition: 'color 0.2s' }}
                >
                  {t('login.registerLink')}
                </Link>
              </p>
            </motion.div>
          </form>
        </div>
      </motion.div>
    </div>
  );
};
