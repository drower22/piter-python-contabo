/**
 * @file useUploadHistory.ts
 * @description Hook customizado para buscar e gerenciar o histórico de uploads.
 */
import { useState, useEffect } from 'react';
import { getUploadHistory } from '../services/historyService';
import type { UploadHistoryItem } from '../services/historyService';

export function useUploadHistory() {
  const [history, setHistory] = useState<UploadHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getUploadHistory();
        setHistory(data);
      } catch (err) {
        setError('Não foi possível carregar o histórico.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchHistory();
  }, []); // Executa apenas uma vez, na montagem do componente

  return { history, isLoading, error };
}
