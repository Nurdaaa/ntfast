import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useActivity } from '../context/ActivityContext';
import { useBackgroundAnalysis } from '../context/BackgroundAnalysisContext';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import {
  AlertTriangle, BadgeCheck, ScanSearch, ArrowRight,
  TrendingUp, Wallet, ShieldAlert, BarChart4, Activity, Zap,
  CheckCircle2, Clock, XCircle, ArrowUpRight, ArrowDownRight,
  Shield, Database, Wifi, WifiOff, ChevronRight, Sparkles,
} from 'lucide-react';
import { analysesAPI } from '../services/api';

/* ═══════════ types ═══════════ */

interface Stats {
  total_analyses: number;
  completed_analyses: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  completion_rate: number;
  total_subjects: number;
  avg_risk_score: number;
  total_income_sum: number;
  total_expense_sum: number;
  total_transactions_sum: number;
  failed_count: number;
  pending_count: number;
  in_progress_count: number;
  success_rate: number;
  monthly_chart: {
    month: string;
    month_label: string;
    total: number;
    completed: number;
    high_risk: number;
    avg_risk: number;
  }[];
}

interface RecentAnalysis {
  id: number;
  file_name?: string | null;
  account_owner?: string | null;
  bank_name?: string | null;
  status: string;
  risk_score: number;
  fraud_composite_score?: number | null;
  fraud_risk_level?: string | null;
  total_transactions?: number;
  created_at: string;
}

/* ═══════════ helpers ═══════════ */

function formatCurrency(amount: number): string {
  if (Math.abs(amount) >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(amount) >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (Math.abs(amount) >= 1_000) return `${(amount / 1_000).toFixed(0)}K`;
  return amount.toFixed(0);
}

function getRiskColor(score: number) {
  if (score <= 30) return { color: 'var(--success)', bg: 'var(--success-bg)', label: 'Low' };
  if (score <= 60) return { color: 'var(--warning)', bg: 'var(--warning-bg)', label: 'Medium' };
  return { color: 'var(--danger)', bg: 'var(--danger-bg)', label: 'High' };
}

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

/* ═══════════ animations ═══════════ */

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: (i: number) => ({
    opacity: 1, scale: 1,
    transition: { delay: i * 0.06, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
};

/* ═══════════ module-level cache ═══════════ */
let cachedStats: Stats | null = null;
let cachedRecent: RecentAnalysis[] = [];

/* ═══════════ component ═══════════ */

export const Dashboard = () => {
  const { user } = useAuth();
  const { userStatuses, isConnected } = useActivity();
  const bgAnalysis = useBackgroundAnalysis();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const activeUsersCount = Array.from(userStatuses.values()).filter(u => u.is_online).length;

  const [stats, setStats] = useState<Stats | null>(cachedStats);
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>(cachedRecent);
  const [loading, setLoading] = useState(cachedStats === null);
  const prevAnalyzingRef = useRef(bgAnalysis.isAnalyzing);

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (prevAnalyzingRef.current && !bgAnalysis.isAnalyzing) {
      loadDashboard();
    }
    prevAnalyzingRef.current = bgAnalysis.isAnalyzing;
  }, [bgAnalysis.isAnalyzing]);

  const loadDashboard = async () => {
    try {
      if (!cachedStats) setLoading(true);
      const results = await Promise.allSettled([
        analysesAPI.getStats(),
        analysesAPI.getAll(),
      ]);

      if (results[0].status === 'fulfilled') {
        cachedStats = results[0].value;
        setStats(results[0].value);
      }
      if (results[1].status === 'fulfilled') {
        const sorted = [...results[1].value]
          .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 5);
        cachedRecent = sorted;
        setRecentAnalyses(sorted);
      }
    } catch (error) {
      console.error('Dashboard load error:', error);
    } finally {
      setLoading(false);
    }
  };

  /* ── loading skeleton ── */
  if (loading) {
    return (
      <div className="px-6 lg:px-8 pb-8 fade-in">
        <div className="mb-8">
          <div className="h-32 premium-skeleton rounded-3xl mb-6" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 premium-skeleton rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 h-[420px] premium-skeleton rounded-2xl" />
          <div className="h-[420px] premium-skeleton rounded-2xl" />
        </div>
      </div>
    );
  }

  const s = stats || {
    total_analyses: 0, completed_analyses: 0, high_risk_count: 0, medium_risk_count: 0,
    low_risk_count: 0, completion_rate: 0, total_subjects: 0, avg_risk_score: 0,
    total_income_sum: 0, total_expense_sum: 0, total_transactions_sum: 0,
    failed_count: 0, pending_count: 0, in_progress_count: 0, success_rate: 0,
    monthly_chart: [],
  };

  const completedTotal = s.low_risk_count + s.medium_risk_count + s.high_risk_count;
  const riskPieData = completedTotal > 0 ? [
    { name: 'lowRisk', value: s.low_risk_count, pct: Math.round(s.low_risk_count / completedTotal * 100), color: '#34a853' },
    { name: 'mediumRisk', value: s.medium_risk_count, pct: Math.round(s.medium_risk_count / completedTotal * 100), color: '#f9ab00' },
    { name: 'highRiskLevel', value: s.high_risk_count, pct: Math.round(s.high_risk_count / completedTotal * 100), color: '#ea4335' },
  ] : [
    { name: 'lowRisk', value: 1, pct: 100, color: '#34a853' },
    { name: 'mediumRisk', value: 0, pct: 0, color: '#f9ab00' },
    { name: 'highRiskLevel', value: 0, pct: 0, color: '#ea4335' },
  ];

  const chartData = s.monthly_chart.map(m => ({
    name: m.month_label,
    total: m.total,
    completed: m.completed,
    high_risk: m.high_risk,
  }));

  const riskInfo = getRiskColor(s.avg_risk_score);
  const totalFlow = s.total_income_sum + Math.abs(s.total_expense_sum);
  const incomeRatio = totalFlow > 0 ? (s.total_income_sum / totalFlow) * 100 : 50;

  return (
    <div className="px-6 lg:px-8 pb-8 fade-in">

      {/* ═══════════ HERO BANNER ═══════════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        style={{
          position: 'relative',
          borderRadius: 24,
          overflow: 'hidden',
          marginBottom: 24,
          background: 'linear-gradient(135deg, #1a73e8 0%, #1557b0 50%, #0d47a1 100%)',
          padding: '36px 40px',
        }}
      >
        {/* Decorative elements */}
        <div style={{
          position: 'absolute', top: -60, right: -40, width: 200, height: 200,
          borderRadius: '50%', background: 'rgba(255,255,255,0.06)',
        }} />
        <div style={{
          position: 'absolute', bottom: -80, right: 120, width: 260, height: 260,
          borderRadius: '50%', background: 'rgba(255,255,255,0.04)',
        }} />
        <div style={{
          position: 'absolute', top: 20, right: 200, width: 80, height: 80,
          borderRadius: '50%', background: 'rgba(255,255,255,0.03)',
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', fontWeight: 500, marginBottom: 6, letterSpacing: 0.5 }}
              >
                {t('dashboard.subtitle')}
              </motion.p>
              <motion.h1
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1, duration: 0.5 }}
                style={{ fontSize: 30, fontWeight: 700, color: '#fff', letterSpacing: '-0.03em', lineHeight: 1.2 }}
              >
                {t('dashboard.welcome', { name: '' })}
                <span style={{ color: 'rgba(255,255,255,0.9)' }}>
                  {user?.full_name || t('common.user')}
                </span>
              </motion.h1>
            </div>

            {/* Hero quick stats */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="flex gap-3 flex-wrap"
            >
              {[
                { value: s.total_analyses, label: t('dashboard.totalChecks'), icon: BadgeCheck },
                { value: s.completed_analyses, label: t('analyses.completed'), icon: CheckCircle2 },
                { value: s.high_risk_count, label: t('dashboard.highRisk'), icon: ShieldAlert },
              ].map((item, i) => {
                const Icon = item.icon;
                return (
                  <div key={i} style={{
                    padding: '14px 20px',
                    borderRadius: 16,
                    background: 'rgba(255,255,255,0.12)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    minWidth: 120,
                  }}>
                    <div className="flex items-center gap-2" style={{ marginBottom: 6 }}>
                      <Icon style={{ width: 14, height: 14, color: 'rgba(255,255,255,0.6)' }} />
                      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>{item.label}</span>
                    </div>
                    <span style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: -1 }}>{item.value}</span>
                  </div>
                );
              })}
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* ═══════════ BENTO METRICS GRID ═══════════ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Risk Score — circular gauge */}
        <motion.div
          custom={0} variants={scaleIn} initial="hidden" animate="visible"
          className="glass-card relative overflow-hidden"
          style={{ padding: '24px 20px' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {t('dashboard.avgRisk') || 'Avg Risk'}
            </span>
            <AlertTriangle style={{ width: 16, height: 16, color: riskInfo.color }} />
          </div>
          <div className="flex items-center gap-4">
            {/* Mini ring */}
            <div style={{ position: 'relative', width: 60, height: 60, flexShrink: 0 }}>
              <svg viewBox="0 0 36 36" style={{ width: 60, height: 60, transform: 'rotate(-90deg)' }}>
                <circle cx="18" cy="18" r="14" fill="none" stroke="var(--bg-secondary)" strokeWidth="3.5" />
                <motion.circle
                  cx="18" cy="18" r="14" fill="none"
                  stroke={riskInfo.color}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeDasharray={`${(s.avg_risk_score / 100) * 87.96} 87.96`}
                  initial={{ strokeDasharray: '0 87.96' }}
                  animate={{ strokeDasharray: `${(s.avg_risk_score / 100) * 87.96} 87.96` }}
                  transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
                />
              </svg>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 800, color: riskInfo.color,
              }}>
                {s.avg_risk_score.toFixed(0)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {s.avg_risk_score <= 30 ? t('dashboard.lowRisk') : s.avg_risk_score <= 60 ? t('dashboard.mediumRisk') : t('dashboard.highRiskLevel')}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-faint)', marginTop: 2 }}>/ 100</div>
            </div>
          </div>
        </motion.div>

        {/* Financial Volume */}
        <motion.div
          custom={1} variants={scaleIn} initial="hidden" animate="visible"
          className="glass-card overflow-hidden"
          style={{ padding: '24px 20px' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {t('dashboard.totalVolume') || 'Volume'}
            </span>
            <Wallet style={{ width: 16, height: 16, color: 'var(--accent)' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <div className="flex items-baseline gap-2">
              <span style={{ fontSize: 13, color: 'var(--success)', fontWeight: 700 }}>
                <ArrowUpRight style={{ width: 12, height: 12, display: 'inline', marginRight: 2 }} />
                {formatCurrency(s.total_income_sum)}
              </span>
              <span style={{ fontSize: 13, color: 'var(--danger)', fontWeight: 700 }}>
                <ArrowDownRight style={{ width: 12, height: 12, display: 'inline', marginRight: 2 }} />
                {formatCurrency(Math.abs(s.total_expense_sum))}
              </span>
            </div>
          </div>
          {/* Income vs Expense visual bar */}
          <div style={{ height: 8, borderRadius: 8, overflow: 'hidden', display: 'flex', background: 'var(--bg-secondary)' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${incomeRatio}%` }}
              transition={{ duration: 1, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
              style={{ height: '100%', background: 'var(--success)', borderRadius: '8px 0 0 8px' }}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${100 - incomeRatio}%` }}
              transition={{ duration: 1, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
              style={{ height: '100%', background: 'var(--danger)', borderRadius: '0 8px 8px 0' }}
            />
          </div>
        </motion.div>

        {/* Transactions */}
        <motion.div
          custom={2} variants={scaleIn} initial="hidden" animate="visible"
          className="glass-card overflow-hidden"
          style={{ padding: '24px 20px' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {t('dashboard.processedTransactions') || 'Transactions'}
            </span>
            <Activity style={{ width: 16, height: 16, color: 'var(--accent)' }} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text)', letterSpacing: -1, lineHeight: 1 }}>
            {s.total_transactions_sum.toLocaleString('ru-RU')}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
            {t('dashboard.acrossAnalyses', { count: s.completed_analyses })}
          </div>
        </motion.div>

        {/* Active Users */}
        <motion.div
          custom={3} variants={scaleIn} initial="hidden" animate="visible"
          className="glass-card overflow-hidden"
          style={{ padding: '24px 20px' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {t('dashboard.activeUsers') || 'Online'}
            </span>
            <div className="flex items-center gap-1.5">
              {isConnected ? (
                <Wifi style={{ width: 14, height: 14, color: 'var(--success)' }} />
              ) : (
                <WifiOff style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
              )}
            </div>
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text)', letterSpacing: -1, lineHeight: 1 }}>
            {activeUsersCount}
          </div>
          <div className="flex items-center gap-1.5" style={{ marginTop: 8 }}>
            {isConnected && (
              <motion.div
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--success)' }}
              />
            )}
            <span style={{ fontSize: 11, color: isConnected ? 'var(--success)' : 'var(--text-muted)', fontWeight: 500 }}>
              {isConnected ? 'Real-time' : 'Offline'}
            </span>
          </div>
        </motion.div>
      </div>

      {/* ═══════════ STATUS PIPELINE ═══════════ */}
      <motion.div
        custom={4} variants={fadeUp} initial="hidden" animate="visible"
        className="glass-card mb-6"
        style={{ padding: '20px 28px' }}
      >
        <div className="flex items-center flex-wrap gap-4 lg:gap-0 justify-between">
          {[
            { icon: CheckCircle2, label: t('analyses.completed'), count: s.completed_analyses, color: 'var(--success)', bg: 'var(--success-bg)' },
            { icon: Clock, label: t('analyses.inProgress'), count: s.in_progress_count, color: 'var(--accent)', bg: 'var(--accent-subtle)' },
            { icon: Clock, label: t('analyses.pending'), count: s.pending_count, color: 'var(--warning)', bg: 'var(--warning-bg)' },
            { icon: XCircle, label: t('analyses.failed') || 'Failed', count: s.failed_count, color: 'var(--danger)', bg: 'var(--danger-bg)' },
          ].map((item, i) => {
            const Icon = item.icon;
            const total = s.total_analyses || 1;
            const pct = Math.round((item.count / total) * 100);
            return (
              <div key={i} className="flex items-center gap-3" style={{ flex: '1 1 auto', minWidth: 140 }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 12,
                  background: item.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Icon style={{ width: 18, height: 18, color: item.color }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="flex items-baseline gap-2">
                    <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--text)', letterSpacing: -0.5 }}>{item.count}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-faint)', fontWeight: 500 }}>{pct}%</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>{item.label}</div>
                </div>
                {i < 3 && (
                  <div className="hidden lg:block" style={{ width: 1, height: 40, background: 'var(--divider)', marginLeft: 16, marginRight: 16 }} />
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* ═══════════ CHARTS ROW ═══════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
        {/* Bar Chart */}
        <motion.div
          custom={5} variants={fadeUp} initial="hidden" animate="visible"
          className="lg:col-span-2 glass-card" style={{ padding: 28 }}
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>
                {t('dashboard.analysesByMonth') || 'Monthly Analytics'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {t('dashboard.analysesByMonthDesc')}
              </div>
            </div>
            <div className="flex items-center gap-4" style={{ fontSize: 11 }}>
              <div className="flex items-center gap-1.5">
                <div style={{ width: 8, height: 8, borderRadius: 2, background: 'rgba(26,115,232,0.45)' }} />
                <span style={{ color: 'var(--text-muted)' }}>{t('dashboard.totalChecks')}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div style={{ width: 8, height: 8, borderRadius: 2, background: 'rgba(234,67,53,0.35)' }} />
                <span style={{ color: 'var(--text-muted)' }}>{t('dashboard.highRisk')}</span>
              </div>
            </div>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--divider)" opacity={0.5} />
                <XAxis dataKey="name" stroke="var(--text-muted)" style={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-muted)" style={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backdropFilter: 'blur(24px)',
                    background: 'var(--card-hover)',
                    border: '1px solid var(--card-border)',
                    borderRadius: 14,
                    boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
                  }}
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = {
                      total: t('dashboard.totalChecks'),
                      completed: t('analyses.completed'),
                      high_risk: t('dashboard.highRisk'),
                    };
                    return [value, labels[name] || name];
                  }}
                />
                <Bar dataKey="total" fill="rgba(26,115,232,0.45)" radius={[6, 6, 2, 2]} name="total" />
                <Bar dataKey="completed" fill="rgba(26,115,232,0.25)" radius={[6, 6, 2, 2]} name="completed" />
                <Bar dataKey="high_risk" fill="rgba(234,67,53,0.35)" radius={[6, 6, 2, 2]} name="high_risk" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center" style={{ height: 320, color: 'var(--text-muted)' }}>
              <div className="text-center">
                <BarChart4 style={{ width: 48, height: 48, margin: '0 auto 12px', opacity: 0.3 }} />
                <p style={{ fontSize: 13 }}>{t('dashboard.noChartData')}</p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Risk Distribution */}
        <motion.div
          custom={6} variants={fadeUp} initial="hidden" animate="visible"
          className="glass-card flex flex-col" style={{ padding: 28 }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>
                {t('dashboard.riskDistribution')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {t('dashboard.riskByLevel')}
              </div>
            </div>
            <Shield style={{ width: 18, height: 18, color: 'var(--text-muted)' }} />
          </div>
          <div className="flex-1 flex flex-col justify-center">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={riskPieData}
                  cx="50%" cy="50%"
                  innerRadius={50} outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {riskPieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = {
                      lowRisk: t('dashboard.lowRisk'),
                      mediumRisk: t('dashboard.mediumRisk'),
                      highRiskLevel: t('dashboard.highRiskLevel'),
                    };
                    return [`${value} (${completedTotal > 0 ? Math.round((value as number) / completedTotal * 100) : 0}%)`, labels[name] || name];
                  }}
                  contentStyle={{
                    backdropFilter: 'blur(24px)',
                    background: 'var(--card-hover)',
                    border: '1px solid var(--card-border)',
                    borderRadius: 14,
                    boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-2">
              {riskPieData.map((item, i) => (
                <div key={i} className="flex items-center justify-between" style={{
                  padding: '10px 14px', borderRadius: 12,
                  background: 'var(--bg-secondary)',
                  transition: 'background 0.2s',
                }}>
                  <div className="flex items-center gap-2.5">
                    <div style={{ width: 10, height: 10, borderRadius: 4, background: item.color }} />
                    <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>{t(`dashboard.${item.name}`)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>{item.value}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      padding: '2px 6px', borderRadius: 6,
                      background: item.color + '18', color: item.color,
                    }}>
                      {item.pct}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* ═══════════ RECENT ANALYSES — TIMELINE STYLE ═══════════ */}
      <motion.div
        custom={7} variants={fadeUp} initial="hidden" animate="visible"
        className="glass-card mb-6" style={{ padding: 28 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'var(--accent-subtle)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Sparkles style={{ width: 20, height: 20, color: 'var(--accent)' }} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>
                {t('dashboard.recentAnalyses')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {t('dashboard.recentAnalysesDesc')}
              </div>
            </div>
          </div>
          <button
            onClick={() => navigate('/analyses')}
            className="flex items-center gap-1.5 hover:gap-2.5 transition-all"
            style={{
              padding: '8px 18px', fontSize: 13, fontWeight: 600,
              borderRadius: 12, background: 'var(--accent-subtle)', color: 'var(--accent)',
              border: 'none', cursor: 'pointer',
            }}
          >
            {t('dashboard.viewAll')}
            <ChevronRight style={{ width: 15, height: 15 }} />
          </button>
        </div>

        {recentAnalyses.length > 0 ? (
          <div className="space-y-1">
            {recentAnalyses.map((analysis, idx) => {
              const riskPct = analysis.fraud_composite_score ?? (analysis.risk_score * 10);
              const aRisk = getRiskColor(riskPct);
              return (
                <motion.div
                  key={analysis.id}
                  custom={idx}
                  variants={fadeUp}
                  initial="hidden"
                  animate="visible"
                  onClick={() => navigate('/analyses')}
                  className="cursor-pointer group"
                  style={{
                    padding: '16px 18px',
                    borderRadius: 16,
                    transition: 'all 0.2s ease',
                    background: 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 12,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'var(--bg-secondary)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  {/* Left */}
                  <div className="flex items-center gap-4" style={{ flex: 1, minWidth: 0 }}>
                    {/* Avatar */}
                    <div className={`subj-avatar ava-${(idx % 5) + 1}`} style={{ flexShrink: 0 }}>
                      {(analysis.account_owner || 'N')[0].toUpperCase()}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div className="flex items-center gap-2">
                        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {analysis.account_owner || 'N/A'}
                        </p>
                        {analysis.bank_name && (
                          <span style={{
                            padding: '2px 8px', fontSize: 10, fontWeight: 600, borderRadius: 6,
                            background: 'var(--accent-subtle)', color: 'var(--accent)',
                            whiteSpace: 'nowrap',
                          }}>
                            {analysis.bank_name}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3" style={{ marginTop: 3 }}>
                        <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                          {timeAgo(analysis.created_at)}
                        </span>
                        {analysis.total_transactions && (
                          <span className="flex items-center gap-1" style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                            <TrendingUp style={{ width: 10, height: 10 }} />
                            {analysis.total_transactions} txns
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right */}
                  <div className="flex items-center gap-3" style={{ flexShrink: 0 }}>
                    <span className={`status-pill ${
                      analysis.status === 'completed' ? 's-completed' :
                      analysis.status === 'failed' ? 's-failed' : 's-progress'
                    }`}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
                      {analysis.status === 'completed' ? t('analyses.completed') :
                       analysis.status === 'failed' ? (t('analyses.failed') || 'Failed') :
                       t('analyses.inProgress')}
                    </span>
                    {analysis.status === 'completed' && (
                      <div className="flex items-center gap-1.5" style={{
                        padding: '4px 10px', borderRadius: 8,
                        background: aRisk.bg,
                      }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: aRisk.color }} />
                        <span style={{ fontSize: 13, fontWeight: 700, color: aRisk.color }}>
                          {riskPct.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    <ArrowRight style={{ width: 14, height: 14, color: 'var(--text-faint)', transition: 'transform 0.2s' }}
                      className="group-hover:translate-x-0.5"
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : (
          <div className="text-center" style={{ padding: '48px 0', color: 'var(--text-muted)' }}>
            <ScanSearch style={{ width: 48, height: 48, margin: '0 auto 16px', opacity: 0.3 }} />
            <p style={{ fontSize: 14, fontWeight: 500 }}>{t('dashboard.noAnalyses')}</p>
            <button
              onClick={() => navigate('/analyses')}
              className="btn-gradient"
              style={{ marginTop: 20, padding: '10px 24px', fontSize: 13 }}
            >
              {t('dashboard.createFirst')}
            </button>
          </div>
        )}
      </motion.div>

      {/* ═══════════ BOTTOM INFO ROW ═══════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* User Info */}
        <motion.div
          custom={8} variants={fadeUp} initial="hidden" animate="visible"
          className="glass-card" style={{ padding: 28 }}
        >
          <div className="flex items-center gap-3 mb-5">
            <div style={{
              width: 44, height: 44, borderRadius: 14,
              background: 'linear-gradient(135deg, #1a73e8, #1557b0)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 18, fontWeight: 700,
            }}>
              {(user?.full_name || 'U')[0].toUpperCase()}
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>
                {t('dashboard.userInfo')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {user?.role === 'superadmin' ? t('dashboard.superadmin') : user?.role || 'User'}
              </div>
            </div>
          </div>
          <div className="space-y-1">
            {[
              { label: t('dashboard.fullName'), value: user?.full_name || '' },
              { label: t('dashboard.email'), value: user?.email || '' },
              { label: t('dashboard.role'), value: user?.role === 'superadmin' ? t('dashboard.superadmin') : user?.role || '' },
            ].map((row, i) => (
              <div key={i} className="flex justify-between items-center" style={{
                padding: '12px 14px', borderRadius: 12,
                background: i % 2 === 0 ? 'var(--bg-secondary)' : 'transparent',
              }}>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{row.label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{row.value}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* System Status */}
        <motion.div
          custom={9} variants={fadeUp} initial="hidden" animate="visible"
          className="glass-card" style={{ padding: 28 }}
        >
          <div className="flex items-center gap-3 mb-5">
            <div style={{
              width: 44, height: 44, borderRadius: 14,
              background: 'var(--success-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Zap style={{ width: 20, height: 20, color: 'var(--success)' }} />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>
                {t('dashboard.systemStatus')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--success)', fontWeight: 500 }}>
                All systems operational
              </div>
            </div>
          </div>
          <div className="space-y-1">
            {[
              { label: t('dashboard.database'), ok: true, message: t('dashboard.databaseConnected'), icon: Database },
              { label: t('dashboard.api'), ok: true, message: t('dashboard.apiWorking'), icon: Zap },
              { label: t('dashboard.authentication'), ok: true, message: t('dashboard.authActive'), icon: Shield },
              { label: t('dashboard.websockets'), ok: isConnected, message: isConnected ? (t('dashboard.websocketsActive') || 'Connected') : t('dashboard.websocketsStatus'), icon: Wifi },
            ].map((row, i) => {
              const Icon = row.icon;
              return (
                <div key={i} className="flex justify-between items-center" style={{
                  padding: '12px 14px', borderRadius: 12,
                  background: i % 2 === 0 ? 'var(--bg-secondary)' : 'transparent',
                }}>
                  <div className="flex items-center gap-2.5">
                    <Icon style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{row.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={row.ok ? { scale: [1, 1.2, 1] } : {}}
                      transition={{ repeat: row.ok ? Infinity : 0, duration: 3 }}
                      style={{
                        width: 7, height: 7, borderRadius: '50%',
                        background: row.ok ? 'var(--success)' : '#94a3b8',
                      }}
                    />
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{row.message}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
};
