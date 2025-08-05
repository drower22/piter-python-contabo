// @file: src/modules/dashboard/data/chart.data.ts
// @description: Mock data and configurations for the dashboard charts.

// --- Mock Data Generation ---
export const last30DaysData = Array.from({ length: 30 }).map((_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - i);
  return {
    date: date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    weekday: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'][date.getDay()],
    'Faturamento Total': 2000 + Math.random() * 500 - (i * 10),
    'Ticket Médio': 85 + Math.random() * 10,
    'Total de Pedidos': Math.floor(50 + Math.random() * 30 - (i * 0.5)),
    'Taxas iFood': 360 + Math.random() * 90 - (i * 2),
    'Anúncios Pagos': 50 + Math.random() * 20,
    'Incentivos iFood': 80 + Math.random() * 30,
    'Incentivos Loja': 60 + Math.random() * 25,
    'Entregas Loja': 20 + Math.random() * 10,
    'Taxas Entregadores': 120 + Math.random() * 40,
  };
}).reverse();

// --- Chart Configurations ---
export const kpiOptions = [
  { id: 'Faturamento Total', name: 'Faturamento Total' },
  { id: 'Ticket Médio', name: 'Ticket Médio' },
  { id: 'Total de Pedidos', name: 'Total de Pedidos' },
  { id: 'Taxas iFood', name: 'Taxas iFood' },
  { id: 'Anúncios Pagos', name: 'Anúncios Pagos' },
  { id: 'Incentivos iFood', name: 'Incentivos iFood' },
  { id: 'Incentivos Loja', name: 'Incentivos Loja' },
  { id: 'Entregas Loja', name: 'Entregas Loja' },
  { id: 'Taxas Entregadores', name: 'Taxas Entregadores' },
];

export const weekDays = [
  { id: 'Seg', label: 'S' },
  { id: 'Ter', label: 'T' },
  { id: 'Qua', label: 'Q' },
  { id: 'Qui', label: 'Q' },
  { id: 'Sex', label: 'S' },
  { id: 'Sáb', label: 'S' },
  { id: 'Dom', label: 'D' },
];
