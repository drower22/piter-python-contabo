import { format, startOfWeek, endOfWeek, subWeeks } from 'date-fns';
import { cn } from '@/lib/utils';

interface WeekSelectorProps {
  selectedWeekIndex: number;
  onWeekChange: (index: number) => void;
  className?: string;
  weekCount?: number;
}

export function WeekSelector({
  selectedWeekIndex,
  onWeekChange,
  className,
  weekCount = 8
}: WeekSelectorProps) {
  const getWeekLabel = (index: number) => {
    const today = new Date();
    const targetDate = subWeeks(today, index);
    const start = startOfWeek(targetDate, { weekStartsOn: 1 });
    const end = endOfWeek(targetDate, { weekStartsOn: 1 });
    
    if (index === 0) return `Esta semana (${format(start, 'dd/MM')} - ${format(end, 'dd/MM')})`;
    if (index === 1) return `Semana passada (${format(start, 'dd/MM')} - ${format(end, 'dd/MM')})`;
    return `Semana ${format(start, 'dd/MM')} - ${format(end, 'dd/MM')}`;
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onWeekChange(Number(e.target.value));
  };

  return (
    <select
      value={selectedWeekIndex}
      onChange={handleChange}
      className={cn(
        'w-[280px] p-2 rounded-md border border-gray-300 bg-gray-50',
        'focus:outline-none focus:ring-2 focus:ring-brand-purple-dark',
        className
      )}
    >
      {Array.from({ length: weekCount }).map((_, index) => (
        <option key={index} value={index}>
          {getWeekLabel(index)}
        </option>
      ))}
    </select>
  );
}
