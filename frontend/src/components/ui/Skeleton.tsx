import { motion } from 'framer-motion';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => (
  <div
    className={`animate-pulse rounded-lg ${className}`}
    style={{ background: 'var(--card-border)' }}
  />
);

// Table skeleton with rows
export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 5 }) => (
  <div className="space-y-0">
    {/* Header */}
    <div
      className="flex gap-4 p-4 border-b"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--card-border)' }}
    >
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton key={`h-${i}`} className="h-4 flex-1 rounded" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIdx) => (
      <div
        key={rowIdx}
        className="flex gap-4 p-4 border-b"
        style={{ borderColor: 'var(--card-border)' }}
      >
        {Array.from({ length: cols }).map((_, colIdx) => (
          <Skeleton
            key={`r-${rowIdx}-${colIdx}`}
            className={`h-4 flex-1 rounded ${colIdx === 0 ? 'max-w-[160px]' : ''}`}
          />
        ))}
      </div>
    ))}
  </div>
);

// Card skeleton with stat-like layout
export const StatCardSkeleton: React.FC = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="backdrop-blur-xl rounded-2xl border p-6"
    style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
  >
    <div className="flex items-center gap-4">
      <Skeleton className="w-12 h-12 rounded-xl" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3 w-24 rounded" />
        <Skeleton className="h-8 w-16 rounded" />
      </div>
    </div>
  </motion.div>
);

// Page loading skeleton
export const PageSkeleton: React.FC = () => (
  <div
    className="min-h-screen p-8 space-y-6"
    style={{ background: 'var(--bg)' }}
  >
    {/* Title skeleton */}
    <div className="space-y-2">
      <Skeleton className="h-8 w-64 rounded-lg" />
      <Skeleton className="h-4 w-96 rounded" />
    </div>

    {/* Stats */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <StatCardSkeleton />
      <StatCardSkeleton />
      <StatCardSkeleton />
    </div>

    {/* Table */}
    <div
      className="backdrop-blur-xl rounded-2xl border overflow-hidden"
      style={{ background: 'var(--card)', borderColor: 'var(--card-border)' }}
    >
      <TableSkeleton rows={5} cols={5} />
    </div>
  </div>
);

export default Skeleton;
