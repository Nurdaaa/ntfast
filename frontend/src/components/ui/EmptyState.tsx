import { LucideIcon, Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Inbox,
  title,
  description,
  action,
}) => (
  <div className="flex flex-col items-center justify-center py-16 px-6 text-center fade-in">
    <div
      className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
      style={{ background: 'var(--bg-secondary)' }}
    >
      <Icon className="w-8 h-8" style={{ color: 'var(--text-faint)' }} />
    </div>
    <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
      {title}
    </h3>
    {description && (
      <p className="text-sm max-w-sm" style={{ color: 'var(--text-muted)' }}>
        {description}
      </p>
    )}
    {action && (
      <button
        onClick={action.onClick}
        className="mt-4 px-5 py-2.5 text-white rounded-xl font-medium text-sm shadow-lg hover:shadow-xl transition-shadow duration-300"
        style={{ background: 'var(--accent)' }}
      >
        {action.label}
      </button>
    )}
  </div>
);

export default EmptyState;
