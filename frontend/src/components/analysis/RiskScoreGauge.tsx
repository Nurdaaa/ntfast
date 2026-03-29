import { motion } from 'framer-motion';

interface RiskScoreGaugeProps {
  score: number;
  riskLevel: string;
  size?: number;
}

const RISK_CONFIG: Record<string, { color: string; stroke: string; bg: string; label: string; glow: string }> = {
  critical: { color: 'text-red-500', stroke: 'stroke-red-500', bg: 'from-red-500 to-red-600', label: 'КРИТИЧЕСКИЙ', glow: 'shadow-red-500/50' },
  high: { color: 'text-orange-500', stroke: 'stroke-orange-500', bg: 'from-orange-500 to-amber-600', label: 'ВЫСОКИЙ', glow: 'shadow-orange-500/50' },
  medium: { color: 'text-yellow-500', stroke: 'stroke-yellow-500', bg: 'from-yellow-500 to-amber-500', label: 'СРЕДНИЙ', glow: 'shadow-yellow-500/50' },
  low: { color: 'text-green-500', stroke: 'stroke-green-500', bg: 'from-green-500 to-emerald-600', label: 'НИЗКИЙ', glow: 'shadow-green-500/50' },
};

export function RiskScoreGauge({ score, riskLevel, size = 200 }: RiskScoreGaugeProps) {
  const safeScore = score ?? 0;
  const config = RISK_CONFIG[riskLevel] || RISK_CONFIG.low;
  const circumference = 2 * Math.PI * 52;
  const dashArray = (safeScore / 100) * circumference;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      {/* Glow effect */}
      <div className={`absolute inset-4 rounded-full blur-2xl opacity-30 bg-gradient-to-br ${config.bg}`} />

      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
        {/* Background track */}
        <circle
          cx="60" cy="60" r="52"
          fill="none" strokeWidth="6"
          className="stroke-gray-200 dark:stroke-gray-700"
        />
        {/* Secondary track for depth */}
        <circle
          cx="60" cy="60" r="52"
          fill="none" strokeWidth="6"
          className="stroke-gray-100 dark:stroke-gray-800"
          strokeDasharray="4 4"
          opacity={0.5}
        />
        {/* Animated score arc */}
        <motion.circle
          cx="60" cy="60" r="52"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className={config.stroke}
          initial={{ strokeDasharray: `0 ${circumference}` }}
          animate={{ strokeDasharray: `${isNaN(dashArray) ? 0 : dashArray} ${circumference}` }}
          transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className={`text-4xl font-bold ${config.color}`}
        >
          {safeScore.toFixed(1)}
        </motion.span>
        <span className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">/ 100</span>
        <motion.span
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8, duration: 0.3 }}
          className={`text-[10px] font-bold uppercase mt-2 px-3 py-1 rounded-full bg-gradient-to-r ${config.bg} text-white shadow-lg ${config.glow}`}
        >
          {config.label}
        </motion.span>
      </div>
    </motion.div>
  );
}
