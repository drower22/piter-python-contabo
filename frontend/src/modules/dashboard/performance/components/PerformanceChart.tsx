import { useState, useMemo } from 'react';
import { type DateRange } from '@/shared/components/ui/DateRangePicker';
import { isWithinInterval } from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { LineChart, Line, XAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SimpleMultiSelect } from '@/shared/components/ui/simple-multiselect';
import { last30DaysData, kpiOptions, weekDays } from '@/modules/dashboard/data/chart.data';

// --- Interfaces ---
interface ChartData {
  date: string;
  fullDate: Date;
  weekday: 'Dom' | 'Seg' | 'Ter' | 'Qua' | 'Qui' | 'Sex' | 'Sáb';
  faturamentoTotal: number;
  ticketMedio: number;
  totalPedidos: number;
  taxasIfood: number;
  anunciosPagos: number;
  incentivosIfood: number;
  incentivosLoja: number;
  entregasLoja: number;
  taxasEntregadores: number;
}

interface KpiOption {
  id: string;
  name: string;
}

interface WeekDay {
  id: string;
  label: string;
}

const colors = ['#4B1F6F', '#FFD53D', '#BDA3E1', '#6B7280', '#00C49F', '#FFBB28', '#FF8042'];

// Definição de tipos para o CustomTooltip
interface CustomTooltipPayload {
  color?: string;
  name?: string;
  value?: number | string;
  payload?: ChartData;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: CustomTooltipPayload[];
  label?: string;
}

// Custom tooltip para o gráfico
function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const dataPoint = payload[0].payload;
  if (!dataPoint) return null;

  const weekday = dataPoint.weekday ? dataPoint.weekday.substring(0, 3).toLowerCase() : '';

  return (
    <div className="rounded-xl shadow-lg border border-gray-200 bg-white px-4 py-2 min-w-[180px] animate-fade-in">
      <div className="text-xs font-semibold text-gray-700 mb-1">{label} ({weekday})</div>
      {payload.map((entry, index: number) => (
        <div key={`item-${index}`} className="flex items-center gap-2 mb-1">
          <span style={{ background: entry.color, width: 10, height: 10, borderRadius: '50%', display: 'inline-block' }} />
          <span className="font-medium text-xs" style={{ color: entry.color }}>{entry.name}:</span>
          <span className="font-bold text-xs ml-1 text-gray-800">
            {typeof entry.value === 'number' ? entry.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

interface PerformanceChartProps {
  dateRange: DateRange | undefined;
}

export function PerformanceChart({ dateRange }: PerformanceChartProps) {
  const [selectedKpis, setSelectedKpis] = useState(['faturamentoTotal', 'ticketMedio']);
  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>([]);
  const chartData: ChartData[] = useMemo(() => {
    if (!dateRange?.from || !dateRange?.to) {
      return last30DaysData; // Retorna todos se não houver período
    }
    return last30DaysData.filter((d: ChartData) => 
      isWithinInterval(d.fullDate, { start: dateRange.from!, end: dateRange.to! })
    );
  }, [dateRange]);

  // 1. Encontrar semanas completas (Dom-Sáb) nos dados filtrados
  const weekStartIndexes = useMemo(() => {
    const indexes: number[] = [];
    for (let i = 0; i <= chartData.length - 7; i++) {
      if (chartData[i].weekday === 'Dom') {
        indexes.push(i);
      }
    }
    return indexes;
  }, [chartData]);

  const [windowStart, setWindowStart] = useState(weekStartIndexes.length > 0 ? weekStartIndexes[weekStartIndexes.length - 1] : 0);

  // Filtrar os dados da janela visível pelos dias da semana selecionados
  const visibleData: ChartData[] = useMemo(() => {
    if (chartData.length === 0) return [];
    const currentWindow = chartData.slice(windowStart, windowStart + 7);
    if (selectedWeekdays.length === 0) {
      return currentWindow;
    }
    return currentWindow.filter((d: ChartData) => selectedWeekdays.includes(d.weekday));
  }, [windowStart, selectedWeekdays, chartData]);

  const minWindowStart = weekStartIndexes.length > 0 ? weekStartIndexes[0] : 0;
  const maxWindowStart = weekStartIndexes.length > 0 ? weekStartIndexes[weekStartIndexes.length - 1] : 0;

  // Dropdown de dias da semana
  const weekdayOptions = weekDays.map((w: WeekDay) => ({ value: w.id, label: w.label }));

  const getBrandColor = (index: number) => {
    return colors[index % colors.length];
  };

  // Navegação: sempre pula de semana fechada (segunda a domingo)
  const handlePrev = () => {
    let prevIndex: number | undefined = undefined;
    for (let j = weekStartIndexes.length - 1; j >= 0; j--) {
      if (weekStartIndexes[j] < windowStart) {
        prevIndex = weekStartIndexes[j];
        break;
      }
    }
    if (typeof prevIndex === 'number') setWindowStart(prevIndex);
  };
  const handleNext = () => {
    let nextIndex: number | undefined = undefined;
    for (let j = 0; j < weekStartIndexes.length; j++) {
      if (weekStartIndexes[j] > windowStart) {
        nextIndex = weekStartIndexes[j];
        break;
      }
    }
    if (typeof nextIndex === 'number') setWindowStart(nextIndex);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm animate-fade-in-up">
      <div className="flex flex-col md:flex-row gap-4 md:items-end md:justify-between mb-6">
        <div className="flex flex-col md:flex-row gap-4 w-full">
          <div className="flex-1 min-w-[200px]">
                        <label className="block text-xs font-semibold text-gray-500 mb-1">Indicadores</label>
            <SimpleMultiSelect
              options={kpiOptions.map((kpi: KpiOption) => ({ value: kpi.id, label: kpi.name }))}
              selected={selectedKpis}
              onChange={setSelectedKpis}
              placeholder="Selecione até 4 indicadores"
              maxSelection={4}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
                        <label className="block text-xs font-semibold text-gray-500 mb-1">Dias da semana</label>
            <SimpleMultiSelect
              options={weekdayOptions}
              selected={selectedWeekdays}
              onChange={setSelectedWeekdays}
              placeholder="Filtrar dias da semana"
              useSingleColor
            />
          </div>
        </div>
      </div>



      <div className="relative" style={{ width: '100%', height: 400 }}>
        {/* Botão de voltar */}
        <button
          onClick={handlePrev}
          disabled={windowStart <= minWindowStart}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 flex items-center justify-center rounded-full bg-[#E9D5FF] text-[#7c3aed] shadow-md hover:bg-[#C4B5FD] hover:text-[#4B1F6F] transition disabled:opacity-40"
          title="Voltar"
          aria-label="Voltar"
        >
          <ChevronLeft size={28} />
        </button>
        {/* Botão de avançar */}
        <button
          onClick={handleNext}
          disabled={windowStart >= maxWindowStart}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 flex items-center justify-center rounded-full bg-[#E9D5FF] text-[#7c3aed] shadow-md hover:bg-[#C4B5FD] hover:text-[#4B1F6F] transition disabled:opacity-40"
          title="Avançar"
          aria-label="Avançar"
        >
          <ChevronRight size={28} />
        </button>
        <div className="px-8 md:px-12"> {/* padding para não sobrepor o gráfico */}
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={visibleData} margin={{ top: 10, right: 30, left: 30, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={({ x, y, payload, index }) => {
                  const item = visibleData[index];
                  const weekday = item && item.weekday ? item.weekday.substring(0, 3).toLowerCase() : '';
                  return (
                    <g transform={`translate(${x},${y})`}>
                                            <text x={0} y={-4} textAnchor="middle" fontSize={13} fill="#6B7280">
                        {payload.value}
                      </text>
                      <text x={0} y={12} textAnchor="middle" fontSize={11} fill="#7c3aed">
                        {weekday}
                      </text>
                    </g>
                  );
                }}
              />
                            <Tooltip content={<CustomTooltip />} />
              <Legend />
              {selectedKpis.map((kpiId, index) => {
                const kpi = kpiOptions.find((k: KpiOption) => k.id === kpiId)!;
                return <Line key={kpi.id} name={kpi.name} type="monotone" dataKey={kpi.id} stroke={getBrandColor(index)} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }}/>; 
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
