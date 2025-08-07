import type { Summary } from '../types';
import { Button } from '@/shared/components/ui/button';
import { Clock, Eye } from 'lucide-react';

interface SummaryCardProps {
  summary: Summary;
  onSchedule: (id: string) => void;
  onView: (summary: Summary) => void;
}

export function SummaryCard({ summary, onSchedule, onView }: SummaryCardProps) {
  return (
    <div className="bg-white border rounded-lg shadow-sm p-6 flex items-center justify-between gap-4">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <h3 className="font-sora text-lg font-semibold text-brand-black-charcoal">{summary.title}</h3>
          <button onClick={() => onView(summary)} className="text-gray-400 hover:text-brand-purple transition-colors">
            <Eye className="w-4 h-4" />
          </button>
        </div>
        <p className="text-gray-600 mt-1 text-sm">{summary.description}</p>
      </div>
      <div className="flex flex-shrink-0">
        <Button onClick={() => onSchedule(summary.id)}>
          <Clock className="w-4 h-4 mr-2" />
          Agendar
        </Button>
      </div>
    </div>
  );
}
