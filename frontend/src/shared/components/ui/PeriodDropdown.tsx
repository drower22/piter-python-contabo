import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../../lib/utils';


const PERIOD_PRESETS = [
  { label: 'Últimos 7 dias', value: '7' },
  { label: 'Últimos 30 dias', value: '30' },
  { label: 'Últimos 60 dias', value: '60' },
  { label: 'Últimos 90 dias', value: '90' },
  { label: 'Personalizado', value: 'custom' },
];

interface PeriodDropdownProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function PeriodDropdown({ value, onChange, className }: PeriodDropdownProps) {
  const [open, setOpen] = useState(false);
  const selected = PERIOD_PRESETS.find(p => p.value === value);

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        className={cn(
          'w-full min-w-[180px] flex items-center justify-between rounded-md border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-purple-dark',
          open && 'ring-2 ring-brand-purple-dark'
        )}
        onClick={() => setOpen(o => !o)}
      >
        <span>{selected?.label || 'Selecione o período'}</span>
        <ChevronDown size={18} />
      </button>
      {open && (
        <ul className="absolute z-10 mt-2 w-full bg-white border rounded-md shadow-lg py-1 animate-fade-in">
          {PERIOD_PRESETS.map(opt => (
            <li
              key={opt.value}
              className={cn(
                'px-4 py-2 text-sm cursor-pointer hover:bg-gray-100',
                value === opt.value && 'bg-brand-purple-light text-brand-purple-dark font-semibold'
              )}
              onClick={() => {
                setOpen(false);
                onChange(opt.value);
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
