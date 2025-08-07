/**
 * @file UploadArea.tsx
 * @description Componente de drag-and-drop para seleção de arquivos.
 */
import { UploadCloud } from 'lucide-react';
import { useRef, useState } from 'react';
import type { DragEvent } from 'react';

interface UploadAreaProps {
  onFilesSelected: (files: File[]) => void;
}

export function UploadArea({ onFilesSelected }: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFilesSelected(Array.from(files));
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      onFilesSelected(Array.from(files));
    }
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  }

  function handleClick() {
    fileInputRef.current?.click();
  }

  const dragDropClasses = isDragging
    ? 'border-brand-purple bg-purple-50'
    : 'border-gray-300';

  return (
    <div
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-brand-purple transition-colors duration-300 ${dragDropClasses}`}>
      <div className="flex flex-col items-center justify-center gap-4 text-gray-500 pointer-events-none">
        <UploadCloud className="w-12 h-12" />
        <p className="font-sora font-semibold text-lg">Arraste e solte os arquivos aqui</p>
        <p className="font-inter text-sm">ou <span className="text-brand-purple font-semibold">clique para selecionar</span>.</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileSelect}
          accept=".xls,.xlsx"
        />
        <p className="font-inter text-xs text-gray-400 mt-4">Suportado: .xls, .xlsx</p>
      </div>
    </div>
  );
}
