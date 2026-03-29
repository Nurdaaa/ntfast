import {
  Car,
  ShoppingCart,
  Gamepad2,
  Smartphone,
  ShoppingBag,
  UtensilsCrossed,
  Package,
  HeartPulse,
  Home,
  Globe,
  CreditCard,
  Shield,
  HeartHandshake,
  Landmark,
  Building2,
  Briefcase,
  Banknote,
  Users,
  User,
  ArrowRightLeft,
  TrendingUp,
  MoreHorizontal,
  LucideIcon
} from 'lucide-react';

// Маппинг категорий на иконки
const CATEGORY_ICONS: Record<string, LucideIcon> = {
  // Расходы
  'Транспорт': Car,
  'Еда и продукты': ShoppingCart,
  'Игры и развлечения': Gamepad2,
  'Подписки и сервисы': Smartphone,
  'Шоппинг': ShoppingBag,
  'Доставка еды': UtensilsCrossed,
  'Почта и доставка': Package,
  'Здоровье': HeartPulse,
  'Связь и коммуналка': Home,
  'Онлайн-покупки': Globe,
  'Рестораны': UtensilsCrossed,
  'Банковские услуги': CreditCard,
  'Страхование': Shield,
  'Благотворительность': HeartHandshake,
  'Прочие покупки': ShoppingBag,
  'Прочее': MoreHorizontal,
  'Разное': MoreHorizontal,

  // Переводы
  'Депозит': Landmark,
  'Межбанк': Building2,
  'Частые контакты': User,
  'Остальные контакты': Users,
  'Перевод': ArrowRightLeft,

  // Доходы
  'Пенсия/пособие': Briefcase,
  'С депозита': Landmark,
  'От частых контактов': User,
  'От остальных': Users,
  'Пополнение': TrendingUp,

  // Снятие
  'Снятие наличных': Banknote,
};

// Цвета для категорий
const CATEGORY_COLORS: Record<string, { bg: string; text: string; iconBg: string }> = {
  'Транспорт': { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', iconBg: 'bg-blue-500' },
  'Еда и продукты': { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', iconBg: 'bg-orange-500' },
  'Игры и развлечения': { bg: 'bg-gray-50 dark:bg-gray-900/20', text: 'text-gray-600 dark:text-gray-400', iconBg: 'bg-gray-500' },
  'Подписки и сервисы': { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-600 dark:text-indigo-400', iconBg: 'bg-indigo-500' },
  'Шоппинг': { bg: 'bg-zinc-50 dark:bg-zinc-900/20', text: 'text-zinc-600 dark:text-zinc-400', iconBg: 'bg-zinc-500' },
  'Доставка еды': { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', iconBg: 'bg-amber-500' },
  'Почта и доставка': { bg: 'bg-teal-50 dark:bg-teal-900/20', text: 'text-teal-600 dark:text-teal-400', iconBg: 'bg-teal-500' },
  'Здоровье': { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', iconBg: 'bg-red-500' },
  'Связь и коммуналка': { bg: 'bg-cyan-50 dark:bg-cyan-900/20', text: 'text-cyan-600 dark:text-cyan-400', iconBg: 'bg-cyan-500' },
  'Онлайн-покупки': { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-600 dark:text-indigo-400', iconBg: 'bg-indigo-500' },
  'Рестораны': { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', iconBg: 'bg-orange-500' },
  'Банковские услуги': { bg: 'bg-slate-50 dark:bg-slate-900/20', text: 'text-slate-600 dark:text-slate-400', iconBg: 'bg-slate-500' },
  'Страхование': { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', iconBg: 'bg-emerald-500' },
  'Благотворительность': { bg: 'bg-stone-50 dark:bg-stone-900/20', text: 'text-stone-600 dark:text-stone-400', iconBg: 'bg-stone-500' },
  'Депозит': { bg: 'bg-sky-50 dark:bg-sky-900/20', text: 'text-sky-600 dark:text-sky-400', iconBg: 'bg-sky-500' },
  'Межбанк': { bg: 'bg-stone-50 dark:bg-stone-900/20', text: 'text-stone-600 dark:text-stone-400', iconBg: 'bg-stone-500' },
  'Частые контакты': { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', iconBg: 'bg-green-500' },
  'Остальные контакты': { bg: 'bg-lime-50 dark:bg-lime-900/20', text: 'text-lime-600 dark:text-lime-400', iconBg: 'bg-lime-500' },
  'Перевод': { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', iconBg: 'bg-blue-500' },
  'Пенсия/пособие': { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', iconBg: 'bg-green-500' },
  'С депозита': { bg: 'bg-sky-50 dark:bg-sky-900/20', text: 'text-sky-600 dark:text-sky-400', iconBg: 'bg-sky-500' },
  'От частых контактов': { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', iconBg: 'bg-green-500' },
  'От остальных': { bg: 'bg-lime-50 dark:bg-lime-900/20', text: 'text-lime-600 dark:text-lime-400', iconBg: 'bg-lime-500' },
  'Пополнение': { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', iconBg: 'bg-green-500' },
  'Снятие наличных': { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', iconBg: 'bg-amber-500' },
};

const DEFAULT_COLORS = { bg: 'bg-gray-50 dark:bg-gray-800/50', text: 'text-gray-600 dark:text-gray-400', iconBg: 'bg-gray-500' };

interface CategoryIconProps {
  category: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function CategoryIcon({ category, size = 'md', showLabel = true, className = '' }: CategoryIconProps) {
  // Убираем эмодзи из названия категории если есть
  const cleanCategory = category.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim();

  const Icon = CATEGORY_ICONS[cleanCategory] || MoreHorizontal;
  const colors = CATEGORY_COLORS[cleanCategory] || DEFAULT_COLORS;

  const sizeClasses = {
    sm: { container: 'gap-1.5', icon: 'w-3.5 h-3.5', iconContainer: 'p-1', text: 'text-xs' },
    md: { container: 'gap-2', icon: 'w-4 h-4', iconContainer: 'p-1.5', text: 'text-sm' },
    lg: { container: 'gap-3', icon: 'w-5 h-5', iconContainer: 'p-2', text: 'text-base' },
  };

  const sizes = sizeClasses[size];

  if (!showLabel) {
    return (
      <div className={`${sizes.iconContainer} ${colors.iconBg} rounded-lg ${className}`}>
        <Icon className={`${sizes.icon} text-white`} />
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center ${sizes.container} ${colors.bg} ${colors.text} px-2.5 py-1.5 rounded-lg ${className}`}>
      <div className={`${sizes.iconContainer} ${colors.iconBg} rounded-md`}>
        <Icon className={`${sizes.icon} text-white`} />
      </div>
      <span className={`${sizes.text} font-medium`}>{cleanCategory}</span>
    </div>
  );
}

// Экспорт функций для использования напрямую
export function getCategoryIcon(category: string): LucideIcon {
  const cleanCategory = category.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim();
  return CATEGORY_ICONS[cleanCategory] || MoreHorizontal;
}

export function getCategoryColors(category: string) {
  const cleanCategory = category.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim();
  return CATEGORY_COLORS[cleanCategory] || DEFAULT_COLORS;
}

export default CategoryIcon;
