import { useState, useEffect, useRef } from 'react';
import { Loader2, X, ChevronDown, ChevronUp, FileType2, BadgeCheck, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useBackgroundAnalysis } from '../context/BackgroundAnalysisContext';
import { useNavigate } from 'react-router-dom';

type NotifState = 'analyzing' | 'completed' | 'error' | 'hidden';

export const AnalysisNotification = () => {
  const bgAnalysis = useBackgroundAnalysis();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [minimized, setMinimized] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [state, setState] = useState<NotifState>('hidden');
  const [fileName, setFileName] = useState('');
  const prevAnalyzingRef = useRef(false);
  const autoDismissRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Analysis started
    if (bgAnalysis.isAnalyzing && !prevAnalyzingRef.current) {
      setState('analyzing');
      setFileName(bgAnalysis.fileName);
      setDismissed(false);
      setMinimized(false);
      if (autoDismissRef.current) clearTimeout(autoDismissRef.current);
    }

    // Analysis finished (was analyzing, now not)
    if (!bgAnalysis.isAnalyzing && prevAnalyzingRef.current) {
      if (bgAnalysis.error) {
        setState('error');
      } else {
        setState('completed');
      }
      // Auto-dismiss after 5 seconds
      autoDismissRef.current = setTimeout(() => {
        setDismissed(true);
      }, 5000);
    }

    prevAnalyzingRef.current = bgAnalysis.isAnalyzing;
  }, [bgAnalysis.isAnalyzing, bgAnalysis.error, bgAnalysis.fileName]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (autoDismissRef.current) clearTimeout(autoDismissRef.current);
    };
  }, []);

  // Error appeared while not analyzing
  useEffect(() => {
    if (bgAnalysis.error && !bgAnalysis.isAnalyzing && state === 'hidden') {
      setState('error');
      setDismissed(false);
      autoDismissRef.current = setTimeout(() => setDismissed(true), 5000);
    }
  }, [bgAnalysis.error]);

  const handleDismiss = () => {
    setDismissed(true);
    if (autoDismissRef.current) clearTimeout(autoDismissRef.current);
    if (state === 'completed') bgAnalysis.dismissResult();
    if (state === 'error') bgAnalysis.clearError();
  };

  // Nothing to show
  if (dismissed || state === 'hidden') return null;

  // Show real WebSocket progress if available, otherwise upload progress (capped at 10%)
  const wsPercent = bgAnalysis.progress.percent;
  const uploadPercent = bgAnalysis.uploadProgress;
  const percent = wsPercent > 0 ? wsPercent : Math.min(uploadPercent, 10) || 2;
  const message = bgAnalysis.progress.message
    || (uploadPercent > 0 && uploadPercent < 100 ? (t('analyses.uploading') || 'Uploading file...') : t('analyses.analyzing'));

  const isAnalyzing = state === 'analyzing';
  const isCompleted = state === 'completed';
  const isError = state === 'error';

  // Colors based on state using CSS variables
  const stateColors = isCompleted
    ? { border: 'var(--success)', bg: 'var(--success-bg)', text: 'var(--success)', bar: 'var(--success)' }
    : isError
      ? { border: 'var(--danger)', bg: 'var(--danger-bg)', text: 'var(--danger)', bar: 'var(--danger)' }
      : { border: 'var(--accent)', bg: 'var(--accent-subtle)', text: 'var(--accent)', bar: 'var(--accent)' };

  const titleText = isCompleted
    ? (t('analyses.completed') || 'Completed')
    : isError
      ? (t('analyses.failed') || 'Failed')
      : (t('analyses.analyzing') || 'Analyzing');

  const statusMessage = isCompleted
    ? (t('analyses.analysisComplete') || 'Analysis complete')
    : isError
      ? (bgAnalysis.error || 'Analysis failed')
      : message;

  return (
    <AnimatePresence>
      <motion.div
        key="analysis-notification"
        initial={{ opacity: 0, y: -20, x: 20 }}
        animate={{ opacity: 1, y: 0, x: 0 }}
        exit={{ opacity: 0, y: -20, x: 20 }}
        className="fixed top-4 right-4 z-50"
      >
        <div
          className={`backdrop-blur-xl rounded-2xl shadow-2xl border overflow-hidden transition-all duration-300 ${minimized ? 'w-64' : 'w-80'}`}
          style={{
            background: 'var(--card)',
            borderColor: stateColors.border,
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-2.5"
            style={{ background: stateColors.bg }}
          >
            <div
              className="flex items-center gap-2 cursor-pointer flex-1 min-w-0"
              onClick={() => navigate('/analyses')}
            >
              <div className="relative">
                {isAnalyzing && <Loader2 className="w-4 h-4 animate-spin" style={{ color: stateColors.text }} />}
                {isCompleted && <BadgeCheck className="w-4 h-4" style={{ color: stateColors.text }} />}
                {isError && <AlertCircle className="w-4 h-4" style={{ color: stateColors.text }} />}
              </div>
              <span
                className="text-xs font-bold uppercase tracking-wide"
                style={{ color: stateColors.text }}
              >
                {titleText}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {isAnalyzing && (
                <button
                  onClick={() => setMinimized(!minimized)}
                  className="p-1 rounded-lg transition-colors"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {minimized ? (
                    <ChevronDown className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronUp className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
              <button
                onClick={handleDismiss}
                className="p-1 rounded-lg transition-colors"
                style={{ color: 'var(--text-faint)' }}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Body */}
          <AnimatePresence>
            {!minimized && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="px-4 py-3">
                  {/* File info */}
                  <div className="flex items-center gap-2 mb-3">
                    <FileType2 className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-faint)' }} />
                    <span className="text-sm truncate font-medium" style={{ color: 'var(--text)' }}>
                      {fileName || bgAnalysis.fileName}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div
                    className="w-full h-2 rounded-full overflow-hidden mb-2"
                    style={{ background: 'var(--card-border)' }}
                  >
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: stateColors.bar }}
                      initial={{ width: 0 }}
                      animate={{ width: `${isCompleted || isError ? 100 : percent}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>

                  {/* Status text */}
                  <div className="flex items-center justify-between">
                    <p className="text-xs truncate flex-1" style={{ color: 'var(--text-muted)' }}>
                      {statusMessage}
                    </p>
                    {isAnalyzing && (
                      <span
                        className="text-xs font-semibold ml-2"
                        style={{ color: stateColors.text }}
                      >
                        {Math.round(percent)}%
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Minimized: just show progress bar */}
          {minimized && isAnalyzing && (
            <div className="px-4 py-2">
              <div className="flex items-center gap-2">
                <div
                  className="flex-1 h-1.5 rounded-full overflow-hidden"
                  style={{ background: 'var(--card-border)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ background: stateColors.bar, width: `${percent}%` }}
                  />
                </div>
                <span
                  className="text-[10px] font-bold"
                  style={{ color: stateColors.text }}
                >
                  {Math.round(percent)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
