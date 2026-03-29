import { useEffect, useState, useCallback } from 'react';
import { analysesAPI } from '../services/api';

interface AnalysisUpdate {
  type: 'analysis_update';
  analysis_id: number;
  status: string;
  timestamp: string;
  [key: string]: any;
}

/**
 * Hook to get real-time analysis updates via polling
 * Polls the server every few seconds to check for analysis status changes
 */
export function useAnalysisUpdates(onUpdate?: (update: AnalysisUpdate) => void) {
  const [latestUpdate, setLatestUpdate] = useState<AnalysisUpdate | null>(null);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [isPolling, setIsPolling] = useState(false);

  const pollAnalyses = useCallback(async () => {
    try {
      const data = await analysesAPI.getAll();
      setAnalyses(data);

      // Check for status changes and trigger updates
      if (data.length > 0) {
        const latestAnalysis = data[0];
        const update: AnalysisUpdate = {
          type: 'analysis_update',
          analysis_id: latestAnalysis.id,
          status: latestAnalysis.status,
          timestamp: latestAnalysis.updated_at || new Date().toISOString(),
        };

        setLatestUpdate(update);

        if (onUpdate) {
          onUpdate(update);
        }
      }
    } catch (error) {
      console.error('Failed to poll analyses:', error);
    }
  }, [onUpdate]);

  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!isPolling) return;

    // Poll immediately on start
    pollAnalyses();

    // Then poll every 5 seconds
    const interval = setInterval(pollAnalyses, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [isPolling, pollAnalyses]);

  return {
    latestUpdate,
    analyses,
    isPolling,
    startPolling,
    stopPolling,
    refresh: pollAnalyses,
  };
}
