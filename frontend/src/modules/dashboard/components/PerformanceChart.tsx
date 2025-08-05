import { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MultiSelectDropdown } from '../../../shared/components/ui/multiselect-dropdown';
import { last30DaysData, kpiOptions, weekDays } from '../data/chart.data';

const colors = ['#4B1F6F', '#FFD53D', '#BDA3E1', '#222222', '#00C49F', '#FFBB28', '#FF8042'];

export function PerformanceChart() {
  const [selectedKpis, setSelectedKpis] = useState(['Faturamento Total', 'Ticket Médio']);
  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>([]);

  const filteredData = useMemo(() => {
    if (selectedWeekdays.length === 0) {
      return last30DaysData;
    }
    return last30DaysData.filter(d => selectedWeekdays.includes(d.weekday));
  }, [selectedWeekdays]);

  const handleDaySelect = (dayId: string) => {
    setSelectedWeekdays(prev =>
      prev.includes(dayId) ? prev.filter(d => d !== dayId) : [...prev, dayId]
    );
  };

  const getBrandColor = (index: number) => {
    return colors[index % colors.length];
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm mt-8 animate-fade-in-up">
      <div className="flex flex-col md:flex-row justify-between md:items-center mb-6">
        <h3 className="font-sora text-lg font-semibold text-brand-black-charcoal mb-4 md:mb-0">Performance dos Últimos 30 Dias</h3>
        <div className="w-full md:w-auto">
          <MultiSelectDropdown
            options={kpiOptions.map(kpi => ({ value: kpi.id, label: kpi.name }))}
            selected={selectedKpis}
            onChange={setSelectedKpis}
            placeholder="Selecionar KPIs"
          />
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 mb-6">
        {weekDays.map(day => (
          <button
            key={day.id}
            onClick={() => handleDaySelect(day.id)}
            className={`font-inter font-semibold text-xs w-8 h-8 rounded-full transition-colors ${selectedWeekdays.includes(day.id) ? 'bg-brand-purple text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
            {day.label}
          </button>
        ))}
      </div>

      <div style={{ width: '100%', height: 400 }}>
        <ResponsiveContainer>
          <LineChart data={filteredData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {selectedKpis.map((kpiId, index) => {
              const kpi = kpiOptions.find(k => k.id === kpiId)!;
              return <Line key={kpi.id} type="monotone" dataKey={kpi.id} stroke={getBrandColor(index)} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }}/>; 
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
