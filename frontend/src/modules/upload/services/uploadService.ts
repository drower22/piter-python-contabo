/**
 * @file uploadService.ts
 * @description Serviço para lidar com as chamadas de API de upload.
 */

/**
 * Simula o upload de arquivos para o backend.
 * @param files - A lista de arquivos para enviar.
 */
export async function uploadFiles(
  files: File[]
): Promise<{ success: boolean; message: string }> {
  console.log('Iniciando upload simulado de', files.length, 'arquivos...');

  // Simula uma chamada de API que leva 2 segundos
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Em um caso real, aqui você usaria fetch() ou axios para enviar os arquivos
  // e trataria a resposta do servidor.
  console.log('Upload simulado concluído.');
  
  // Simula uma resposta de sucesso da API
  return {
    success: true,
    message: 'Arquivos enviados com sucesso!',
  };
}
