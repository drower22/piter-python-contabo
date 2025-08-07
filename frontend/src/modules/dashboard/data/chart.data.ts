// @file: src/modules/dashboard/data/chart.data.ts
// @description: Mock data and configurations for the dashboard charts.

// --- Mock Data Generation ---
const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'] as const;

export const last30DaysData = Array.from({ length: 30 }).map((_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - i);
  return {
    date: date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    fullDate: date,
    weekday: weekdays[date.getDay()],
    faturamentoTotal: Math.floor(Math.random() * (2500 - 1500 + 1)) + 1500,
    ticketMedio: Math.floor(Math.random() * (120 - 80 + 1)) + 80,
    totalPedidos: Math.floor(50 + Math.random() * 30 - (i * 0.5)),
    taxasIfood: 360 + Math.random() * 90 - (i * 2),
    anunciosPagos: 50 + Math.random() * 20,
    incentivosIfood: 80 + Math.random() * 30,
    incentivosLoja: 60 + Math.random() * 25,
    entregasLoja: 20 + Math.random() * 10,
    taxasEntregadores: 120 + Math.random() * 40,
  };
}).reverse();

// --- Chart Configurations ---
export const kpiOptions = [
  { id: 'faturamentoTotal', name: 'Faturamento Total' },
  { id: 'ticketMedio', name: 'Ticket Médio' },
  { id: 'totalPedidos', name: 'Total de Pedidos' },
  { id: 'taxasIfood', name: 'Taxas iFood' },
  { id: 'anunciosPagos', name: 'Anúncios Pagos' },
  { id: 'incentivosIfood', name: 'Incentivos iFood' },
  { id: 'incentivosLoja', name: 'Incentivos Loja' },
  { id: 'entregasLoja', name: 'Entregas Loja' },
  { id: 'taxasEntregadores', name: 'Taxas Entregadores' },
];

export const weekDays = [
  { id: 'Dom', label: 'domingo' },
  { id: 'Seg', label: 'segunda' },
  { id: 'Ter', label: 'terça' },
  { id: 'Qua', label: 'quarta' },
  { id: 'Qui', label: 'quinta' },
  { id: 'Sex', label: 'sexta' },
  { id: 'Sáb', label: 'sábado' },
];
