import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
  Shield, User, Calendar, CreditCard, CheckCircle, AlertTriangle, X,
  TrendingUp, ArrowUpRight, ArrowDownRight, Activity,
  Network, Layers, ArrowLeftRight, Store, Eye,
  ChevronDown, ChevronRight, Zap, Target, Fingerprint, Clock,
  PieChart as PieChartIcon, FileText, Sparkles, Download, Loader2,
  Moon, Copy, CircleDollarSign, UserX
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { KaspiAnalysisResult, bankAnalysisAPI } from '../../services/api';
import { RiskScoreGauge } from './RiskScoreGauge';
import { ModuleScoreCard } from './ModuleScoreCard';

interface BankAnalysisReportProps {
  result: KaspiAnalysisResult;
  onClose: () => void;
}

type SectionId = 'overview' | 'financial' | 'antifraud' | 'details' | 'conclusions';

const SECTION_NAV: { id: SectionId; label: string; icon: any; description: string }[] = [
  { id: 'overview', label: 'Обзор', icon: Eye, description: 'Общая информация о счёте' },
  { id: 'financial', label: 'Финансы', icon: TrendingUp, description: 'Финансовый профиль' },
  { id: 'antifraud', label: 'ntFAST Антифрод', icon: Shield, description: 'Глубокий AI-анализ' },
  { id: 'details', label: 'Детали', icon: FileText, description: 'Транзакции и данные' },
  { id: 'conclusions', label: 'Выводы', icon: Target, description: 'Рекомендации AI' },
];

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('ru-RU').format(Math.round(value)) + ' \u20B8';
};

const CHART_COLORS = ['#1a73e8', '#4285f4', '#f9ab00', '#ea4335', '#0891b2', '#5f6368', '#8ab4f8', '#1557b0'];

export function BankAnalysisReport({ result, onClose }: BankAnalysisReportProps) {
  const [activeSection, setActiveSection] = useState<SectionId>('overview');
  const [expandedModule, setExpandedModule] = useState<string | null>(null);
  const [showAllTransactions, setShowAllTransactions] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const fraud = result.fraud_report;

  const handleExportPDF = async () => {
    try {
      setPdfLoading(true);
      const blob = await bankAnalysisAPI.exportPDF(result);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const owner = result.account?.owner || 'report';
      const safeName = owner.replace(/[^a-zA-Z0-9\u0400-\u04FF _-]/g, '').trim().slice(0, 30) || 'report';
      link.download = `ntFAST_${safeName}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export failed:', err);
      toast.error('Ошибка экспорта PDF. Попробуйте ещё раз.');
    } finally {
      setPdfLoading(false);
    }
  };

  // Helper: safely get count from a field that might be array or number
  const safeLen = (val: any): number => {
    if (Array.isArray(val)) return val.length;
    if (typeof val === 'number') return val;
    return 0;
  };

  const getModuleIcon = (name: string) => {
    const iconMap: Record<string, any> = {
      velocity: <Zap className="w-4 h-4" />,
      graph: <Network className="w-4 h-4" />,
      structuring: <Layers className="w-4 h-4" />,
      cross_reference: <ArrowLeftRight className="w-4 h-4" />,
      merchant_risk: <Store className="w-4 h-4" />,
      night_transactions: <Moon className="w-4 h-4" />,
      duplicate_payments: <Copy className="w-4 h-4" />,
      round_amounts: <CircleDollarSign className="w-4 h-4" />,
      profile_mismatch: <UserX className="w-4 h-4" />,
    };
    return iconMap[name] || <Activity className="w-4 h-4" />;
  };

  return (
    <div className="mb-8 fade-in">
      <div className="backdrop-blur-xl bg-white/95 dark:bg-gray-900/95 rounded-3xl border border-gray-200/50 dark:border-gray-800/50 shadow-2xl overflow-hidden">

        {/* ===== HEADER WITH ntFAST BRANDING ===== */}
        <div className="relative overflow-hidden">
          {/* Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-900 to-black" />
          {/* Animated pattern */}
          <div className="absolute inset-0 opacity-[0.07]">
            <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '20px 20px' }} />
          </div>
          {/* Glow orbs */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl" />

          <div className="relative p-8">
            {/* Top row: Logo & Close */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-14 h-14 rounded-2xl bg-[#2563eb] flex items-center justify-center shadow-xl shadow-blue-500/20">
                    <Shield className="w-7 h-7 text-white" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-slate-900 flex items-center justify-center">
                    <Sparkles className="w-2 h-2 text-white" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-bold text-white">ntFAST</h1>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-500/30 text-blue-300 border border-blue-500/30">
                      AI v2.0
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mt-0.5">Financial Analysis System for Transactions</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportPDF}
                  disabled={pdfLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-50 rounded-xl transition-all text-sm font-medium text-white border border-white/10 hover:border-white/20"
                  title="Download PDF Report"
                >
                  {pdfLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  <span className="hidden sm:inline">{pdfLoading ? 'Generating...' : 'PDF'}</span>
                </button>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                >
                  <X className="w-6 h-6 text-white/70 hover:text-white" />
                </button>
              </div>
            </div>

            {/* Account info */}
            <div className="flex flex-wrap items-center gap-6 text-sm text-gray-300">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-blue-400" />
                <span className="font-medium text-white">{result.account.owner}</span>
              </div>
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-blue-400" />
                <span>{result.account.card}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-blue-400" />
                <span>{result.account.period?.from || '?'} &mdash; {result.account.period?.to || '?'}</span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>{result.summary.total_transactions} транзакций</span>
              </div>
              {result.validation.is_valid ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'rgba(52,168,83,0.2)', color: '#34a853', borderWidth: 1, borderStyle: 'solid', borderColor: 'rgba(52,168,83,0.3)' }}>
                  <CheckCircle className="w-3.5 h-3.5" />
                  Верифицировано
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'rgba(217,119,6,0.2)', color: '#f59e0b', borderWidth: 1, borderStyle: 'solid', borderColor: 'rgba(217,119,6,0.3)' }}>
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Есть расхождения
                </span>
              )}
            </div>

            {/* Section Navigation */}
            <div className="flex gap-1.5 mt-6 overflow-x-auto pb-1">
              {SECTION_NAV.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? 'bg-white text-slate-900 shadow-lg shadow-white/20'
                        : 'bg-white/10 text-white/80 hover:bg-white/20 hover:text-white'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {section.label}
                    {section.id === 'antifraud' && fraud && (
                      <span className={`ml-1 w-2 h-2 rounded-full ${
                        fraud.composite_score >= 50 ? 'bg-red-400 animate-pulse' :
                        fraud.composite_score >= 25 ? 'bg-yellow-400' : 'bg-green-400'
                      }`} />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* ===== CONTENT SECTIONS ===== */}
        <div className="p-8">
          <AnimatePresence mode="wait">
            {/* SECTION 1: OVERVIEW */}
            {activeSection === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                  {[
                    { label: 'Общий доход', value: result.summary.total_income, icon: ArrowUpRight, color: 'green', prefix: '+' },
                    { label: 'Общий расход', value: result.summary.total_expense, icon: ArrowDownRight, color: 'red', prefix: '-' },
                    { label: 'Чистый поток', value: result.summary.net_flow, icon: TrendingUp, color: result.summary.net_flow >= 0 ? 'blue' : 'red', prefix: result.summary.net_flow >= 0 ? '+' : '' },
                    { label: 'Средний расход/день', value: result.summary.avg_daily_expense, icon: Activity, color: 'slate', prefix: '' },
                  ].map((kpi) => {
                    const Icon = kpi.icon;
                    const colorMap: Record<string, { bg: string; iconBg: string; text: string; border: string }> = {
                      green: { bg: 'from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20', iconBg: 'bg-green-500', text: 'text-green-700 dark:text-green-300', border: 'border-green-200/50 dark:border-green-800/40' },
                      red: { bg: 'from-red-50 to-red-50 dark:from-red-900/20 dark:to-red-900/20', iconBg: 'bg-red-500', text: 'text-red-700 dark:text-red-300', border: 'border-red-200/50 dark:border-red-800/40' },
                      blue: { bg: 'from-blue-50 to-blue-50 dark:from-blue-900/20 dark:to-blue-900/20', iconBg: 'bg-blue-500', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-200/50 dark:border-blue-800/40' },
                      slate: { bg: 'from-slate-50 to-gray-50 dark:from-slate-900/20 dark:to-gray-900/20', iconBg: 'bg-slate-500', text: 'text-slate-700 dark:text-slate-300', border: 'border-slate-200/50 dark:border-slate-800/40' },
                    };
                    const c = colorMap[kpi.color];
                    return (
                      <div
                        key={kpi.label}
                        className={`relative p-5 bg-gradient-to-br ${c.bg} rounded-2xl border ${c.border} group`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{kpi.label}</span>
                          <div className={`p-2 ${c.iconBg} rounded-xl shadow-lg`}>
                            <Icon className="w-4 h-4 text-white" />
                          </div>
                        </div>
                        <p className={`text-2xl font-bold ${c.text}`}>
                          {kpi.prefix}{formatCurrency(Math.abs(kpi.value))}
                        </p>
                      </div>
                    );
                  })}
                </div>

                {/* Account Summary Card */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Balance info */}
                  <div
                    className="p-6 bg-gradient-to-br from-slate-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-900/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <CreditCard className="w-5 h-5 text-blue-500" />
                      Информация о счёте
                    </h3>
                    <div className="space-y-3">
                      {[
                        { label: 'Владелец', value: result.account.owner },
                        { label: 'Карта', value: result.account.card },
                        { label: 'Номер счёта', value: result.account.account_number || '---' },
                        { label: 'Баланс на начало', value: formatCurrency(result.account.balance_start || 0) },
                        { label: 'Баланс на конец', value: formatCurrency(result.account.balance_end || 0) },
                        { label: 'Валюта', value: result.account.currency || 'KZT' },
                      ].map((row) => (
                        <div key={row.label} className="flex justify-between items-center py-1.5 border-b border-gray-200/50 dark:border-gray-700/30 last:border-0">
                          <span className="text-sm text-gray-500 dark:text-gray-400">{row.label}</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">{row.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quick risk summary */}
                  {fraud && (
                    <div
                      className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-900/30 rounded-2xl border border-blue-200/50 dark:border-blue-800/40"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-blue-500" />
                        ntFAST Risk Score
                      </h3>
                      <div className="flex items-center gap-6">
                        <RiskScoreGauge score={fraud.composite_score} riskLevel={fraud.risk_level} size={160} />
                        <div className="flex-1 space-y-2">
                          <p className="text-sm text-gray-600 dark:text-gray-300">
                            Система ntFAST проанализировала <span className="font-semibold text-blue-600 dark:text-blue-400">{result.summary.total_transactions}</span> транзакций по <span className="font-semibold text-blue-600 dark:text-blue-400">11 модулям</span> антифрод-анализа.
                          </p>
                          {fraud.red_flags && fraud.red_flags.length > 0 && (
                            <div className="flex items-center gap-2 mt-3">
                              <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
                              <span className="text-sm text-red-600 dark:text-red-400 font-medium">
                                Обнаружено {fraud.red_flags.length} {fraud.red_flags.length === 1 ? 'красный флаг' : fraud.red_flags.length < 5 ? 'красных флага' : 'красных флагов'}
                              </span>
                            </div>
                          )}
                          <button
                            onClick={() => setActiveSection('antifraud')}
                            className="mt-3 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1 transition-colors"
                          >
                            Подробный анализ <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Financial Health */}
                {result.analytics?.financial_health && (
                  <div
                    className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Activity className="w-5 h-5 text-emerald-500" />
                      Финансовое здоровье
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {[
                        { label: 'Норма сбережений', value: `${(result.analytics.financial_health.savings_rate * 100).toFixed(1)}%`, color: result.analytics.financial_health.savings_rate > 0.1 ? 'text-green-600' : 'text-red-600' },
                        { label: 'Тренд баланса', value: result.analytics.financial_health.balance_trend === 'growing' ? 'Растущий' : result.analytics.financial_health.balance_trend === 'declining' ? 'Падающий' : 'Стабильный', color: result.analytics.financial_health.balance_trend === 'growing' ? 'text-green-600' : result.analytics.financial_health.balance_trend === 'declining' ? 'text-red-600' : 'text-blue-600' },
                        { label: 'Финансовый буфер', value: `${result.analytics.financial_health.financial_buffer_days} дней`, color: result.analytics.financial_health.financial_buffer_days > 30 ? 'text-green-600' : 'text-yellow-600' },
                        { label: 'Доля необходимых', value: `${(result.analytics.financial_health.essential_ratio * 100).toFixed(0)}%`, color: 'text-gray-700 dark:text-gray-300' },
                      ].map((item) => (
                        <div key={item.label} className="text-center p-3 bg-gray-50 dark:bg-gray-700/30 rounded-xl">
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{item.label}</p>
                          <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* SECTION 2: FINANCIAL PROFILE */}
            {activeSection === 'financial' && (
              <motion.div
                key="financial"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {/* Financial summary KPIs (always shown) */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Общий доход', value: result.summary?.total_income || 0, color: 'green' },
                    { label: 'Общий расход', value: result.summary?.total_expense || 0, color: 'red' },
                    { label: 'Чистый поток', value: result.summary?.net_flow || 0, color: (result.summary?.net_flow || 0) >= 0 ? 'blue' : 'red' },
                    { label: 'Сред. расход/день', value: result.summary?.avg_daily_expense || 0, color: 'slate' },
                  ].map((kpi) => {
                    const colors: Record<string, string> = {
                      green: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border-green-200/50 dark:border-green-800/40',
                      red: 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border-red-200/50 dark:border-red-800/40',
                      blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-200/50 dark:border-blue-800/40',
                      slate: 'bg-slate-50 dark:bg-slate-900/20 text-slate-700 dark:text-slate-300 border-slate-200/50 dark:border-slate-800/40',
                    };
                    return (
                      <div key={kpi.label} className={`p-4 rounded-xl border ${colors[kpi.color]}`}>
                        <p className="text-xs font-medium opacity-70 mb-1">{kpi.label}</p>
                        <p className="text-xl font-bold">{formatCurrency(Math.abs(kpi.value))}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Monthly breakdown chart */}
                {result.analytics?.monthly_breakdown && result.analytics.monthly_breakdown.length > 0 && (
                  <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-blue-500" />
                      Динамика доходов и расходов по месяцам
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={result.analytics.monthly_breakdown}>
                        <defs>
                          <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#34a853" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#34a853" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ea4335" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#ea4335" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="month_name" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                        <Tooltip
                          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.15)', background: 'rgba(255,255,255,0.95)' }}
                          formatter={(value: number, name: string) => [formatCurrency(value), name === 'income' ? 'Доход' : 'Расход']}
                        />
                        <Area type="monotone" dataKey="income" stroke="#34a853" fill="url(#colorIncome)" strokeWidth={2.5} name="income" />
                        <Area type="monotone" dataKey="expense" stroke="#ea4335" fill="url(#colorExpense)" strokeWidth={2.5} name="expense" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Category breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Expense categories */}
                  {result.analytics?.category_breakdown?.expense && result.analytics.category_breakdown.expense.length > 0 && (
                    <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <PieChartIcon className="w-5 h-5 text-red-500" />
                        Категории расходов
                      </h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={result.analytics.category_breakdown.expense.slice(0, 8)}
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            innerRadius={50}
                            paddingAngle={2}
                            dataKey="amount"
                            nameKey="category"
                          >
                            {result.analytics.category_breakdown.expense.slice(0, 8).map((_, i) => (
                              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
                            formatter={(value: number) => [formatCurrency(value)]}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-2 mt-2">
                        {result.analytics.category_breakdown.expense.slice(0, 6).map((cat, i) => (
                          <div key={cat.category} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                              <span className="text-gray-600 dark:text-gray-400">{cat.category}</span>
                            </div>
                            <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(cat.amount)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Income categories */}
                  {result.analytics?.category_breakdown?.income && result.analytics.category_breakdown.income.length > 0 && (
                    <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <PieChartIcon className="w-5 h-5 text-green-500" />
                        Источники дохода
                      </h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={result.analytics.category_breakdown.income.slice(0, 8)}
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            innerRadius={50}
                            paddingAngle={2}
                            dataKey="amount"
                            nameKey="category"
                          >
                            {result.analytics.category_breakdown.income.slice(0, 8).map((_, i) => (
                              <Cell key={i} fill={CHART_COLORS[(i + 3) % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
                            formatter={(value: number) => [formatCurrency(value)]}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-2 mt-2">
                        {result.analytics.category_breakdown.income.slice(0, 6).map((cat, i) => (
                          <div key={cat.category} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS[(i + 3) % CHART_COLORS.length] }} />
                              <span className="text-gray-600 dark:text-gray-400">{cat.category}</span>
                            </div>
                            <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(cat.amount)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Top merchants */}
                {result.analytics?.top_merchants && result.analytics.top_merchants.length > 0 && (
                  <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Store className="w-5 h-5 text-slate-500" />
                      Топ мерчанты
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {result.analytics.top_merchants.slice(0, 9).map((merchant, i) => (
                        <div
                          key={merchant.merchant}
                          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/30 rounded-xl"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-900/30 flex items-center justify-center flex-shrink-0">
                              <span className="text-sm font-bold text-slate-600 dark:text-slate-400">
                                {i + 1}
                              </span>
                            </div>
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{merchant.merchant}</p>
                              <p className="text-xs text-gray-500">{merchant.count} операций</p>
                            </div>
                          </div>
                          <span className="text-sm font-semibold text-gray-900 dark:text-white ml-2 flex-shrink-0">
                            {formatCurrency(merchant.amount)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Weekday analysis */}
                {result.analytics?.weekday_analysis && result.analytics.weekday_analysis.length > 0 && (
                  <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-blue-500" />
                      Активность по дням недели
                    </h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={result.analytics.weekday_analysis}>
                        <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                        <Tooltip
                          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
                          formatter={(value: number) => [formatCurrency(value), 'Оборот']}
                        />
                        <Bar dataKey="amount" fill="#2563eb" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Fallback when no charts/analytics data */}
                {(!result.analytics?.monthly_breakdown || result.analytics.monthly_breakdown.length === 0) &&
                 (!result.analytics?.category_breakdown?.expense || result.analytics.category_breakdown.expense.length === 0) &&
                 (!result.analytics?.top_merchants || result.analytics.top_merchants.length === 0) && (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400">Детальная аналитика по категориям и мерчантам будет доступна при наличии расширенных данных в выписке.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* SECTION 3: ntFAST ANTIFRAUD */}
            {activeSection === 'antifraud' && (
              <motion.div
                key="antifraud"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {fraud ? (
                  <>
                    {/* ntFAST Analysis Pipeline Header */}
                    <div className="text-center mb-2">
                      <div
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-full border border-blue-200/50 dark:border-blue-800/40 mb-3"
                      >
                        <Fingerprint className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                          ntFAST AI Anti-Fraud Pipeline
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
                        Каждая транзакция проходит через 11 rule-based модулей антифрод-анализа.
                        Результаты объединяются взвешенным скорингом для финального Risk Score.
                      </p>
                    </div>

                    {/* Main Risk Score */}
                    <div className="flex flex-col lg:flex-row items-center gap-8 p-8 bg-gradient-to-br from-slate-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-900/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                      <RiskScoreGauge score={fraud.composite_score} riskLevel={fraud.risk_level} size={220} />

                      <div className="flex-1 w-full">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                          Результат анализа
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                          Композитный Risk Score рассчитан на основе взвешенных оценок всех модулей.
                          Чем выше значение, тем больше подозрительных паттернов обнаружено.
                        </p>

                        {/* Radar chart of modules */}
                        <ResponsiveContainer width="100%" height={220}>
                          <RadarChart data={[
                            { module: 'Velocity', score: fraud.velocity.risk_score },
                            { module: 'Граф', score: fraud.graph.risk_score },
                            { module: 'Структ.', score: fraud.structuring.risk_score },
                            { module: 'Cross-Ref', score: fraud.cross_reference.risk_score },
                            { module: 'Мерчанты', score: fraud.merchant_risk.risk_score },
                            ...(fraud.night_transactions ? [{ module: 'Ночные', score: fraud.night_transactions.risk_score }] : []),
                            ...(fraud.duplicate_payments ? [{ module: 'Дубли', score: fraud.duplicate_payments.risk_score }] : []),
                            ...(fraud.round_amounts ? [{ module: 'Круглые', score: fraud.round_amounts.risk_score }] : []),
                            ...(fraud.profile_mismatch ? [{ module: 'Профиль', score: fraud.profile_mismatch.risk_score }] : []),
                          ]}>
                            <PolarGrid strokeDasharray="3 3" className="text-gray-300 dark:text-gray-600" />
                            <PolarAngleAxis dataKey="module" tick={{ fontSize: 11, fill: '#6b7280' }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                            <Radar name="Risk Score" dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} strokeWidth={2} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Module Score Cards Grid */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Layers className="w-5 h-5 text-blue-500" />
                        Модули анализа
                        <span className="text-xs text-gray-400 font-normal ml-2">Нажмите для подробностей</span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                          { key: 'velocity', name: 'Velocity-анализ', score: fraud.velocity.risk_score, detail: `${fraud.velocity.burst_alerts.length} всплесков, ${fraud.velocity.daily_spikes.length} аномальных дней` },
                          { key: 'graph', name: 'Сетевой анализ', score: fraud.graph.risk_score, detail: `${fraud.graph.node_count} узлов, ${fraud.graph.cycles.length} циклов` },
                          { key: 'structuring', name: 'Структурирование', score: fraud.structuring.risk_score, detail: `${fraud.structuring.just_under_threshold.length} порогов, ${fraud.structuring.split_groups.length} дроблений` },
                          { key: 'cross_reference', name: 'Кросс-анализ', score: fraud.cross_reference.risk_score, detail: `Ratio: ${fraud.cross_reference.income_expense_ratio?.toFixed(2)}, ${fraud.cross_reference.rapid_pass_through.length} транзитов` },
                          { key: 'merchant_risk', name: 'Рисковые мерчанты', score: fraud.merchant_risk.risk_score, detail: `${fraud.merchant_risk.high_risk_merchants.length} высокого, ${fraud.merchant_risk.medium_risk_merchants.length} среднего` },
                          ...(fraud.night_transactions ? [{ key: 'night_transactions', name: 'Ночные транзакции', score: fraud.night_transactions.risk_score, detail: `${fraud.night_transactions.night_count} ночных, ${(fraud.night_transactions.night_ratio * 100).toFixed(1)}% от всех` }] : []),
                          ...(fraud.duplicate_payments ? [{ key: 'duplicate_payments', name: 'Дубли платежей', score: fraud.duplicate_payments.risk_score, detail: `${fraud.duplicate_payments.total_duplicates} дубликатов` }] : []),
                          ...(fraud.round_amounts ? [{ key: 'round_amounts', name: 'Круглые суммы', score: fraud.round_amounts.risk_score, detail: `${fraud.round_amounts.round_count} круглых, ${(fraud.round_amounts.round_ratio * 100).toFixed(1)}%` }] : []),
                          ...(fraud.profile_mismatch ? [{ key: 'profile_mismatch', name: 'Профиль клиента', score: fraud.profile_mismatch.risk_score, detail: `${safeLen(fraud.profile_mismatch.mismatches)} несоответствий` }] : []),
                        ].map((mod, i) => (
                          <ModuleScoreCard
                            key={mod.key}
                            name={mod.name}
                            score={mod.score}
                            detail={mod.detail}
                            icon={getModuleIcon(mod.key)}
                            index={i}
                            onClick={() => setExpandedModule(expandedModule === mod.key ? null : mod.key)}
                            isExpanded={expandedModule === mod.key}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Expanded Module Details */}
                    <AnimatePresence>
                      {expandedModule && (
                        <motion.div
                          key={`detail-${expandedModule}`}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.4 }}
                          className="overflow-hidden"
                        >
                          {/* Velocity */}
                          {expandedModule === 'velocity' && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Zap className="w-5 h-5 text-amber-500" />
                                  Velocity-анализ
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Обнаружение аномальных всплесков транзакций, дневных пиков и ускорения оборота.
                                </p>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {fraud.velocity.burst_alerts.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-orange-600 dark:text-orange-400 mb-2 flex items-center gap-1.5">
                                      <Zap className="w-3.5 h-3.5" />
                                      Серии быстрых транзакций ({fraud.velocity.burst_alerts.length})
                                    </h5>
                                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                                      {fraud.velocity.burst_alerts.map((burst, i) => (
                                        <div
                                          key={i}
                                          className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-sm border border-orange-200/50 dark:border-orange-800/30"
                                        >
                                          <div className="flex justify-between items-center">
                                            <span className="font-semibold text-orange-700 dark:text-orange-300">{burst.transaction_count} транзакций</span>
                                            <span className="text-xs text-gray-500">за {burst.window_hours}ч</span>
                                          </div>
                                          <div className="text-gray-600 dark:text-gray-400 mt-1">
                                            Сумма: {formatCurrency(burst.total_amount)}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {fraud.velocity.daily_spikes.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-2 flex items-center gap-1.5">
                                      <Activity className="w-3.5 h-3.5" />
                                      Дни с аномальной активностью ({fraud.velocity.daily_spikes.length})
                                    </h5>
                                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                                      {fraud.velocity.daily_spikes.map((spike, i) => (
                                        <div
                                          key={i}
                                          className="p-3 bg-red-50 dark:bg-red-900/20 rounded-xl text-sm border border-red-200/50 dark:border-red-800/30"
                                        >
                                          <div className="flex justify-between items-center">
                                            <span className="font-semibold text-red-700 dark:text-red-300">{spike.date}</span>
                                            <span className="text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-full font-medium">
                                              Z-score: {spike.z_score.toFixed(1)}
                                            </span>
                                          </div>
                                          <div className="text-gray-600 dark:text-gray-400 mt-1">
                                            {spike.transaction_count} операций &bull; {formatCurrency(spike.total_amount)}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              {fraud.velocity.burst_alerts.length === 0 && fraud.velocity.daily_spikes.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Аномальных всплесков не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Graph */}
                          {expandedModule === 'graph' && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Network className="w-5 h-5 text-blue-500" />
                                  Сетевой анализ
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Построение графа связей между контрагентами. Поиск циклических переводов и центральных узлов.
                                </p>
                              </div>
                              <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{fraud.graph.node_count}</p>
                                  <p className="text-xs text-gray-500">Узлов</p>
                                </div>
                                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{fraud.graph.edge_count}</p>
                                  <p className="text-xs text-gray-500">Связей</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{fraud.graph.cycles.length}</p>
                                  <p className="text-xs text-gray-500">Циклов</p>
                                </div>
                              </div>

                              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                {fraud.graph.cycles.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">Круговые переводы</h5>
                                    <div className="space-y-2 max-h-48 overflow-y-auto">
                                      {fraud.graph.cycles.slice(0, 10).map((cycle, i) => (
                                        <div key={i} className="p-3 bg-red-50 dark:bg-red-900/20 rounded-xl text-xs border border-red-200/50 dark:border-red-800/30">
                                          <div className="font-medium text-red-700 dark:text-red-300 truncate">
                                            {cycle.nodes.join(' \u2192 ')}
                                          </div>
                                          <div className="text-red-500 mt-1">{formatCurrency(cycle.total_flow)}</div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {fraud.graph.hub_nodes.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Ключевые контрагенты</h5>
                                    <div className="space-y-2 max-h-48 overflow-y-auto">
                                      {fraud.graph.hub_nodes.slice(0, 10).map((hub, i) => (
                                        <div key={i} className="p-3 bg-slate-50 dark:bg-slate-900/20 rounded-xl text-xs border border-slate-200/50 dark:border-slate-800/30 flex justify-between items-center">
                                          <div>
                                            <span className="font-medium text-slate-700 dark:text-slate-300">{hub.name}</span>
                                            <span className="text-gray-400 ml-1">({hub.connections} связей)</span>
                                          </div>
                                          <span className="text-slate-600 font-medium">{formatCurrency(hub.total_volume)}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Structuring */}
                          {expandedModule === 'structuring' && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Layers className="w-5 h-5 text-amber-500" />
                                  Обнаружение структурирования
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Поиск паттернов дробления крупных сумм: суммы у пороговых значений, разбивка операций, смурфинг.
                                </p>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {fraud.structuring.just_under_threshold.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-amber-600 dark:text-amber-400 mb-2">
                                      Суммы у порога ({fraud.structuring.just_under_threshold.length})
                                    </h5>
                                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                                      {fraud.structuring.just_under_threshold.slice(0, 8).map((item, i) => (
                                        <div key={i} className="text-xs p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200/50 dark:border-amber-800/30">
                                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                                          <span className="text-gray-500 ml-1">({item.pct_of_threshold}% от порога)</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {fraud.structuring.split_groups.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">
                                      Дробление ({fraud.structuring.split_groups.length})
                                    </h5>
                                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                                      {fraud.structuring.split_groups.map((group, i) => (
                                        <div key={i} className="text-xs p-2 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200/50 dark:border-red-800/30">
                                          <div className="font-medium text-red-700 dark:text-red-300 truncate">{group.counterparty}</div>
                                          <div className="text-gray-500">{group.transaction_count} op = {formatCurrency(group.total_amount)}</div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {fraud.structuring.smurfing_patterns.length > 0 && (
                                  <div>
                                    <h5 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">
                                      Smurfing ({fraud.structuring.smurfing_patterns.length})
                                    </h5>
                                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                                      {fraud.structuring.smurfing_patterns.map((p, i) => (
                                        <div key={i} className="text-xs p-2 bg-slate-50 dark:bg-slate-900/20 rounded-lg border border-slate-200/50 dark:border-slate-800/30">
                                          <div className="font-medium">{formatCurrency(p.amount)} x{p.occurrence_count}</div>
                                          <div className="text-gray-500">{p.unique_counterparties} получателей</div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              {fraud.structuring.just_under_threshold.length === 0 && fraud.structuring.split_groups.length === 0 && fraud.structuring.smurfing_patterns.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Признаков структурирования не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Cross Reference */}
                          {expandedModule === 'cross_reference' && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <ArrowLeftRight className="w-5 h-5 text-blue-500" />
                                  Кросс-анализ
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Сопоставление входящих и исходящих потоков. Обнаружение транзитных операций и необъяснимых поступлений.
                                </p>
                              </div>
                              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl mb-4">
                                <p className="text-sm text-gray-600 dark:text-gray-300">
                                  Соотношение доход/расход: <span className="font-bold text-blue-600 dark:text-blue-400">{fraud.cross_reference.income_expense_ratio?.toFixed(2)}</span>
                                </p>
                              </div>
                              {fraud.cross_reference.rapid_pass_through.length > 0 && (
                                <div>
                                  <h5 className="text-sm font-semibold text-orange-600 dark:text-orange-400 mb-2">
                                    Транзитные операции ({fraud.cross_reference.rapid_pass_through.length})
                                  </h5>
                                  <div className="space-y-2 max-h-60 overflow-y-auto">
                                    {fraud.cross_reference.rapid_pass_through.map((pt, i) => (
                                      <div
                                        key={i}
                                        className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-sm border border-orange-200/50 dark:border-orange-800/30"
                                      >
                                        <div className="flex items-center justify-between">
                                          <span className="text-green-600 font-semibold">+{formatCurrency(pt.income_amount)}</span>
                                          <div className="flex items-center gap-1 text-gray-400 text-xs">
                                            <Clock className="w-3 h-3" />
                                            {pt.time_gap_hours}ч
                                          </div>
                                          <span className="text-red-600 font-semibold">-{formatCurrency(pt.expense_amount)}</span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1 truncate">
                                          {pt.income_source} \u2192 {pt.expense_dest}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {fraud.cross_reference.rapid_pass_through.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Транзитных операций не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Merchant Risk */}
                          {expandedModule === 'merchant_risk' && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Store className="w-5 h-5 text-red-500" />
                                  Рисковые мерчанты
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Мерчанты из категорий повышенного риска: гемблинг, криптообменники, анонимные платёжные системы.
                                </p>
                              </div>
                              <div className="p-3 bg-gray-50 dark:bg-gray-700/30 rounded-xl mb-2">
                                <p className="text-sm text-gray-600 dark:text-gray-300">
                                  Высокорисковые мерчанты: <span className="font-bold text-red-500">{fraud.merchant_risk.total_high_risk_pct.toFixed(1)}%</span> от расходов ({formatCurrency(fraud.merchant_risk.total_high_risk_amount)})
                                </p>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {fraud.merchant_risk.high_risk_merchants.length > 0 && (
                                  <div>
                                    <h5 className="text-xs font-bold text-red-500 uppercase mb-2">Высокий риск</h5>
                                    <div className="space-y-2">
                                      {fraud.merchant_risk.high_risk_merchants.map((m, i) => (
                                        <div key={i} className="flex justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-xs border border-red-200/50 dark:border-red-800/30">
                                          <div>
                                            <span className="font-medium text-red-700 dark:text-red-300">{m.name}</span>
                                            <span className="text-gray-400 ml-1">({m.category})</span>
                                          </div>
                                          <div className="text-right">
                                            <span className="font-medium">{formatCurrency(m.amount)}</span>
                                            <span className="text-gray-400 ml-1">x{m.count}</span>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {fraud.merchant_risk.medium_risk_merchants.length > 0 && (
                                  <div>
                                    <h5 className="text-xs font-bold text-yellow-500 uppercase mb-2">Средний риск</h5>
                                    <div className="space-y-2">
                                      {fraud.merchant_risk.medium_risk_merchants.map((m, i) => (
                                        <div key={i} className="flex justify-between p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-xs border border-yellow-200/50 dark:border-yellow-800/30">
                                          <div>
                                            <span className="font-medium text-yellow-700 dark:text-yellow-300">{m.name}</span>
                                            <span className="text-gray-400 ml-1">({m.category})</span>
                                          </div>
                                          <div className="text-right">
                                            <span className="font-medium">{formatCurrency(m.amount)}</span>
                                            <span className="text-gray-400 ml-1">x{m.count}</span>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              {fraud.merchant_risk.high_risk_merchants.length === 0 && fraud.merchant_risk.medium_risk_merchants.length === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Рисковых мерчантов не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Night Transactions */}
                          {expandedModule === 'night_transactions' && fraud.night_transactions && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Moon className="w-5 h-5 text-blue-500" />
                                  Ночные транзакции
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Операции в период 23:00-06:00. Крупные ночные переводы и серии ночных операций могут указывать на подозрительную активность.
                                </p>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{fraud.night_transactions.night_count}</p>
                                  <p className="text-xs text-gray-500">Ночных операций</p>
                                </div>
                                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{(fraud.night_transactions.night_ratio * 100).toFixed(1)}%</p>
                                  <p className="text-xs text-gray-500">Доля ночных</p>
                                </div>
                                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{formatCurrency(fraud.night_transactions.night_total_amount)}</p>
                                  <p className="text-xs text-gray-500">Сумма ночных</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.night_transactions.large_night_transfers)}</p>
                                  <p className="text-xs text-gray-500">Крупных ночных</p>
                                </div>
                              </div>
                              {safeLen(fraud.night_transactions.night_clusters) > 0 && (
                                <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
                                  <p className="text-sm text-amber-700 dark:text-amber-300">
                                    <AlertTriangle className="w-4 h-4 inline mr-1" />
                                    Обнаружено <span className="font-bold">{safeLen(fraud.night_transactions.night_clusters)}</span> серий ночных операций (кластеры в 2-часовом окне)
                                  </p>
                                </div>
                              )}
                              {fraud.night_transactions.night_count === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Ночных транзакций не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Duplicate Payments */}
                          {expandedModule === 'duplicate_payments' && fraud.duplicate_payments && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <Copy className="w-5 h-5 text-orange-500" />
                                  Дублирующие платежи
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Повторяющиеся платежи на одинаковые суммы одному получателю или рассылка одинаковых сумм разным получателям.
                                </p>
                              </div>
                              <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{fraud.duplicate_payments.total_duplicates}</p>
                                  <p className="text-xs text-gray-500">Дубликатов</p>
                                </div>
                                <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{safeLen(fraud.duplicate_payments.duplicate_groups)}</p>
                                  <p className="text-xs text-gray-500">Групп</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.duplicate_payments.same_amount_diff_recipient)}</p>
                                  <p className="text-xs text-gray-500">Рассылок</p>
                                </div>
                              </div>
                              {fraud.duplicate_payments.total_duplicate_amount > 0 && (
                                <div className="p-3 bg-gray-50 dark:bg-gray-700/30 rounded-xl">
                                  <p className="text-sm text-gray-600 dark:text-gray-300">
                                    Общая сумма дублирующих платежей: <span className="font-bold text-orange-600 dark:text-orange-400">{formatCurrency(fraud.duplicate_payments.total_duplicate_amount)}</span>
                                  </p>
                                </div>
                              )}
                              {fraud.duplicate_payments.total_duplicates === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Дублирующих платежей не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Round Amounts */}
                          {expandedModule === 'round_amounts' && fraud.round_amounts && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <CircleDollarSign className="w-5 h-5 text-emerald-500" />
                                  Круглые суммы
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Высокая доля круглых сумм может указывать на фиктивные операции или обналичивание.
                                </p>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{fraud.round_amounts.round_count}</p>
                                  <p className="text-xs text-gray-500">Круглых</p>
                                </div>
                                <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{(fraud.round_amounts.round_ratio * 100).toFixed(1)}%</p>
                                  <p className="text-xs text-gray-500">Доля круглых</p>
                                </div>
                                <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(fraud.round_amounts.round_total_amount)}</p>
                                  <p className="text-xs text-gray-500">Сумма круглых</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.round_amounts.consecutive_round)}</p>
                                  <p className="text-xs text-gray-500">Подряд</p>
                                </div>
                              </div>
                              {fraud.round_amounts.round_count === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Аномалий с круглыми суммами не обнаружено</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Profile Mismatch */}
                          {expandedModule === 'profile_mismatch' && fraud.profile_mismatch && (
                            <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 space-y-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                  <UserX className="w-5 h-5 text-red-500" />
                                  Несоответствие профилю
                                </h4>
                                <p className="text-xs text-gray-500 mt-1">
                                  Операции, нетипичные для данного типа клиента: превышение лимитов, необычные категории, аномалии дохода.
                                </p>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.profile_mismatch.mismatches)}</p>
                                  <p className="text-xs text-gray-500">Несоответствий</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.profile_mismatch.oversized_transactions)}</p>
                                  <p className="text-xs text-gray-500">Крупных</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.profile_mismatch.unexpected_activity)}</p>
                                  <p className="text-xs text-gray-500">Нетипичных</p>
                                </div>
                                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">{safeLen(fraud.profile_mismatch.income_anomalies)}</p>
                                  <p className="text-xs text-gray-500">Аномалий дохода</p>
                                </div>
                              </div>
                              {safeLen(fraud.profile_mismatch.mismatches) === 0 && (
                                <div className="text-center py-8 text-gray-400">
                                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                  <p className="text-sm">Профиль клиента соответствует операциям</p>
                                </div>
                              )}
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </>
                ) : (
                  <div className="text-center py-16">
                    <Shield className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400 text-lg">ntFAST Антифрод-анализ</p>
                    <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
                      Данные антифрод-анализа недоступны для этого файла. Повторите загрузку.
                    </p>
                  </div>
                )}
              </motion.div>
            )}

            {/* SECTION 4: TRANSACTIONS */}
            {activeSection === 'details' && (
              <motion.div
                key="details"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                {/* Account profile info (from fraud engine) */}
                {fraud?.account_profile && (
                  <div className="p-5 bg-gradient-to-br from-blue-50 to-blue-50 dark:from-blue-900/20 dark:to-blue-900/20 rounded-2xl border border-blue-200/50 dark:border-blue-800/40">
                    <h3 className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-3 flex items-center gap-2">
                      <Fingerprint className="w-4 h-4" />
                      Профиль аккаунта (определён AI)
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Тип:</span>
                        <span className="ml-1 font-medium text-gray-900 dark:text-white capitalize">
                          {fraud.account_profile.account_type?.replace('_', ' ') || 'unknown'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Сред. доход/мес:</span>
                        <span className="ml-1 font-medium text-gray-900 dark:text-white">
                          {formatCurrency(fraud.account_profile.avg_monthly_income || 0)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Сред. расход/мес:</span>
                        <span className="ml-1 font-medium text-gray-900 dark:text-white">
                          {formatCurrency(fraud.account_profile.avg_monthly_expense || 0)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Регулярность:</span>
                        <span className="ml-1 font-medium text-gray-900 dark:text-white">
                          {((fraud.account_profile.income_regularity_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-500" />
                    Все транзакции ({result.transactions?.length || 0})
                  </h3>
                  {result.transactions?.length > 50 && (
                    <button
                      onClick={() => setShowAllTransactions(!showAllTransactions)}
                      className="text-sm text-blue-600 dark:text-blue-400 font-medium hover:text-blue-700 flex items-center gap-1"
                    >
                      {showAllTransactions ? 'Показать первые 50' : 'Показать все'}
                      <ChevronDown className={`w-4 h-4 transition-transform ${showAllTransactions ? 'rotate-180' : ''}`} />
                    </button>
                  )}
                </div>

                {result.transactions && result.transactions.length > 0 ? (
                <div className="overflow-hidden rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                  <div className="max-h-[600px] overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-800/80 sticky top-0 z-10">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">#</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Дата</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Описание</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Категория</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">Сумма</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-800/50">
                        {(showAllTransactions ? result.transactions : result.transactions.slice(0, 50)).map((tx, i) => (
                          <tr
                            key={i}
                            className="hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors"
                          >
                            <td className="px-4 py-3 text-gray-400 text-xs">{i + 1}</td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                              {new Date(tx.date).toLocaleDateString('ru-RU')}
                            </td>
                            <td className="px-4 py-3 text-gray-900 dark:text-white max-w-xs truncate">
                              {tx.details}
                            </td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400">
                                {tx.category}
                              </span>
                            </td>
                            <td className={`px-4 py-3 text-right font-semibold whitespace-nowrap ${
                              tx.amount >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                            }`}>
                              {tx.amount >= 0 ? '+' : ''}{formatCurrency(tx.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                ) : (
                  <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/30 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                    <FileText className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400">Данные транзакций недоступны для отображения в таблице.</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Информация о транзакциях доступна в антифрод-анализе.</p>
                  </div>
                )}

                {/* Anomalies */}
                {result.analytics?.anomalies && result.analytics.anomalies.length > 0 && (
                  <div className="p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-2xl border border-yellow-200/50 dark:border-yellow-800/40">
                    <h3 className="text-lg font-semibold text-yellow-700 dark:text-yellow-400 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Аномалии ({result.analytics.anomalies.length})
                    </h3>
                    <div className="space-y-2">
                      {result.analytics.anomalies.map((anomaly, i) => (
                        <div key={i} className="p-3 bg-white/80 dark:bg-gray-800/50 rounded-xl text-sm flex items-start gap-3 border border-yellow-200/50 dark:border-yellow-800/30">
                          <AlertTriangle className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium text-gray-900 dark:text-white">{anomaly.type}</span>
                            {anomaly.date && <span className="text-gray-500 ml-2">{anomaly.date}</span>}
                            {anomaly.amount && <span className="text-gray-500 ml-2">{formatCurrency(anomaly.amount)}</span>}
                            {anomaly.details && <p className="text-xs text-gray-500 mt-0.5">{anomaly.details}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* SECTION 5: CONCLUSIONS */}
            {activeSection === 'conclusions' && (
              <motion.div
                key="conclusions"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {fraud ? (
                  <>
                    {/* Final verdict */}
                    <div
                      className="p-8 bg-gradient-to-br from-slate-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-900/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40 text-center"
                    >
                      <div className="flex justify-center mb-4">
                        <RiskScoreGauge score={fraud.composite_score} riskLevel={fraud.risk_level} size={180} />
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                        Заключение ntFAST AI
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                        На основе анализа {result.summary.total_transactions} транзакций за период
                        {result.account.period?.from && ` с ${result.account.period.from}`}
                        {result.account.period?.to && ` по ${result.account.period.to}`},
                        система ntFAST оценила общий уровень риска как <span className="font-bold">
                          {fraud.risk_level === 'critical' ? 'КРИТИЧЕСКИЙ' : fraud.risk_level === 'high' ? 'ВЫСОКИЙ' : fraud.risk_level === 'medium' ? 'СРЕДНИЙ' : 'НИЗКИЙ'}
                        </span> ({fraud.composite_score.toFixed(1)}/100).
                      </p>
                    </div>

                    {/* Analysis summary - what was found step by step */}
                    <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-700/40">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Fingerprint className="w-5 h-5 text-blue-500" />
                        Этапы анализа ntFAST
                      </h3>
                      <div className="space-y-3">
                        {[
                          {
                            step: 1, name: 'Velocity-анализ', score: fraud.velocity.risk_score,
                            desc: fraud.velocity.burst_alerts.length > 0 || fraud.velocity.daily_spikes.length > 0
                              ? `Обнаружено ${fraud.velocity.burst_alerts.length} серий быстрых транзакций (burst) и ${fraud.velocity.daily_spikes.length} дней с аномальной активностью (Z-score > 2.5). ${fraud.velocity.amount_acceleration?.length > 0 ? `Крупные оттоки за 24ч: ${fraud.velocity.amount_acceleration.length} случаев.` : ''} ${fraud.velocity.counterparty_churn?.high_churn_days > 0 ? `Высокая частота новых контрагентов: ${fraud.velocity.counterparty_churn.high_churn_days} дней.` : ''}`
                              : 'Серий быстрых транзакций и аномальных дней не обнаружено. Частота операций в пределах нормы.'
                          },
                          {
                            step: 2, name: 'Сетевой/Графовый анализ', score: fraud.graph.risk_score,
                            desc: fraud.graph.node_count > 0
                              ? `Построен граф: ${fraud.graph.node_count} контрагентов, ${fraud.graph.edge_count} связей. ${fraud.graph.cycles.length > 0 ? `⚠️ Обнаружено ${fraud.graph.cycles.length} круговых переводов (round-tripping).` : 'Круговых переводов не обнаружено.'} ${fraud.graph.hub_nodes?.length > 0 ? `Ключевые хабы: ${fraud.graph.hub_nodes.slice(0, 3).map((h: any) => h.name).join(', ')}.` : ''}`
                              : 'Граф контрагентов пуст — нет данных о контрагентах для сетевого анализа.'
                          },
                          {
                            step: 3, name: 'Структурирование (AML)', score: fraud.structuring.risk_score,
                            desc: (fraud.structuring.just_under_threshold.length > 0 || fraud.structuring.split_groups.length > 0 || fraud.structuring.smurfing_patterns.length > 0)
                              ? `${fraud.structuring.just_under_threshold.length > 0 ? `${fraud.structuring.just_under_threshold.length} сумм близких к порогу 1M KZT (90-99%).` : ''} ${fraud.structuring.split_groups.length > 0 ? `${fraud.structuring.split_groups.length} случаев дробления суммы одному получателю.` : ''} ${fraud.structuring.smurfing_patterns.length > 0 ? `${fraud.structuring.smurfing_patterns.length} паттернов smurfing (одна сумма → разные получатели).` : ''}`.trim()
                              : 'Признаков структурирования (дробления для обхода порогов) не обнаружено.'
                          },
                          {
                            step: 4, name: 'Кросс-анализ доходов/расходов', score: fraud.cross_reference.risk_score,
                            desc: `Соотношение доходов к расходам: ${fraud.cross_reference.income_expense_ratio?.toFixed(2) || 'N/A'}. ${fraud.cross_reference.rapid_pass_through.length > 0 ? `⚠️ ${fraud.cross_reference.rapid_pass_through.length} транзитных операций (приход → быстрый отток похожей суммы за 48ч).` : 'Транзитных операций (pass-through) не обнаружено.'}`
                          },
                          {
                            step: 5, name: 'Рисковые мерчанты', score: fraud.merchant_risk.risk_score,
                            desc: (fraud.merchant_risk.high_risk_merchants.length > 0 || fraud.merchant_risk.medium_risk_merchants?.length > 0)
                              ? `${fraud.merchant_risk.high_risk_merchants.length > 0 ? `Высокий риск: ${fraud.merchant_risk.high_risk_merchants.map((m: any) => `${m.name} (${m.category})`).join(', ')} — ${fraud.merchant_risk.total_high_risk_pct.toFixed(1)}% расходов.` : ''} ${fraud.merchant_risk.medium_risk_merchants?.length > 0 ? `Средний риск: ${fraud.merchant_risk.medium_risk_merchants.slice(0, 3).map((m: any) => `${m.name} (${m.category})`).join(', ')}.` : ''}`.trim()
                              : 'Операций с высокорисковыми мерчантами (гемблинг, крипто, ломбарды) не обнаружено.'
                          },
                          ...(fraud.night_transactions ? [{
                            step: 6, name: 'Ночные транзакции (23:00-06:00)', score: fraud.night_transactions.risk_score,
                            desc: fraud.night_transactions.no_time_data
                              ? 'Анализ пропущен — в выписке отсутствует информация о времени транзакций (только даты).'
                              : fraud.night_transactions.night_count > 0
                                ? `${fraud.night_transactions.night_count} ночных операций (${(fraud.night_transactions.night_ratio * 100).toFixed(1)}% от всех). ${fraud.night_transactions.large_night_transfers?.length > 0 ? `Крупных ночных переводов (>50K): ${fraud.night_transactions.large_night_transfers.length}.` : ''} ${fraud.night_transactions.night_clusters?.length > 0 ? `Серий ночных транзакций: ${fraud.night_transactions.night_clusters.length}.` : ''}`
                                : 'Подозрительных ночных операций не обнаружено.'
                          }] : []),
                          ...(fraud.duplicate_payments ? [{
                            step: 7, name: 'Дублирующие платежи', score: fraud.duplicate_payments.risk_score,
                            desc: fraud.duplicate_payments.total_duplicates > 0
                              ? `${fraud.duplicate_payments.total_duplicates} дубликатов в ${safeLen(fraud.duplicate_payments.duplicate_groups)} группах. ${fraud.duplicate_payments.total_duplicate_amount > 0 ? `Общая сумма дублей: ${Math.round(fraud.duplicate_payments.total_duplicate_amount).toLocaleString('ru-RU')} KZT.` : ''} ${fraud.duplicate_payments.same_amount_diff_recipient?.length > 0 ? `⚠️ ${fraud.duplicate_payments.same_amount_diff_recipient.length} случаев веерной отправки одной суммы разным получателям.` : ''}`
                              : 'Повторных/дублирующих платежей одному получателю не обнаружено.'
                          }] : []),
                          ...(fraud.round_amounts ? [{
                            step: 8, name: 'Круглые суммы', score: fraud.round_amounts.risk_score,
                            desc: fraud.round_amounts.round_count > 0
                              ? `${fraud.round_amounts.round_count} круглых исходящих переводов (${(fraud.round_amounts.round_ratio * 100).toFixed(1)}% от исходящих). ${fraud.round_amounts.consecutive_round?.length > 0 ? `Серии круглых сумм подряд: ${fraud.round_amounts.consecutive_round.length}.` : ''} ${fraud.round_amounts.round_total_amount > 0 ? `Общая сумма: ${Math.round(fraud.round_amounts.round_total_amount).toLocaleString('ru-RU')} KZT.` : ''}`
                              : 'Подозрительных паттернов круглых сумм в исходящих переводах не обнаружено.'
                          }] : []),
                          ...(fraud.profile_mismatch ? [{
                            step: 9, name: 'Профиль клиента', score: fraud.profile_mismatch.risk_score,
                            desc: (safeLen(fraud.profile_mismatch.mismatches) > 0)
                              ? `${safeLen(fraud.profile_mismatch.oversized_transactions)} транзакций превышают норму для профиля. ${safeLen(fraud.profile_mismatch.unexpected_activity)} случаев нехарактерной активности. ${safeLen(fraud.profile_mismatch.income_anomalies)} аномальных поступлений.`
                              : 'Активность соответствует определённому профилю клиента. Отклонений не обнаружено.'
                          }] : []),
                        ].map((item, i, arr) => {
                          const scoreColor = item.score >= 50 ? 'text-red-500 bg-red-50 dark:bg-red-900/20' : item.score >= 25 ? 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20' : 'text-green-500 bg-green-50 dark:bg-green-900/20';
                          const lineColor = item.score >= 50 ? 'bg-red-400' : item.score >= 25 ? 'bg-yellow-400' : 'bg-green-400';
                          return (
                            <div
                              key={item.step}
                              className="flex items-start gap-4"
                            >
                              {/* Step number with connecting line */}
                              <div className="flex flex-col items-center">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${scoreColor}`}>
                                  {item.step}
                                </div>
                                {i < arr.length - 1 && <div className={`w-0.5 h-8 ${lineColor} opacity-30`} />}
                              </div>
                              <div className="flex-1 pb-2">
                                <div className="flex items-center justify-between">
                                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{item.name}</h4>
                                  <span className={`text-xs font-bold ${item.score >= 50 ? 'text-red-500' : item.score >= 25 ? 'text-yellow-500' : 'text-green-500'}`}>
                                    {item.score.toFixed(0)}/100
                                  </span>
                                </div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.desc}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Red Flags */}
                    {fraud.red_flags && fraud.red_flags.length > 0 && (
                      <div
                        className="p-6 bg-red-50 dark:bg-red-900/20 rounded-2xl border border-red-200/50 dark:border-red-800/40"
                      >
                        <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 mb-4 flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5" />
                          Красные флаги ({fraud.red_flags.length})
                        </h3>
                        <div className="space-y-2">
                          {fraud.red_flags.map((flag, i) => (
                            <div
                              key={i}
                              className="flex items-start gap-3 p-3 bg-white/80 dark:bg-gray-800/50 rounded-xl border border-red-200/30 dark:border-red-800/20"
                            >
                              <div className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center flex-shrink-0">
                                <span className="text-xs font-bold text-red-600 dark:text-red-400">{i + 1}</span>
                              </div>
                              <span className="text-sm text-gray-700 dark:text-gray-300">{flag}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {fraud.recommendations && fraud.recommendations.length > 0 && (
                      <div
                        className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200/50 dark:border-blue-800/40"
                      >
                        <h3 className="text-lg font-semibold text-blue-700 dark:text-blue-400 mb-4 flex items-center gap-2">
                          <Sparkles className="w-5 h-5" />
                          Рекомендации ntFAST AI ({fraud.recommendations.length})
                        </h3>
                        <div className="space-y-2">
                          {fraud.recommendations.map((rec, i) => (
                            <div
                              key={i}
                              className="flex items-start gap-3 p-3 bg-white/80 dark:bg-gray-800/50 rounded-xl border border-blue-200/30 dark:border-blue-800/20"
                            >
                              <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center flex-shrink-0">
                                <CheckCircle className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                              </div>
                              <span className="text-sm text-gray-700 dark:text-gray-300">{rec}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* ntFAST Footer */}
                    <div
                      className="text-center py-6 border-t border-gray-200/50 dark:border-gray-700/30"
                    >
                      <div className="flex items-center justify-center gap-2 text-sm text-gray-400 dark:text-gray-500">
                        <Shield className="w-4 h-4" />
                        <span>Отчёт сгенерирован системой <span className="font-semibold text-blue-500">ntFAST AI v2.0</span></span>
                      </div>
                      <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                        Financial Analysis System for Transactions &bull; {new Date().toLocaleString('ru-RU')}
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-16">
                    <Target className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">Выводы будут доступны после антифрод-анализа</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
