import { useState, useEffect, useCallback } from 'react';
import type { Summary } from '../types';
import { summariesService } from '../services/summariesService';

export function useSummaries() {
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummaries = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await summariesService.getSummaries();
      setSummaries(data);
    } catch (err) {
      setError('Falha ao buscar os resumos. Tente novamente mais tarde.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummaries();
  }, [fetchSummaries]);

  return { summaries, isLoading, error, refetch: fetchSummaries, setSummaries };
}
