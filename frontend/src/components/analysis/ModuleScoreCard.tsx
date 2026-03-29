import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface ModuleScoreCardProps {
  name: string;
  score: number;
  detail: string;
  icon: ReactNode;
  index: number;
  onClick?: () => void;
  isExpanded?: boolean;
}

export function ModuleScoreCard({ name, score, detail, icon, index, onClick, isExpanded }: ModuleScoreCardProps) {
  const getScoreColor = (s: number) => {
    if (s >= 60) return { bar: 'bg-red-500', text: 'text-red-500', ring: 'ring-red-500/20', glow: 'group-hover:shadow-red-500/20' };
    if (s >= 30) return { bar: 'bg-yellow-500', text: 'text-yellow-500', ring: 'ring-yellow-500/20', glow: 'group-hover:shadow-yellow-500/20' };
    return { bar: 'bg-green-500', text: 'text-green-500', ring: 'ring-green-500/20', glow: 'group-hover:shadow-green-500/20' };
  };

  const colors = getScoreColor(score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4, scale: 1.02 }}
      onClick={onClick}
      className={`group relative cursor-pointer p-4 rounded-2xl bg-white dark:bg-gray-800/60 border border-gray-200/60 dark:border-gray-700/40
        shadow-md hover:shadow-xl ${colors.glow} transition-all duration-300
        ${isExpanded ? `ring-2 ${colors.ring}` : ''}`}
    >
      {/* Score indicator dot */}
      <div className={`absolute top-3 right-3 w-2.5 h-2.5 rounded-full ${colors.bar} shadow-lg`} />

      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-300">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white truncate">{name}</h4>
          <p className="text-[10px] text-gray-400 dark:text-gray-500 truncate">{detail}</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, score)}%` }}
            transition={{ delay: index * 0.08 + 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className={`h-full rounded-full ${colors.bar}`}
          />
        </div>
        <span className={`text-sm font-bold ${colors.text} min-w-[2rem] text-right`}>
          {score.toFixed(0)}
        </span>
      </div>
    </motion.div>
  );
}
