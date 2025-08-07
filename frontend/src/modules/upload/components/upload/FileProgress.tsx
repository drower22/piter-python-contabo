/**
 * @file FileProgress.tsx
 * @description Componente para exibir o progresso de upload de um único arquivo.
 */
import { File, X } from 'lucide-react';

interface FileProgressProps {
  file: File;
  onRemove: (file: File) => void;
}

export function FileProgress({ file, onRemove }: FileProgressProps) {
  const fileSize = (file.size / 1024 / 1024).toFixed(2); // Converte para MB

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gray-200 rounded-full">
          <File className="w-5 h-5 text-gray-600" />
        </div>
        <div className="flex flex-col">
          <span className="font-inter font-medium text-sm text-brand-black-charcoal">{file.name}</span>
          <span className="font-inter text-xs text-gray-500">{fileSize} MB</span>
        </div>
      </div>
      <button onClick={() => onRemove(file)} className="text-gray-500 hover:text-red-500 transition-colors">
        <X className="w-5 h-5" />
      </button>
    </div>
  );
}
