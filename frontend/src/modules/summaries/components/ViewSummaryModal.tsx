import { Button } from '@/shared/components/ui/button';
import type { Summary } from '../types';

interface ViewSummaryModalProps {
  isOpen: boolean;
  summary: Summary | null;
  onClose: () => void;
}

export function ViewSummaryModal({ isOpen, summary, onClose }: ViewSummaryModalProps) {
  if (!isOpen || !summary) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md transform transition-all">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold font-sora text-brand-black-charcoal">{summary.title}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <p className="text-gray-800 whitespace-pre-wrap">{summary.content}</p>
        </div>
        <div className="mt-6 flex justify-end">
          <Button onClick={onClose}>Fechar</Button>
        </div>
      </div>
    </div>
  );
}
