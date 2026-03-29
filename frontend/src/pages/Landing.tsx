import { useRef } from 'react';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowRight, Shield, BarChart4, ScanLine, FileSearch, Gauge,
  TrendingUp, Lock, FileText, RefreshCw,
  ChevronDown, Cpu, Globe,
} from 'lucide-react';
import { LogoIcon } from '../components/ui/LogoIcon';

/* ────────── animation presets ────────── */
const fadeUp = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0 } };
const scaleIn = { hidden: { opacity: 0, scale: 0.9 }, visible: { opacity: 1, scale: 1 } };

function Section({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.section
      ref={ref}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      variants={fadeUp}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   LANDING PAGE
   ═══════════════════════════════════════════════════════════════ */

export function Landing() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  return (
    <div style={{ background: 'var(--bg)', color: 'var(--text)', overflowX: 'hidden', marginTop: -90 }}>

      {/* ═══════════════════ HERO SECTION (~60vh) ═══════════════════ */}
      <div ref={heroRef} style={{ position: 'relative', minHeight: '100vh', background: '#0a0a0a', overflow: 'hidden' }}>
        {/* Gradient orbs */}
        <div style={{ position: 'absolute', width: 800, height: 800, borderRadius: '50%', background: 'radial-gradient(circle, rgba(26,115,232,0.15), transparent 70%)', top: '-20%', right: '-10%', filter: 'blur(80px)' }} />
        <div style={{ position: 'absolute', width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(21,87,176,0.10), transparent 70%)', bottom: '-10%', left: '-5%', filter: 'blur(80px)' }} />
        <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(66,133,244,0.08), transparent 70%)', top: '40%', left: '40%', filter: 'blur(60px)' }} />

        {/* Grid pattern overlay */}
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.03,
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        <motion.div style={{ y: heroY, opacity: heroOpacity }} className="relative z-10">
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '160px 40px 60px', textAlign: 'center' }}>

            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                padding: '6px 16px 6px 8px', borderRadius: 50,
                background: 'rgba(26,115,232,0.1)', border: '1px solid rgba(26,115,232,0.2)',
                marginBottom: 32,
              }}
            >
              <span style={{ background: '#1a73e8', borderRadius: '50%', width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Cpu style={{ width: 11, height: 11, color: 'white' }} />
              </span>
              <span style={{ fontSize: 13, color: '#4285f4', fontWeight: 600 }}>{t('landing.badge')}</span>
            </motion.div>

            {/* Main heading */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              style={{
                fontSize: 'clamp(40px, 6vw, 80px)',
                fontWeight: 800,
                color: 'white',
                lineHeight: 1.05,
                letterSpacing: '-0.04em',
                marginBottom: 24,
                maxWidth: 900,
                margin: '0 auto 24px',
              }}
            >
              {t('landing.heroLine1')}{' '}
              <span style={{ background: 'linear-gradient(135deg, #1a73e8, #4285f4, #8ab4f8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {t('landing.heroHighlight')}
              </span>
              {' '}{t('landing.heroLine2')}
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.55 }}
              style={{ fontSize: 18, color: 'rgba(255,255,255,0.55)', maxWidth: 560, margin: '0 auto 40px', lineHeight: 1.7 }}
            >
              {t('landing.heroSubtitle') || 'Intelligent analysis of bank statements with AI-powered risk assessment, fraud detection and comprehensive financial insights'}
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.65 }}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, marginBottom: 60 }}
            >
              <motion.button
                whileHover={{ scale: 1.04, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/analyses')}
                style={{
                  padding: '16px 36px', borderRadius: 14, border: 'none',
                  background: 'linear-gradient(135deg, #1a73e8, #1557b0)',
                  color: 'white', fontSize: 15, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                  boxShadow: '0 8px 32px rgba(26,115,232,0.4), 0 0 0 1px rgba(26,115,232,0.2)',
                  display: 'flex', alignItems: 'center', gap: 10,
                }}
              >
                {t('landing.startAnalysis') || 'Start Analysis'}
                <ArrowRight style={{ width: 18, height: 18 }} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.04, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/dashboard')}
                style={{
                  padding: '16px 36px', borderRadius: 14,
                  border: '1px solid rgba(255,255,255,0.15)',
                  background: 'rgba(255,255,255,0.05)',
                  backdropFilter: 'blur(10px)',
                  color: 'white', fontSize: 15, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                  display: 'flex', alignItems: 'center', gap: 10,
                }}
              >
                {t('landing.goToDashboard') || 'Dashboard'}
                <ChevronDown style={{ width: 18, height: 18 }} />
              </motion.button>
            </motion.div>

            {/* Floating stat cards */}
            <div style={{ position: 'relative', maxWidth: 900, margin: '0 auto', height: 200, zIndex: 1, pointerEvents: 'none' }}>
              {[
                { label: '100K+', sub: t('landing.floatTransactions'), icon: TrendingUp, x: '5%', y: '10%', delay: 0.8 },
                { label: '11', sub: t('landing.floatFraudModules'), icon: Shield, x: '70%', y: '0%', delay: 0.9 },
                { label: '5+', sub: t('landing.floatBanks'), icon: Gauge, x: '35%', y: '55%', delay: 1.0 },
              ].map((card, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 30, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ delay: card.delay, duration: 0.6 }}
                  style={{
                    position: 'absolute', left: card.x, top: card.y,
                    padding: '16px 22px', borderRadius: 16,
                    background: 'rgba(255,255,255,0.06)',
                    backdropFilter: 'blur(20px) saturate(150%)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    display: 'flex', alignItems: 'center', gap: 14,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                    animation: `float ${6 + i}s ease-in-out infinite`,
                    animationDelay: `${i * -2}s`,
                  }}
                >
                  <div style={{
                    width: 42, height: 42, borderRadius: 12,
                    background: 'linear-gradient(135deg, rgba(26,115,232,0.2), rgba(26,115,232,0.05))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: '1px solid rgba(26,115,232,0.15)',
                  }}>
                    <card.icon style={{ width: 20, height: 20, color: '#4285f4' }} />
                  </div>
                  <div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: 'white', letterSpacing: '-0.03em' }}>{card.label}</div>
                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', fontWeight: 500 }}>{card.sub}</div>
                  </div>
                </motion.div>
              ))}
            </div>

          </div>
        </motion.div>

        {/* Bottom curve */}
        <div style={{ position: 'absolute', bottom: -2, left: 0, right: 0, zIndex: 20 }}>
          <svg viewBox="0 0 1440 80" fill="none" style={{ width: '100%', display: 'block' }}>
            <path d="M0 40C240 80 480 80 720 40C960 0 1200 0 1440 40V80H0V40Z" fill="var(--bg)" />
          </svg>
        </div>
      </div>

      {/* ═══════════════════ TRUSTED BY / PARTNERS ═══════════════════ */}
      <Section className="relative z-10" delay={0.1}>
        <div style={{ maxWidth: 1000, margin: '0 auto', padding: '60px 40px 40px', textAlign: 'center' }}>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 30 }}>
            {t('landing.supportedBanks')}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 50, flexWrap: 'wrap', opacity: 0.4 }}>
            {['Kaspi Bank', 'Halyk Bank', 'Forte Bank', 'Jusan Bank', 'Binance'].map((name) => (
              <span key={name} style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em', whiteSpace: 'nowrap' }}>
                {name}
              </span>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════════════ DASHBOARD SHOWCASE ═══════════════════ */}
      <Section delay={0.15}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '60px 40px 80px', textAlign: 'center', position: 'relative', zIndex: 5 }}>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 12, color: 'var(--text)' }}>
            {t('landing.dashboardTitle') || 'Powerful Analytics Dashboard'}
          </h2>
          <p style={{ fontSize: 16, color: 'var(--text-muted)', maxWidth: 520, margin: '0 auto 50px', lineHeight: 1.7 }}>
            {t('landing.dashboardSubtitle') || 'Real-time insights, risk assessments and fraud detection in one beautiful interface'}
          </p>

          {/* Dashboard mockup with perspective */}
          <motion.div
            initial={{ opacity: 0, y: 60, rotateX: 8 }}
            whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            style={{
              perspective: 1200,
              maxWidth: 1000,
              margin: '0 auto',
            }}
          >
            <div style={{
              borderRadius: 20,
              overflow: 'hidden',
              background: '#0a0a0a',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0 40px 80px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.05) inset',
              padding: 3,
            }}>
              {/* Browser chrome */}
              <div style={{ background: '#141414', borderRadius: '17px 17px 0 0', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ display: 'flex', gap: 6 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }} />
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }} />
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#1a73e8' }} />
                </div>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                  <div style={{ background: '#0a0a0a', borderRadius: 8, padding: '5px 40px', fontSize: 11, color: 'rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Lock style={{ width: 10, height: 10 }} />
                    ntfast.io/dashboard
                  </div>
                </div>
              </div>

              {/* Dashboard content mockup */}
              <div style={{ background: '#0f0f0f', padding: '24px 28px', borderRadius: '0 0 17px 17px' }}>
                {/* Top bar mock */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <LogoIcon height={14} color="#1a73e8" />
                    <div style={{ display: 'flex', gap: 20 }}>
                      {['Dashboard', 'Analyses', 'Settings'].map((item, i) => (
                        <span key={item} style={{ fontSize: 12, color: i === 0 ? '#1a73e8' : 'rgba(255,255,255,0.4)', fontWeight: i === 0 ? 600 : 400 }}>{item}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: '#1a73e8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'white' }}>T</div>
                </div>

                {/* Stat cards mock */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
                  {[
                    { label: 'Total Checks', value: '156', color: '#1a73e8' },
                    { label: 'Completed', value: '142', color: '#1a73e8' },
                    { label: 'Risk Alerts', value: '12', color: '#f59e0b' },
                    { label: 'Active Users', value: '24', color: '#6366f1' },
                  ].map((s, i) => (
                    <div key={i} style={{ background: '#161616', borderRadius: 12, padding: '14px 16px', border: '1px solid rgba(255,255,255,0.04)' }}>
                      <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>{s.label}</div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: s.color, letterSpacing: '-0.03em' }}>{s.value}</div>
                    </div>
                  ))}
                </div>

                {/* Chart area mock */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                  <div style={{ background: '#161616', borderRadius: 12, padding: 16, border: '1px solid rgba(255,255,255,0.04)', height: 160 }}>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 12 }}>Monthly Activity</div>
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 100 }}>
                      {[40, 65, 50, 80, 60, 90, 70, 85, 55, 75, 95, 60].map((h, i) => (
                        <div key={i} style={{ flex: 1, height: `${h}%`, borderRadius: 4, background: i === 11 ? 'rgba(26,115,232,0.6)' : 'rgba(26,115,232,0.2)', transition: 'all 0.3s' }} />
                      ))}
                    </div>
                  </div>
                  <div style={{ background: '#161616', borderRadius: 12, padding: 16, border: '1px solid rgba(255,255,255,0.04)', height: 160 }}>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 12 }}>Risk Distribution</div>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 100 }}>
                      <div style={{
                        width: 90, height: 90, borderRadius: '50%',
                        background: `conic-gradient(#1a73e8 0% 65%, #f9ab00 65% 85%, #ea4335 85% 100%)`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <div style={{ width: 60, height: 60, borderRadius: '50%', background: '#161616', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <span style={{ fontSize: 14, fontWeight: 800, color: '#1a73e8' }}>65%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </Section>

      {/* ═══════════════════ FEATURES SECTION ═══════════════════ */}
      <div id="features" style={{ background: 'var(--bg-secondary)', position: 'relative', zIndex: 10 }}>
        <Section delay={0.1}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 40px' }}>
            <div style={{ textAlign: 'center', marginBottom: 60 }}>
              <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 12, color: 'var(--text)' }}>
                {t('landing.featuresTitle') || 'Everything You Need'}
              </h2>
              <p style={{ fontSize: 16, color: 'var(--text-muted)', maxWidth: 500, margin: '0 auto', lineHeight: 1.7 }}>
                {t('landing.featuresSubtitle') || 'Powerful tools for complete financial transaction analysis'}
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
              {[
                {
                  icon: ScanLine, color: '#1a73e8', bg: 'rgba(26,115,232,0.08)',
                  title: t('landing.featureAI') || 'AI Risk Assessment',
                  desc: t('landing.featureAIDesc') || 'Advanced machine learning algorithms analyze transaction patterns and detect anomalies in real-time',
                },
                {
                  icon: FileSearch, color: '#6366f1', bg: 'rgba(99,102,241,0.08)',
                  title: t('landing.featureParser') || 'Smart Document Parsing',
                  desc: t('landing.featureParserDesc') || 'Automatic parsing of PDF, Excel and CSV bank statements from Kaspi, Halyk, Forte and more',
                },
                {
                  icon: Shield, color: '#f59e0b', bg: 'rgba(245,158,11,0.08)',
                  title: t('landing.featureFraud') || 'Fraud Detection',
                  desc: t('landing.featureFraudDesc') || 'Comprehensive fraud scoring with red flags, suspicious patterns and actionable recommendations',
                },
                {
                  icon: BarChart4, color: '#06b6d4', bg: 'rgba(6,182,212,0.08)',
                  title: t('landing.featureAnalytics') || 'Deep Analytics',
                  desc: t('landing.featureAnalyticsDesc') || 'Monthly breakdowns, category analysis, top merchants, recurring payments and financial health metrics',
                },
                {
                  icon: Globe, color: '#5f6368', bg: 'rgba(95,99,104,0.08)',
                  title: t('landing.featureMultiBank') || 'Multi-Bank Support',
                  desc: t('landing.featureMultiBankDesc') || 'Support for all major Kazakhstan banks with automatic format detection and intelligent data extraction',
                },
                {
                  icon: Gauge, color: '#f9ab00', bg: 'rgba(249,171,0,0.08)',
                  title: t('landing.featureSpeed') || 'Lightning Fast',
                  desc: t('landing.featureSpeedDesc') || 'Process thousands of transactions in seconds with real-time progress tracking and background processing',
                },
              ].map((feature, i) => {
                const Icon = feature.icon;
                return (
                  <motion.div
                    key={i}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={scaleIn}
                    transition={{ delay: i * 0.08, duration: 0.5 }}
                    whileHover={{ y: -6, boxShadow: 'var(--card-shadow-hover)' }}
                    style={{
                      padding: 28,
                      borderRadius: 20,
                      background: 'var(--card)',
                      border: '1px solid var(--card-border)',
                      boxShadow: 'var(--card-shadow)',
                      cursor: 'default',
                      transition: 'box-shadow 0.3s, transform 0.3s',
                    }}
                  >
                    <div style={{
                      width: 48, height: 48, borderRadius: 14, background: feature.bg,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 18,
                    }}>
                      <Icon style={{ width: 22, height: 22, color: feature.color }} />
                    </div>
                    <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text)', marginBottom: 8, letterSpacing: '-0.02em' }}>{feature.title}</h3>
                    <p style={{ fontSize: 14, color: 'var(--text-muted)', lineHeight: 1.7 }}>{feature.desc}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </Section>
      </div>

      {/* ═══════════════════ HOW IT WORKS ═══════════════════ */}
      <Section delay={0.1}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 40px', position: 'relative', zIndex: 5 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12, display: 'block' }}>
                {t('landing.howItWorks') || 'How It Works'}
              </span>
              <h2 style={{ fontSize: 'clamp(28px, 3.5vw, 40px)', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 16, color: 'var(--text)' }}>
                {t('landing.howTitle') || 'Analyze with Confidence, Succeed with Ease'}
              </h2>
              <p style={{ fontSize: 15, color: 'var(--text-muted)', lineHeight: 1.8, marginBottom: 36 }}>
                {t('landing.howDesc') || 'Upload your bank statements and let our AI do the heavy lifting. Get comprehensive analysis in seconds, not hours.'}
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {[
                  { step: '01', title: t('landing.step1') || 'Upload Statement', desc: t('landing.step1Desc') || 'Drag & drop your PDF, Excel or CSV bank statement' },
                  { step: '02', title: t('landing.step2') || 'AI Analysis', desc: t('landing.step2Desc') || 'Our AI parses, categorizes and evaluates every transaction' },
                  { step: '03', title: t('landing.step3') || 'Get Insights', desc: t('landing.step3Desc') || 'Receive detailed risk reports, fraud alerts and financial metrics' },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={fadeUp}
                    transition={{ delay: i * 0.15 }}
                    style={{ display: 'flex', gap: 16 }}
                  >
                    <div style={{
                      width: 44, height: 44, borderRadius: 14, flexShrink: 0,
                      background: 'var(--accent-subtle)', border: '1px solid var(--accent-glow)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 14, fontWeight: 800, color: 'var(--accent)',
                    }}>
                      {item.step}
                    </div>
                    <div>
                      <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>{item.title}</h4>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>{item.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Right side — feature cards grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              {[
                { icon: FileText, title: t('landing.cardFormats'), desc: t('landing.cardFormatsDesc'), color: '#1a73e8' },
                { icon: RefreshCw, title: t('landing.cardBackground'), desc: t('landing.cardBackgroundDesc'), color: '#6366f1' },
                { icon: TrendingUp, title: t('landing.cardAnalytics'), desc: t('landing.cardAnalyticsDesc'), color: '#f59e0b' },
                { icon: Lock, title: t('landing.cardExport'), desc: t('landing.cardExportDesc'), color: '#ef4444' },
              ].map((card, i) => {
                const Icon = card.icon;
                return (
                  <motion.div
                    key={i}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={scaleIn}
                    transition={{ delay: 0.1 + i * 0.1 }}
                    whileHover={{ y: -4 }}
                    style={{
                      padding: 24, borderRadius: 18,
                      background: 'var(--card)', border: '1px solid var(--card-border)',
                      boxShadow: 'var(--card-shadow)',
                      textAlign: 'center',
                      transition: 'transform 0.3s',
                    }}
                  >
                    <div style={{
                      width: 48, height: 48, borderRadius: 14, margin: '0 auto 14px',
                      background: `${card.color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Icon style={{ width: 22, height: 22, color: card.color }} />
                    </div>
                    <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>{card.title}</h4>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{card.desc}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      </Section>

      {/* ═══════════════════ STATS BAR ═══════════════════ */}
      <div style={{ background: '#0a0a0a', position: 'relative', zIndex: 5 }}>
        <Section delay={0.1}>
          <div style={{ maxWidth: 1000, margin: '0 auto', padding: '60px 40px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, textAlign: 'center' }}>
            {[
              { value: '100K+', label: t('landing.statTransactions') },
              { value: '11', label: t('landing.statFraudModules') },
              { value: '5+', label: t('landing.statBanks') },
              { value: '~5 ' + t('landing.statMinutes'), label: t('landing.statSpeed') },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div style={{ fontSize: 36, fontWeight: 800, background: 'linear-gradient(135deg, #1a73e8, #4285f4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: '-0.03em', marginBottom: 6 }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)', fontWeight: 500 }}>{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </Section>
      </div>

      {/* ═══════════════════ CTA SECTION ═══════════════════ */}
      <Section delay={0.1}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '80px 40px', textAlign: 'center' }}>
          <motion.div
            style={{
              padding: '60px 40px', borderRadius: 28,
              background: 'linear-gradient(135deg, #0a0a0a, #111827)',
              border: '1px solid rgba(26,115,232,0.15)',
              boxShadow: '0 40px 80px rgba(0,0,0,0.15), 0 0 100px rgba(26,115,232,0.05)',
              position: 'relative', overflow: 'hidden',
            }}
          >
            {/* Glow */}
            <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(26,115,232,0.12), transparent 70%)', top: '-40%', right: '-10%' }} />
            <div style={{ position: 'absolute', width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(66,133,244,0.08), transparent 70%)', bottom: '-30%', left: '-5%' }} />

            <div style={{ position: 'relative', zIndex: 1 }}>
              <h2 style={{ fontSize: 32, fontWeight: 800, color: 'white', letterSpacing: '-0.03em', marginBottom: 12 }}>
                {t('landing.ctaTitle') || 'Ready to Start?'}
              </h2>
              <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.55)', marginBottom: 32, maxWidth: 440, margin: '0 auto 32px' }}>
                {t('landing.ctaDesc') || 'Join analysts who trust ntFAST for intelligent financial analysis'}
              </p>
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/analyses')}
                style={{
                  padding: '16px 40px', borderRadius: 14, border: 'none',
                  background: 'linear-gradient(135deg, #1a73e8, #1557b0)',
                  color: 'white', fontSize: 16, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                  boxShadow: '0 8px 32px rgba(26,115,232,0.4)',
                  display: 'inline-flex', alignItems: 'center', gap: 10,
                }}
              >
                {t('landing.startAnalysis') || 'Start Analysis'}
                <ArrowRight style={{ width: 18, height: 18 }} />
              </motion.button>
            </div>
          </motion.div>
        </div>
      </Section>

      {/* ═══════════════════ FOOTER ═══════════════════ */}
      <footer style={{ borderTop: '1px solid var(--divider)', padding: '40px 40px 30px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <LogoIcon height={16} color="var(--accent)" />
            <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.03em' }}>ntFAST</span>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            © {new Date().getFullYear()} ntFAST — Financial Analysis System for Transactions
          </p>
        </div>
      </footer>
    </div>
  );
}
