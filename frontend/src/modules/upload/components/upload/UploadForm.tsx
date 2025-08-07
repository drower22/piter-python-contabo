/**
 * @file UploadForm.tsx
 * @description Formulário principal que orquestra o processo de upload.
 */
import { useState } from 'react';
import { UploadArea } from './UploadArea';
import { FileProgress } from './FileProgress';
import { Button } from '@/shared/components/ui/button';
import { useUpload } from '../../hooks/useUpload';
import { Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

export function UploadForm() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const { status, error, executeUpload, resetStatus } = useUpload();

  function handleFilesSelected(files: File[]) {
    // Evita arquivos duplicados pelo nome
    const newFiles = files.filter(
      (file) => !selectedFiles.some((existingFile) => existingFile.name === file.name)
    );
    setSelectedFiles((prevFiles) => [...prevFiles, ...newFiles]);
  }

  function handleRemoveFile(fileToRemove: File) {
    setSelectedFiles((prevFiles) => prevFiles.filter((file) => file !== fileToRemove));
  }

  async function handleUpload() {
    await executeUpload(selectedFiles);
  }

  return (
    <div className="flex flex-col gap-6">
      {status !== 'success' && <UploadArea onFilesSelected={handleFilesSelected} />}
      
      {status === 'success' && (
        <div className="flex flex-col items-center justify-center text-center p-8 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="w-12 h-12 text-green-500 mb-4" />
          <h3 className="font-sora font-semibold text-lg text-green-800">Upload Concluído!</h3>
          <p className="font-inter text-sm text-green-700">Seus arquivos foram enviados com sucesso.</p>
          <Button onClick={() => { resetStatus(); setSelectedFiles([]); }} className="mt-6">
            Enviar Novos Arquivos
          </Button>
        </div>
      )}

      {status === 'error' && (
        <div className="flex flex-col items-center justify-center text-center p-8 bg-red-50 border border-red-200 rounded-lg">
          <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
          <h3 className="font-sora font-semibold text-lg text-red-800">Erro no Upload</h3>
          <p className="font-inter text-sm text-red-700">{error}</p>
          <Button onClick={resetStatus} variant="destructive" className="mt-6">
            Tentar Novamente
          </Button>
        </div>
      )}

      {selectedFiles.length > 0 && status !== 'success' && status !== 'error' && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-3">
            <h3 className="font-sora font-semibold text-lg text-brand-black-charcoal">Arquivos Selecionados</h3>
            {selectedFiles.map((file) => (
              <FileProgress key={file.name} file={file} onRemove={handleRemoveFile} />
            ))}
          </div>

          <Button onClick={handleUpload} disabled={selectedFiles.length === 0 || status === 'uploading'} className="w-full md:w-auto md:self-end">
            {status === 'uploading' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {status === 'uploading' ? 'Enviando...' : 'Enviar Arquivos'}
          </Button>
        </div>
      )}
    </div>
  );
}
