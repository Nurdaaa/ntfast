import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Check, X } from 'lucide-react';

interface PasswordStrengthProps {
  password: string;
}

interface StrengthCheck {
  label: string;
  met: boolean;
}

const getStrength = (password: string): { score: number; checks: StrengthCheck[] } => {
  const checks: StrengthCheck[] = [
    { label: 'Минимум 6 символов', met: password.length >= 6 },
    { label: 'Содержит заглавную букву', met: /[A-ZА-ЯЁ]/.test(password) },
    { label: 'Содержит строчную букву', met: /[a-zа-яё]/.test(password) },
    { label: 'Содержит цифру', met: /[0-9]/.test(password) },
    { label: 'Содержит спецсимвол', met: /[^A-Za-zА-Яа-яЁё0-9]/.test(password) },
  ];

  const score = checks.filter(c => c.met).length;
  return { score, checks };
};

const strengthLevels = [
  { text: 'Очень слабый', color: 'var(--danger)', barColor: 'var(--danger)' },
  { text: 'Очень слабый', color: 'var(--danger)', barColor: 'var(--danger)' },
  { text: 'Слабый', color: 'var(--warning)', barColor: 'var(--warning)' },
  { text: 'Средний', color: '#e37400', barColor: '#f9ab00' },
  { text: 'Хороший', color: 'var(--accent)', barColor: 'var(--accent)' },
  { text: 'Отличный', color: 'var(--success)', barColor: 'var(--success)' },
];

const getStrengthLabel = (score: number) => strengthLevels[score] || strengthLevels[0];

export const PasswordStrength: React.FC<PasswordStrengthProps> = ({ password }) => {
  const { score, checks } = useMemo(() => getStrength(password), [password]);
  const { text, color, barColor } = getStrengthLabel(score);

  if (!password) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      className="mt-2 space-y-2"
    >
      {/* Strength Bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 flex gap-1">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-1.5 flex-1 rounded-full transition-all duration-300"
              style={{ background: i <= score ? barColor : 'var(--card-border)' }}
            />
          ))}
        </div>
        <span className="text-xs font-medium min-w-[80px] text-right" style={{ color }}>
          {text}
        </span>
      </div>

      {/* Checklist */}
      <div className="grid grid-cols-1 gap-1">
        {checks.map((check, i) => (
          <div key={i} className="flex items-center gap-1.5">
            {check.met ? (
              <Check className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--success)' }} />
            ) : (
              <X className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--text-faint)' }} />
            )}
            <span
              className="text-xs"
              style={{ color: check.met ? 'var(--success)' : 'var(--text-faint)' }}
            >
              {check.label}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export default PasswordStrength;
