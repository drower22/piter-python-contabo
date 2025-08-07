import { Button } from '@/shared/components/ui/button';
import { Textarea } from '@/shared/components/ui/textarea';
import type { Summary } from '../types';
import { useEffect, useState } from 'react';

interface EditSummaryModalProps {
  summary: Summary | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (summaryId: string, updatedContent: string) => void;
}

export function EditSummaryModal({ summary, isOpen, onClose, onSave }: EditSummaryModalProps) {
  const [content, setContent] = useState('');

  useEffect(() => {
    if (summary) {
      setContent(summary.content);
    } else {
      setContent('');
    }
  }, [summary]);

  if (!isOpen || !summary) {
    return null;
  }

  const handleSave = () => {
    onSave(summary.id, content);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl transform transition-all">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold font-sora text-brand-black-charcoal">Editar Mensagem do Resumo</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <p className="mb-4 text-sm text-gray-600">
          Você está editando o modelo: <span className="font-semibold text-brand-purple">{summary.title}</span>
        </p>
        <Textarea 
          value={content}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setContent(e.target.value)}
          className="h-48 text-base"
          placeholder="Digite a mensagem do resumo aqui..."
        />
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            Salvar Alterações
          </Button>
        </div>
      </div>
    </div>
  );
}
