import { useSummaries } from '../hooks/useSummaries';
import { useState } from 'react';
import { SummaryCard } from './SummaryCard';
import { Skeleton } from '@/shared/components/ui/skeleton';
import { ViewSummaryModal } from './ViewSummaryModal';
import { ScheduleModal } from './ScheduleModal';
import type { Summary } from '../types';

export function SummaryList() {
  const { summaries, isLoading, error } = useSummaries();
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);

  const handleScheduleClick = (summaryId: string) => {
    const summaryToSchedule = summaries.find(s => s.id === summaryId);
    if (summaryToSchedule) {
      setSelectedSummary(summaryToSchedule);
      setIsScheduleModalOpen(true);
    }
  };

  const handleConfirmSchedule = (day: string, time: string) => {
    if (selectedSummary) {
      alert(`Resumo "${selectedSummary.title}" agendado para ${day} às ${time}`);
      // Aqui você chamaria o serviço de backend para salvar o agendamento
    }
  };

  const handleView = (summary: Summary) => {
    setSelectedSummary(summary);
    setIsViewModalOpen(true);
  };

  const handleCloseModals = () => {
    setIsViewModalOpen(false);
    setIsScheduleModalOpen(false);
    setSelectedSummary(null);
  };

  

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="bg-white border rounded-lg p-6 flex items-center justify-between">
            <div className="flex-1 pr-4">
              <Skeleton className="h-6 w-1/2 mb-2" />
              <Skeleton className="h-4 w-3/4" />
            </div>
            <div className="flex gap-3">
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-32" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-red-500 bg-red-100 border border-red-400 rounded p-4">{error}</p>;
  }

  return (
    <>
      <div className="space-y-4">
        {summaries.map((summary) => (
          <SummaryCard 
            key={summary.id} 
            summary={summary} 
            onSchedule={handleScheduleClick} 
            onView={handleView}
          />
        ))}
      </div>

      <ViewSummaryModal 
        isOpen={isViewModalOpen}
        summary={selectedSummary}
        onClose={handleCloseModals}
      />

      <ScheduleModal 
        isOpen={isScheduleModalOpen}
        onClose={handleCloseModals}
        onSchedule={handleConfirmSchedule}
      />
    </>
  );
}
