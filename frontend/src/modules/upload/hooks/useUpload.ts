/**
 * @file useUpload.ts
 * @description Hook customizado para gerenciar o estado e a lógica do upload de arquivos.
 */
import { useState } from 'react';
import { uploadFiles } from '../services/uploadService';

export type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export function useUpload() {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  async function executeUpload(files: File[]) {
    if (files.length === 0) return;

    setStatus('uploading');
    setError(null);

    try {
      const response = await uploadFiles(files);
      if (response.success) {
        setStatus('success');
      } else {
        setStatus('error');
        setError(response.message);
      }
    } catch (err) {
      setStatus('error');
      setError('Ocorreu um erro inesperado ao enviar os arquivos.');
      console.error(err);
    }
  }
  
  function resetStatus() {
    setStatus('idle');
    setError(null);
  }

  return { status, error, executeUpload, resetStatus };
}
