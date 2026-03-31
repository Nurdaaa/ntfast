import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { Moon, Sun, Loader2, AlertCircle, BadgeCheck, ArrowRight, UserRound, AtSign, KeyRound, UserRoundPlus, Languages, Eye, EyeOff } from 'lucide-react';
import i18n from '../i18n';
import { LogoIcon } from './ui/LogoIcon';
import { authAPI, emailVerificationAPI } from '../services/api';

export const Auth = () => {
  const location = useLocation();
  const [isRegisterMode, setIsRegisterMode] = useState(location.pathname === '/register');
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => { setIsRegisterMode(location.pathname === '/register'); }, [location.pathname]);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [registerError, setRegisterError] = useState('');
  const [registerSuccess, setRegisterSuccess] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);

  const [showVerification, setShowVerification] = useState(false);
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [verificationError, setVerificationError] = useState('');
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [verifyingCode, setVerifyingCode] = useState(false);
  const [codeSent, setCodeSent] = useState(false);

  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const codeInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleLoginSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      await login({ username: loginEmail, password: loginPassword });
      navigate('/');
    } catch (err: any) {
      setLoginError(err.response?.data?.detail || t('common.loginError'));
    } finally { setLoginLoading(false); }
  };

  const validateRegisterForm = () => {
    if (!firstName || !lastName || !registerEmail || !registerPassword || !confirmPassword) { setRegisterError(t('register.fillAllFields')); return false; }
    if (registerPassword !== confirmPassword) { setRegisterError(t('register.passwordMismatch')); return false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerEmail)) { setRegisterError('Invalid email format'); return false; }
    return true;
  };

  const sendVerificationCode = async () => {
    setSendingCode(true); setVerificationError('');
    try {
      await emailVerificationAPI.sendCode(registerEmail);
      setCodeSent(true); setVerificationError('');
    } catch (err: any) { setVerificationError(err.response?.data?.detail || 'Failed to send verification code'); }
    finally { setSendingCode(false); }
  };

  const handleVerifyCode = async (e: FormEvent) => {
    e.preventDefault(); setVerifyingCode(true); setVerificationError('');
    const code = verificationCode.join('');
    try {
      await emailVerificationAPI.verifyCode(registerEmail, code);
      await authAPI.completeRegistration({ email: registerEmail, password: registerPassword, full_name: `${firstName} ${lastName}` } as any);
      setVerificationSuccess(true);
      setTimeout(() => { setShowVerification(false); setVerificationSuccess(false); setIsRegisterMode(false); navigate('/login'); setFirstName(''); setLastName(''); setRegisterEmail(''); setRegisterPassword(''); setConfirmPassword(''); setVerificationCode(['','','','','','']); setCodeSent(false); }, 2000);
    } catch (err: any) { setVerificationError(err.response?.data?.detail || t('register.invalidCode')); }
    finally { setVerifyingCode(false); }
  };

  const handleCodeChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return;
    const newCode = [...verificationCode]; newCode[index] = value; setVerificationCode(newCode);
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
    codeInputRefs.current[newCode.findIndex(d => !d) === -1 ? 5 : Math.min(newCode.findIndex(d => !d), 5)]?.focus();
  };

  const handleRegisterSubmit = async (e: FormEvent) => {
    e.preventDefault(); setRegisterError(''); setRegisterSuccess(false);
    if (!validateRegisterForm()) return;
    setRegisterLoading(true);
    try {
      await authAPI.register({ email: registerEmail, password: registerPassword, full_name: `${firstName} ${lastName}` } as any);
      await sendVerificationCode();
      setShowVerification(true);
    } catch (err: any) { setRegisterError(err.response?.data?.detail || t('register.registrationError')); }
    finally { setRegisterLoading(false); }
  };

  /* ═══ Shared styles ═══ */
  const inputCls = "glass-input";
  const inputStyle = { width: '100%', paddingLeft: 38, paddingTop: 11, paddingBottom: 11, fontSize: 13 };
  const iconStyle = { position: 'absolute' as const, left: 12, top: '50%', transform: 'translateY(-50%)', width: 16, height: 16, color: 'var(--text-faint)' };
  const labelStyle = { display: 'block', fontSize: 11, fontWeight: 500 as const, color: 'var(--text-secondary)', marginBottom: 4 };

  const ErrorMsg = ({ msg }: { msg: string }) => (
    <AnimatePresence>
      {msg && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
          style={{ marginBottom: 12, padding: 10, borderRadius: 12, background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.15)', display: 'flex', alignItems: 'flex-start', gap: 8, backdropFilter: 'blur(8px)' }}>
          <AlertCircle style={{ width: 14, height: 14, color: 'var(--danger)', flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 12, color: 'var(--danger)' }}>{msg}</p>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const SuccessMsg = ({ msg, show }: { msg: string; show: boolean }) => (
    <AnimatePresence>
      {show && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
          style={{ marginBottom: 12, padding: 10, borderRadius: 12, background: 'var(--success-bg)', border: '1px solid rgba(26,115,232,0.15)', display: 'flex', alignItems: 'flex-start', gap: 8, backdropFilter: 'blur(8px)' }}>
          <BadgeCheck style={{ width: 14, height: 14, color: 'var(--success)', flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 12, color: 'var(--success)' }}>{msg}</p>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background with glass blobs */}
      <div className="absolute inset-0" style={{ background: 'var(--bg)' }} />
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div style={{ position: 'absolute', width: 600, height: 600, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.3, background: 'radial-gradient(circle, #b3d4fc, transparent 70%)', top: '-15%', left: '-5%', animation: 'float 25s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', width: 500, height: 500, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.25, background: 'radial-gradient(circle, #d4e4fc, transparent 70%)', bottom: '-10%', right: '-8%', animation: 'float 25s ease-in-out infinite', animationDelay: '-8s' }} />
        <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', filter: 'blur(100px)', opacity: 0.25, background: 'radial-gradient(circle, #a4c8f0, transparent 70%)', top: '40%', left: '55%', animation: 'float 25s ease-in-out infinite', animationDelay: '-4s' }} />
      </div>

      {/* Top buttons */}
      <div className="absolute top-8 right-8 flex items-center gap-3 z-[200]">
        <motion.button initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.25 }}
          whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
          onClick={() => { const ls = ['ru','en','kk']; i18n.changeLanguage(ls[(ls.indexOf(i18n.language)+1)%ls.length]); }}
          style={{ backdropFilter: 'blur(24px) saturate(180%)', background: 'var(--card)', border: '1px solid var(--card-border)' }}
          className="group p-3 rounded-xl shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex items-center gap-2">
            <Languages style={{ width: 18, height: 18, color: 'var(--accent)' }} />
            <motion.span key={i18n.language} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', minWidth: 24, textAlign: 'center' }}>{i18n.language}</motion.span>
          </div>
        </motion.button>

        <motion.button initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}
          whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
          onClick={toggleTheme}
          style={{ backdropFilter: 'blur(24px) saturate(180%)', background: 'var(--card)', border: '1px solid var(--card-border)' }}
          className="p-3 rounded-xl shadow-sm hover:shadow-md transition-all duration-300">
          <motion.div initial={false} animate={{ rotate: theme === 'dark' ? 180 : 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
            {theme === 'dark' ? <Sun style={{ width: 18, height: 18, color: 'var(--text-muted)' }} /> : <Moon style={{ width: 18, height: 18, color: 'var(--text-muted)' }} />}
          </motion.div>
        </motion.button>
      </div>

      {/* Main Container */}
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }} className="relative z-10 w-full max-w-5xl">
        <div className="relative">
          {/* Glow */}
          <div style={{ position: 'absolute', inset: -4, background: 'linear-gradient(135deg, var(--accent-glow), rgba(26,115,232,0.15), var(--accent-glow))', borderRadius: 28, filter: 'blur(20px)', opacity: 0.5, pointerEvents: 'none' }} />

          {/* Dual Slider */}
          <div className="relative overflow-hidden" style={{
            backdropFilter: 'blur(40px) saturate(200%)',
            background: 'var(--card)',
            border: '1px solid var(--card-border)',
            borderRadius: 24,
            boxShadow: '0 24px 80px var(--shadow-strong), 0 1px 0 rgba(255,255,255,0.08) inset',
            height: 650,
          }}>
            {/* Top glass shine */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)', zIndex: 60 }} />

            {/* ═══ LOGIN FORM ═══ */}
            <motion.div animate={{ x: isRegisterMode ? '-100%' : '0%' }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="absolute top-0 left-0 w-1/2 h-full z-10" style={{ pointerEvents: isRegisterMode ? 'none' : 'auto' }}>
              <div className="w-full h-full flex items-center justify-center p-12">
                <div className="w-full max-w-md">
                  <motion.div className="text-center mb-8">
                    <motion.div whileHover={{ scale: 1.08, rotate: 3 }} transition={{ duration: 0.3 }}
                      style={{ width: 60, height: 60, borderRadius: 16, background: 'linear-gradient(135deg, var(--accent), #4285f4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--accent-glow)', margin: '0 auto 16px' }}>
                      <LogoIcon height={28} color="white" />
                    </motion.div>
                    <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text)', marginBottom: 6, letterSpacing: '-0.03em' }}>{t('common.welcome')}</h1>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('common.loginPrompt')}</p>
                  </motion.div>

                  <ErrorMsg msg={loginError} />

                  <form onSubmit={handleLoginSubmit} className="space-y-3">
                    <div>
                      <label style={labelStyle}>Email</label>
                      <div className="relative">
                        <AtSign style={iconStyle} />
                        <input type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)} className={inputCls} style={inputStyle} placeholder="your@email.com" disabled={loginLoading} required />
                      </div>
                    </div>
                    <div>
                      <label style={labelStyle}>{t('common.password')}</label>
                      <div className="relative">
                        <KeyRound style={iconStyle} />
                        <input type={showLoginPassword ? 'text' : 'password'} value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                          className={inputCls} style={{ ...inputStyle, paddingRight: 38 }} placeholder={t('common.passwordHolder')} disabled={loginLoading} required />
                        <button type="button" onClick={() => setShowLoginPassword(!showLoginPassword)}
                          style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-faint)', background: 'none', border: 'none', cursor: 'pointer' }}>
                          {showLoginPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                        </button>
                      </div>
                    </div>
                    <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} type="submit" disabled={loginLoading}
                      className="btn-gradient" style={{ width: '100%', padding: '12px 24px', justifyContent: 'center', marginTop: 8 }}>
                      <span className="flex items-center gap-2" style={{ fontSize: 13 }}>
                        {loginLoading ? (<><Loader2 style={{ width: 16, height: 16, animation: 'spin 1s linear infinite' }} />{t('common.loggingIn')}</>) :
                          (<>{t('common.loginBtn')}<ArrowRight style={{ width: 16, height: 16 }} /></>)}
                      </span>
                    </motion.button>
                    <div className="text-center" style={{ marginTop: 12 }}>
                      <a href="/forgot-password" style={{ fontSize: 13, color: 'var(--text-muted)', transition: 'color 0.2s' }}>{t('login.forgotPassword', 'Забыли пароль?')}</a>
                    </div>
                  </form>
                </div>
              </div>
            </motion.div>

            {/* ═══ REGISTER FORM ═══ */}
            <motion.div animate={{ x: isRegisterMode ? '-100%' : '0%' }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="absolute top-0 left-full w-1/2 h-full z-10" style={{ pointerEvents: isRegisterMode ? 'auto' : 'none' }}>
              <div className="w-full h-full flex items-center justify-center p-12 overflow-y-auto">
                <div className="w-full max-w-md">
                  {!showVerification ? (
                    <>
                      <motion.div className="text-center mb-6">
                        <motion.div whileHover={{ scale: 1.08, rotate: -3 }} transition={{ duration: 0.3 }}
                          style={{ width: 60, height: 60, borderRadius: 16, background: 'linear-gradient(135deg, var(--accent), #4285f4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--accent-glow)', margin: '0 auto 16px' }}>
                          <UserRoundPlus style={{ width: 28, height: 28, color: 'white' }} />
                        </motion.div>
                        <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text)', marginBottom: 6, letterSpacing: '-0.03em' }}>{t('register.title')}</h1>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('register.subtitle')}</p>
                      </motion.div>

                      <SuccessMsg msg={t('register.registrationSuccess')} show={registerSuccess} />
                      <ErrorMsg msg={registerError} />

                      <form onSubmit={handleRegisterSubmit} className="space-y-2.5">
                        <div className="flex gap-2">
                          {[
                            { label: t('register.firstName'), value: firstName, set: setFirstName, ph: t('register.firstNamePlaceholder') },
                            { label: t('register.lastName'), value: lastName, set: setLastName, ph: t('register.lastNamePlaceholder') },
                          ].map(f => (
                            <div key={f.label} className="flex-1">
                              <label style={labelStyle}>{f.label}</label>
                              <div className="relative">
                                <UserRound style={iconStyle} />
                                <input type="text" value={f.value} onChange={e => f.set(e.target.value)} className={inputCls} style={inputStyle} placeholder={f.ph} disabled={registerLoading || registerSuccess} required />
                              </div>
                            </div>
                          ))}
                        </div>
                        <div>
                          <label style={labelStyle}>{t('register.email')}</label>
                          <div className="relative">
                            <AtSign style={iconStyle} />
                            <input type="email" value={registerEmail} onChange={e => setRegisterEmail(e.target.value)} className={inputCls} style={inputStyle} placeholder={t('register.emailPlaceholder')} disabled={registerLoading || registerSuccess} required />
                          </div>
                        </div>
                        <div>
                          <label style={labelStyle}>{t('register.password')}</label>
                          <div className="relative">
                            <KeyRound style={iconStyle} />
                            <input type={showRegisterPassword ? 'text' : 'password'} value={registerPassword} onChange={e => setRegisterPassword(e.target.value)}
                              className={inputCls} style={{ ...inputStyle, paddingRight: 38 }} placeholder={t('register.passwordPlaceholder')} disabled={registerLoading || registerSuccess} required />
                            <button type="button" onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                              style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-faint)', background: 'none', border: 'none', cursor: 'pointer' }}>
                              {showRegisterPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                            </button>
                          </div>
                        </div>
                        <div>
                          <label style={labelStyle}>{t('register.confirmPassword')}</label>
                          <div className="relative">
                            <KeyRound style={iconStyle} />
                            <input type={showConfirmPassword ? 'text' : 'password'} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                              className={inputCls} style={{ ...inputStyle, paddingRight: 38 }} placeholder={t('register.confirmPasswordPlaceholder')} disabled={registerLoading || registerSuccess} required />
                            <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                              style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-faint)', background: 'none', border: 'none', cursor: 'pointer' }}>
                              {showConfirmPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                            </button>
                          </div>
                        </div>
                        <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} type="submit" disabled={registerLoading || registerSuccess}
                          className="btn-gradient" style={{ width: '100%', padding: '12px 24px', justifyContent: 'center', marginTop: 8 }}>
                          <span className="flex items-center gap-2" style={{ fontSize: 13 }}>
                            {registerLoading ? (<><Loader2 style={{ width: 16, height: 16, animation: 'spin 1s linear infinite' }} />{t('register.registering')}</>) :
                              (<>{t('register.register')}<ArrowRight style={{ width: 16, height: 16 }} /></>)}
                          </span>
                        </motion.button>
                      </form>
                    </>
                  ) : (
                    <>
                      {/* Email Verification */}
                      <motion.div className="text-center mb-6">
                        <motion.div whileHover={{ scale: 1.08 }}
                          style={{ width: 60, height: 60, borderRadius: 16, background: 'linear-gradient(135deg, var(--accent), #4285f4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--accent-glow)', margin: '0 auto 16px' }}>
                          <AtSign style={{ width: 28, height: 28, color: 'white' }} />
                        </motion.div>
                        <h1 style={{ fontSize: 24, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>{t('register.verifyEmail')}</h1>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('register.codeSent')}</p>
                        <p style={{ fontSize: 13, color: 'var(--accent)', marginTop: 4, fontWeight: 600 }}>{registerEmail}</p>
                      </motion.div>

                      <SuccessMsg msg={t('register.codeVerified')} show={verificationSuccess} />
                      <ErrorMsg msg={verificationError} />
                      {codeSent && !verificationError && (
                        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                          style={{ marginBottom: 12, padding: 10, borderRadius: 12, background: 'var(--accent-subtle)', border: '1px solid rgba(26,115,232,0.15)', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                          <BadgeCheck style={{ width: 14, height: 14, color: 'var(--accent)', flexShrink: 0, marginTop: 1 }} />
                          <p style={{ fontSize: 12, color: 'var(--accent)' }}>{t('register.codeSent')}</p>
                        </motion.div>
                      )}

                      <form onSubmit={handleVerifyCode} className="space-y-4">
                        <div>
                          <label style={{ ...labelStyle, textAlign: 'center', marginBottom: 12 }}>{t('register.verificationCode')}</label>
                          <div className="flex justify-center gap-2 mb-4">
                            {[0,1,2,3,4,5].map(index => (
                              <input key={index} ref={el => (codeInputRefs.current[index] = el)}
                                type="text" inputMode="numeric" maxLength={1} autoComplete="one-time-code"
                                value={verificationCode[index]} onChange={e => handleCodeChange(index, e.target.value)}
                                onKeyDown={e => handleCodeKeyDown(index, e)} onPaste={index === 0 ? handleCodePaste : undefined}
                                disabled={verifyingCode || verificationSuccess}
                                className="glass-input" style={{ width: 44, height: 48, textAlign: 'center', fontSize: 20, fontWeight: 600, padding: 0, caretColor: 'transparent' }} />
                            ))}
                          </div>
                        </div>
                        <motion.button whileHover={{ scale: 1.02, y: -2 }} whileTap={{ scale: 0.98 }} type="submit"
                          disabled={verifyingCode || verificationSuccess || verificationCode.some(d => !d)}
                          className="btn-gradient" style={{ width: '100%', padding: '12px 24px', justifyContent: 'center' }}>
                          <span className="flex items-center gap-2" style={{ fontSize: 13 }}>
                            {verifyingCode ? (<><Loader2 style={{ width: 16, height: 16, animation: 'spin 1s linear infinite' }} />{t('register.verifying')}</>) :
                              (<>{t('register.verifyCode')}<BadgeCheck style={{ width: 16, height: 16 }} /></>)}
                          </span>
                        </motion.button>
                        <button type="button" onClick={sendVerificationCode} disabled={sendingCode || verificationSuccess}
                          style={{ width: '100%', padding: '8px 0', fontSize: 13, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500, opacity: sendingCode ? 0.5 : 1 }}>
                          {sendingCode ? t('register.sendingCode') : t('register.resendCode')}
                        </button>
                      </form>
                    </>
                  )}
                </div>
              </div>
            </motion.div>

            {/* ═══ OVERLAY PANEL ═══ */}
            <motion.div animate={{ x: isRegisterMode ? '-100%' : '0%' }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="absolute top-0 left-1/2 w-1/2 h-full z-50 overflow-hidden" style={{ borderRadius: 24 }}>
              <div className="relative h-full w-full" style={{ background: 'linear-gradient(135deg, #111111, #1a1a2e, #1557b0)', borderRadius: 24 }}>
                {/* Glass texture on overlay */}
                <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.15), transparent 60%)', pointerEvents: 'none' }} />

                <AnimatePresence>
                  {!isRegisterMode && (
                    <motion.div key="right-panel" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}
                      className="absolute inset-0 flex items-center justify-center p-12">
                      <div className="text-center text-white">
                        <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'center' }}>
                          <LogoIcon height={48} color="rgba(255,255,255,0.9)" />
                        </div>
                        <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16, letterSpacing: '-0.03em' }}>{t('register.helloFriend')}</h1>
                        <p style={{ color: 'rgba(255,255,255,0.85)', marginBottom: 32, maxWidth: 280, margin: '0 auto 32px', lineHeight: 1.6, fontSize: 14 }}>{t('register.helloFriendDesc')}</p>
                        <motion.button whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
                          onClick={() => { setIsRegisterMode(true); navigate('/register'); }}
                          style={{ padding: '12px 32px', borderRadius: 14, border: '2px solid rgba(255,255,255,0.5)', color: 'white', background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)', fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.3s' }}>
                          {t('login.switchToRegister')}
                        </motion.button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {isRegisterMode && (
                    <motion.div key="left-panel" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}
                      className="absolute inset-0 flex items-center justify-center p-12">
                      <div className="text-center text-white">
                        <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'center' }}>
                          <LogoIcon height={48} color="rgba(255,255,255,0.9)" />
                        </div>
                        <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16, letterSpacing: '-0.03em' }}>{t('login.welcomeBack')}</h1>
                        <p style={{ color: 'rgba(255,255,255,0.85)', marginBottom: 32, maxWidth: 280, margin: '0 auto 32px', lineHeight: 1.6, fontSize: 14 }}>{t('login.welcomeBackDesc')}</p>
                        <motion.button whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }}
                          onClick={() => { setIsRegisterMode(false); navigate('/login'); }}
                          style={{ padding: '12px 32px', borderRadius: 14, border: '2px solid rgba(255,255,255,0.5)', color: 'white', background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)', fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.3s' }}>
                          {t('register.switchToLogin')}
                        </motion.button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
