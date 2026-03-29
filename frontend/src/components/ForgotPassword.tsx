import { useState, useRef } from 'react';
import type { FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { Moon, Sun, Loader2, AlertCircle, BadgeCheck, ArrowLeft, AtSign, KeyRound, Languages, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import i18n from '../i18n';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ForgotPassword = () => {
  const [step, setStep] = useState<'email' | 'code' | 'success'>('email');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const codeInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleCodeChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return;
    const newCode = [...verificationCode];
    newCode[index] = value;
    setVerificationCode(newCode);
    if (value && index < 5) codeInputRefs.current[index + 1]?.focus();
  };

  const handleCodeKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !verificationCode[index] && index > 0) codeInputRefs.current[index - 1]?.focus();
  };

  const handleCodePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...verificationCode];
    for (let i = 0; i < pasteData.length; i++) newCode[i] = pasteData[i];
    setVerificationCode(newCode);
    const nextEmptyIndex = newCode.findIndex(digit => !digit);
    codeInputRefs.current[nextEmptyIndex === -1 ? 5 : Math.min(nextEmptyIndex, 5)]?.focus();
  };

  const handleRequestCode = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/forgot-password`, { email });
      setStep('code');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при отправке кода');
    } finally { setLoading(false); }
  };

  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    const code = verificationCode.join('');
    if (code.length !== 6) { setError('Введите 6-значный код'); return; }
    if (newPassword !== confirmPassword) { setError('Пароли не совпадают'); return; }
    if (newPassword.length < 6) { setError('Пароль должен содержать минимум 6 символов'); return; }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/reset-password`, { email, code, new_password: newPassword });
      setStep('success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Неверный или истёкший код');
    } finally { setLoading(false); }
  };

  const handleResendCode = async () => {
    setVerificationCode(['', '', '', '', '', '']);
    setError('');
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/forgot-password`, { email });
      setTimeout(() => codeInputRefs.current[0]?.focus(), 100);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при повторной отправке');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0" style={{ background: 'var(--bg)' }} />
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div style={{ position: 'absolute', width: 500, height: 500, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.3, background: 'radial-gradient(circle, #bbf7d0, transparent 70%)', top: '-10%', left: '50%', animation: 'float 25s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.25, background: 'radial-gradient(circle, #d1fae5, transparent 70%)', bottom: '-5%', left: '-5%', animation: 'float 25s ease-in-out infinite', animationDelay: '-10s' }} />
      </div>

      {/* Top buttons */}
      <div className="absolute top-8 right-8 flex items-center gap-3 z-[200]">
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.25 }}
          whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
          onClick={() => { const ls = ['ru', 'en', 'kk']; i18n.changeLanguage(ls[(ls.indexOf(i18n.language) + 1) % ls.length]); }}
          style={{ backdropFilter: 'blur(24px) saturate(180%)', background: 'var(--card)', border: '1px solid var(--card-border)' }}
          className="group p-3 rounded-xl shadow-sm hover:shadow-md transition-all duration-300"
        >
          <div className="flex items-center gap-2">
            <Languages className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            <motion.span key={i18n.language} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', minWidth: 24, textAlign: 'center' }}>
              {i18n.language}
            </motion.span>
          </div>
        </motion.button>

        <motion.button
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}
          whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
          onClick={toggleTheme}
          style={{ backdropFilter: 'blur(24px) saturate(180%)', background: 'var(--card)', border: '1px solid var(--card-border)' }}
          className="p-3 rounded-xl shadow-sm hover:shadow-md transition-all duration-300"
        >
          <motion.div initial={false} animate={{ rotate: theme === 'dark' ? 180 : 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
            {theme === 'dark' ? <Sun className="w-5 h-5" style={{ color: 'var(--text-muted)' }} /> : <Moon className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />}
          </motion.div>
        </motion.button>
      </div>

      {/* Main Card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <div style={{
          backdropFilter: 'blur(40px) saturate(200%)',
          background: 'var(--card)',
          border: '1px solid var(--card-border)',
          borderRadius: 20,
          boxShadow: '0 16px 64px var(--shadow-strong), 0 1px 0 rgba(255,255,255,0.1) inset',
          padding: '36px 36px',
          position: 'relative',
        }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)', borderRadius: '20px 20px 0 0' }} />

          {/* Back to Login */}
          <Link to="/login" className="inline-flex items-center gap-2 group" style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24, display: 'inline-flex', transition: 'color 0.2s' }}>
            <ArrowLeft style={{ width: 16, height: 16, transition: 'transform 0.2s' }} className="group-hover:-translate-x-1" />
            {t('forgotPassword.backToLogin', 'Назад к входу')}
          </Link>

          <AnimatePresence mode="wait">
            {step === 'email' && (
              <motion.div key="email-step" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                <div className="text-center mb-8">
                  <motion.div whileHover={{ scale: 1.08, rotate: 3 }} style={{ width: 64, height: 64, borderRadius: 18, background: 'linear-gradient(135deg, var(--accent), #4285f4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--accent-glow)', margin: '0 auto 20px' }}>
                    <KeyRound className="w-8 h-8 text-white" />
                  </motion.div>
                  <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text)', marginBottom: 8, letterSpacing: '-0.03em' }}>
                    {t('forgotPassword.title', 'Сброс пароля')}
                  </h1>
                  <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>
                    {t('forgotPassword.subtitle', 'Введите email для получения кода')}
                  </p>
                </div>

                <AnimatePresence>
                  {error && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                      style={{ marginBottom: 16, padding: 14, borderRadius: 14, background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.2)', display: 'flex', alignItems: 'flex-start', gap: 10, backdropFilter: 'blur(8px)' }}>
                      <AlertCircle style={{ width: 16, height: 16, color: 'var(--danger)', flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 12, color: 'var(--danger)' }}>{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <form onSubmit={handleRequestCode} className="space-y-4">
                  <div>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>Email</label>
                    <div className="relative">
                      <AtSign style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 18, height: 18, color: 'var(--text-faint)' }} />
                      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                        className="glass-input" style={{ width: '100%', paddingLeft: 42, paddingTop: 14, paddingBottom: 14 }}
                        placeholder="example@mail.com" disabled={loading} required autoFocus />
                    </div>
                  </div>
                  <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} type="submit" disabled={loading || !email}
                    className="btn-gradient" style={{ width: '100%', padding: '14px 24px', justifyContent: 'center' }}>
                    <span className="flex items-center gap-2">
                      {loading ? (<><Loader2 className="w-5 h-5 animate-spin" />{t('forgotPassword.sending', 'Отправка...')}</>) :
                        (<><AtSign className="w-5 h-5" />{t('forgotPassword.getCode', 'Получить код')}</>)}
                    </span>
                  </motion.button>
                </form>
              </motion.div>
            )}

            {step === 'code' && (
              <motion.div key="code-step" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                <div className="text-center mb-6">
                  <motion.div whileHover={{ scale: 1.08 }} style={{ width: 64, height: 64, borderRadius: 18, background: 'linear-gradient(135deg, var(--accent), #4285f4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--accent-glow)', margin: '0 auto 20px' }}>
                    <AtSign className="w-8 h-8 text-white" />
                  </motion.div>
                  <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text)', marginBottom: 8, letterSpacing: '-0.03em' }}>
                    {t('forgotPassword.verifyTitle', 'Подтверждение Email')}
                  </h1>
                  <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>
                    {t('forgotPassword.codeSent', 'Код подтверждения отправлен на')}
                  </p>
                  <p style={{ fontSize: 14, color: 'var(--accent)', marginTop: 4, fontWeight: 600 }}>{email}</p>
                </div>

                <AnimatePresence>
                  {error && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                      style={{ marginBottom: 16, padding: 14, borderRadius: 14, background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.2)', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                      <AlertCircle style={{ width: 16, height: 16, color: 'var(--danger)', flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 12, color: 'var(--danger)' }}>{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <form onSubmit={handleResetPassword} className="space-y-4">
                  <div>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 12, textAlign: 'center' }}>
                      {t('forgotPassword.verificationCode', 'Код подтверждения')}
                    </label>
                    <div className="flex justify-center gap-2 mb-4">
                      {[0, 1, 2, 3, 4, 5].map((index) => (
                        <input key={index} ref={(el) => (codeInputRefs.current[index] = el)}
                          type="text" inputMode="numeric" maxLength={1} autoComplete="one-time-code"
                          value={verificationCode[index]}
                          onChange={(e) => handleCodeChange(index, e.target.value)}
                          onKeyDown={(e) => handleCodeKeyDown(index, e)}
                          onPaste={index === 0 ? handleCodePaste : undefined}
                          disabled={loading}
                          className="glass-input"
                          style={{ width: 44, height: 48, textAlign: 'center', fontSize: 20, fontWeight: 600, padding: 0, caretColor: 'transparent' }}
                        />
                      ))}
                    </div>
                  </div>

                  {[
                    { label: t('forgotPassword.newPassword', 'Новый пароль'), value: newPassword, set: setNewPassword, show: showPassword, toggle: () => setShowPassword(!showPassword), ph: t('forgotPassword.passwordPlaceholder', 'Минимум 6 символов') },
                    { label: t('forgotPassword.confirmPassword', 'Подтвердите пароль'), value: confirmPassword, set: setConfirmPassword, show: showConfirmPassword, toggle: () => setShowConfirmPassword(!showConfirmPassword), ph: t('forgotPassword.confirmPlaceholder', 'Повторите пароль') },
                  ].map((f) => (
                    <div key={f.label}>
                      <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>{f.label}</label>
                      <div className="relative">
                        <KeyRound style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 18, height: 18, color: 'var(--text-faint)' }} />
                        <input type={f.show ? 'text' : 'password'} value={f.value} onChange={(e) => f.set(e.target.value)}
                          className="glass-input" style={{ width: '100%', paddingLeft: 42, paddingRight: 42, paddingTop: 14, paddingBottom: 14 }}
                          placeholder={f.ph} disabled={loading} required />
                        <button type="button" onClick={f.toggle} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-faint)', transition: 'color 0.2s', background: 'none', border: 'none', cursor: 'pointer' }}>
                          {f.show ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                      </div>
                    </div>
                  ))}

                  <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} type="submit"
                    disabled={loading || verificationCode.some(d => !d) || !newPassword || newPassword !== confirmPassword}
                    className="btn-gradient" style={{ width: '100%', padding: '14px 24px', justifyContent: 'center' }}>
                    <span className="flex items-center gap-2">
                      {loading ? (<><Loader2 className="w-5 h-5 animate-spin" />{t('forgotPassword.saving', 'Сохранение...')}</>) :
                        (<><KeyRound className="w-5 h-5" />{t('forgotPassword.changePassword', 'Сменить пароль')}</>)}
                    </span>
                  </motion.button>

                  <button type="button" onClick={handleResendCode} disabled={loading}
                    style={{ width: '100%', padding: '8px 0', fontSize: 13, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500, opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>
                    {t('forgotPassword.resendCode', 'Отправить код повторно')}
                  </button>
                </form>
              </motion.div>
            )}

            {step === 'success' && (
              <motion.div key="success-step" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }} className="text-center py-8">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
                  style={{ width: 72, height: 72, margin: '0 auto 24px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--success), #1557b0)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px rgba(26,115,232,0.3)' }}>
                  <BadgeCheck className="w-9 h-9 text-white" />
                </motion.div>
                <h1 style={{ fontSize: 24, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
                  {t('forgotPassword.successTitle', 'Пароль изменён!')}
                </h1>
                <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 32 }}>
                  {t('forgotPassword.successMessage', 'Теперь вы можете войти с новым паролем')}
                </p>
                <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} onClick={() => navigate('/login')}
                  style={{ width: '100%', padding: '14px 24px', borderRadius: 12, background: 'linear-gradient(135deg, var(--success), #1557b0)', color: 'white', border: 'none', fontWeight: 600, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit', boxShadow: '0 4px 16px rgba(26,115,232,0.3)', transition: 'all 0.25s' }}>
                  <span className="flex items-center gap-2 justify-center">
                    {t('forgotPassword.goToLogin', 'Войти в систему')}
                  </span>
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};
