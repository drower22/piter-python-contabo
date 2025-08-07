/**
 * @file historyService.ts
 * @description Serviço para lidar com as chamadas de API do histórico de uploads.
 */

// Interface para o tipo de dado do histórico
export interface UploadHistoryItem {
  id: string;
  fileName: string;
  uploadDate: string;
  status: 'Concluído' | 'Processando' | 'Falhou';
  user: string;
}

// Dados mocados para a tabela
const mockUploads: UploadHistoryItem[] = [
  {
    id: 'UPLOAD-001',
    fileName: 'vendas_semana_42.xlsx',
    uploadDate: '2023-10-25 14:30',
    status: 'Concluído',
    user: 'ana.silva@example.com',
  },
  {
    id: 'UPLOAD-002',
    fileName: 'vendas_outubro.xlsx',
    uploadDate: '2023-10-24 10:15',
    status: 'Processando',
    user: 'carlos.santos@example.com',
  },
  {
    id: 'UPLOAD-003',
    fileName: 'relatorio_q3.xlsx',
    uploadDate: '2023-10-23 18:00',
    status: 'Falhou',
    user: 'ana.silva@example.com',
  },
  {
    id: 'UPLOAD-004',
    fileName: 'vendas_semana_41.xlsx',
    uploadDate: '2023-10-22 11:45',
    status: 'Concluído',
    user: 'bruno.melo@example.com',
  },
];

/**
 * Simula a busca do histórico de uploads.
 */
export async function getUploadHistory(): Promise<UploadHistoryItem[]> {
  console.log('Buscando histórico de uploads...');
  
  // Simula uma chamada de API que leva 1.5 segundos
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  console.log('Histórico de uploads recebido.');
  return mockUploads;
}
