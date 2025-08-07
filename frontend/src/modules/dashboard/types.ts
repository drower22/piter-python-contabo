// Centralized type definitions for the Dashboard module

export interface WeeklyFinancials {
  weekLabel: string;
  totalPedidos: number;
  ticketMedio: number;
  online: {
    gross: number;
    ifoodFees: number;
    ifoodIncentives: number;
    net: number;
    anunciosPagos: number;
    taxasEntregadores: number;
    methods: {
      credit: number;
      debit: number;
      pix: number;
      voucher: number;
    };
  };
  direct: {
    total: number;
    incentivosLoja: number;
    entregasLoja: number;
    methods: {
      credit: number;
      debit: number;
      pix: number;
      cash: number;
    };
  };
  reconciliation: {
    status: 'pending' | 'reconciled';
    pendingItems: number;
    divergences: {
      id: string;
      description: string;
      type: 'Taxa incorreta' | 'Pedido não encontrado' | 'Valor divergente';
      amount: number;
      date: string;
    }[];
  };
}

export type Divergence = WeeklyFinancials['reconciliation']['divergences'][0];
