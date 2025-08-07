import { cn } from '@/lib/utils';

type DashboardFiltersProps = {
  filterType: 'performance' | 'financial';
  onFilterTypeChange: (type: 'performance' | 'financial') => void;
};

export function DashboardFilters({ filterType, onFilterTypeChange }: DashboardFiltersProps) {
  const tabs = [
    { id: 'performance', label: 'Desempenho' },
    { id: 'financial', label: 'Financeiro' },
  ];

  return (
    <div className="flex border-b">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onFilterTypeChange(tab.id as 'performance' | 'financial')}
          className={cn(
            'py-2 px-4 text-sm font-medium focus:outline-none',
            filterType === tab.id
              ? 'border-b-2 border-brand-purple-500 text-brand-purple-500'
              : 'text-gray-500 hover:text-gray-700'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

