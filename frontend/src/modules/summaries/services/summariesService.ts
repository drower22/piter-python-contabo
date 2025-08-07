import type { Summary } from '../types';

const mockSummaries: Summary[] = [
  {
    id: '1',
    title: 'Resumo de Terça-feira: Ticket Médio',
    description: 'Análise detalhada sobre o ticket médio de suas vendas recentes.',
    content: 'Ticket médio de ontem: R$ [Valor]. Esse valor representa a média de compras realizadas na loja.'
  },
  {
    id: '2',
    title: 'Resumo de Quarta-feira: Repasse Financeiro',
    description: 'Informações sobre o status e os valores do seu próximo repasse.',
    content: 'O próximo repasse será de R$ [Valor], programado para [Data]. Esse valor corresponde às vendas realizadas no período.'
  },
  {
    id: '3',
    title: 'Resumo de Quinta-feira: Performance de Cupons',
    description: 'Análise de como seus cupons de desconto estão performando.',
    content: 'Os cupons desta semana geraram R$ [Valor] em vendas. O cupom mais utilizado foi: [Nome do Cupom].'
  },
  {
    id: '4',
    title: 'Resumo de Sexta-feira: Destaques da Semana',
    description: 'Descubra quais produtos e estratégias mais se destacaram na semana.',
    content: 'Produto destaque da semana: [Produto], com [X] vendas. Esse foi o item mais vendido no período.'
  }
];

export const summariesService = {
  getSummaries: async (): Promise<Summary[]> => {
    console.log('Fetching summaries...');
    // Simula um delay da API
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('Summaries fetched!');
    return mockSummaries;
  },

  sendNow: async (summaryId: string): Promise<{ success: boolean }> => {
    console.log(`Sending summary ${summaryId} now...`);
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log(`Summary ${summaryId} sent!`);
    return { success: true };
  },

  schedule: async (summaryId: string, date: Date): Promise<{ success: boolean }> => {
    console.log(`Scheduling summary ${summaryId} for ${date.toISOString()}...`);
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log(`Summary ${summaryId} scheduled!`);
    return { success: true };
  },
};
