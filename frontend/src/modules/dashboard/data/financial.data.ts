import { format, startOfWeek, endOfWeek, subWeeks } from 'date-fns';
import type { WeeklyFinancials } from '../types';

// Função para gerar dados financeiros fictícios para uma semana
export const generateWeeklyData = (weekIndex: number): WeeklyFinancials => {
  const today = new Date();
  const targetDate = subWeeks(today, weekIndex);
  const from = startOfWeek(targetDate, { weekStartsOn: 1 });
  const to = endOfWeek(targetDate, { weekStartsOn: 1 });

  let label = `Semana de ${format(from, 'dd/MM')} a ${format(to, 'dd/MM')}`;
  if (weekIndex === 0) label = 'Esta semana';
  if (weekIndex === 1) label = 'Semana passada';

  const onlineGross = 5000 + Math.random() * 2000 - weekIndex * 300;
  const ifoodFees = onlineGross * (0.18 + Math.random() * 0.05);
  const ifoodIncentives = Math.random() * 500;
  const onlineNet = onlineGross - ifoodFees + ifoodIncentives;

  const directTotal = 2000 + Math.random() * 1000 - weekIndex * 150;

  const isPending = weekIndex <= 1;
  const pendingItems = isPending ? Math.floor(Math.random() * 3) + 1 : 0;
  const totalPedidos = Math.floor(150 + Math.random() * 50 - weekIndex * 10);

  return {
    weekLabel: label,
    totalPedidos,
    ticketMedio: (onlineGross + directTotal) / totalPedidos,
    online: {
      gross: onlineGross,
      ifoodFees,
      ifoodIncentives,
      net: onlineNet,
      anunciosPagos: onlineGross * 0.03,
      taxasEntregadores: onlineGross * 0.05,
      methods: {
        credit: onlineGross * 0.6,
        debit: onlineGross * 0.2,
        pix: onlineGross * 0.15,
        voucher: onlineGross * 0.05,
      },
    },
    direct: {
      total: directTotal,
      incentivosLoja: directTotal * 0.02,
      entregasLoja: directTotal * 0.08,
      methods: {
        credit: directTotal * 0.4,
        debit: directTotal * 0.3,
        pix: directTotal * 0.2,
        cash: directTotal * 0.1,
      },
    },
    reconciliation: {
      status: isPending ? 'pending' : 'reconciled',
      pendingItems,
      divergences: isPending
        ? Array.from({ length: pendingItems }, (_, i) => ({
            id: `div-${weekIndex}-${i}`,
            description: `Ajuste na taxa do pedido #${12345 + i}`,
            type: 'Taxa incorreta',
            amount: -(Math.random() * 10 + 5),
            date: format(subWeeks(new Date(), weekIndex), 'dd/MM/yyyy'),
          }))
        : [],
    },
  };
};

// Gerar dados para as últimas 8 semanas
export const weeklyFinancialData: WeeklyFinancials[] = Array.from({ length: 8 }, (_, i) => generateWeeklyData(i));
