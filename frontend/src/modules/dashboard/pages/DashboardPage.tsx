/**
 * @file src/modules/dashboard/pages/DashboardPage.tsx
 * @description Componente que renderiza a página principal do dashboard.
 * Esta página exibe uma visão geral das métricas de vendas mais importantes.
 * - `dashboardMetrics`: Um array de dados fictícios que simula as métricas a serem exibidas.
 * - `Card`: Utiliza o componente reutilizável `Card` para exibir cada métrica.
 * - `grid`: O layout é uma grade responsiva do Tailwind CSS que se ajusta de 1 para 2 e 4 colunas dependendo do tamanho da tela.
 * Análise: A página está bem estruturada, separando os dados da apresentação. O uso de componentes reutilizáveis e do sistema de grade do Tailwind é uma excelente prática. A lógica para exibir os dados e ícones dinamicamente está correta.
 */
import { useState } from 'react';
import { DollarSign, TrendingUp, FileText, Gift, Store, Truck, Megaphone, Users } from 'lucide-react';
import { Card } from '../../../shared/components/Card';
import { DashboardFilters } from '../components/DashboardFilters';
import { PerformanceChart } from '../components/PerformanceChart';

const performanceMetrics = [
  { icon: DollarSign, title: 'Faturamento Total', value: 'R$ 25.850,70', subValue: '', change: '+8.2%', changeType: 'increase' },
  { icon: TrendingUp, title: 'Ticket Médio', value: 'R$ 92,32', subValue: '', change: '+1.5%', changeType: 'increase' },
  { icon: FileText, title: 'Taxas iFood', value: 'R$ 4.653,12', subValue: '18%', change: '+0.5%', changeType: 'decrease' }, // Higher tax is bad
  { icon: Megaphone, title: 'Anúncios Pagos', value: 'R$ 750,00', subValue: '', change: '+20%', changeType: 'decrease' }, // Higher cost is bad
  { icon: Gift, title: 'Incentivos iFood', value: 'R$ 1.230,00', subValue: '', change: '-5%', changeType: 'increase' }, // Lower incentive is good for comparison
  { icon: Store, title: 'Incentivos Loja', value: 'R$ 980,00', subValue: '', change: '+10%', changeType: 'decrease' }, // Higher cost is bad
  { icon: Truck, title: 'Entregas Loja', value: 'R$ 315,50', subValue: '', change: '+3%', changeType: 'decrease' }, // Higher cost is bad
  { icon: Users, title: 'Taxas Entregadores', value: 'R$ 1.890,25', subValue: '', change: '+2.1%', changeType: 'decrease' }, // Higher cost is bad
];

export function DashboardPage() {
  const [filterType, setFilterType] = useState<'performance' | 'financial'>('performance');

  return (
    <div>
      <h1 className="font-sora text-3xl font-bold text-brand-black-charcoal">Dashboard</h1>
      <p className="font-inter text-gray-600 mt-2">Visão geral dos seus resultados.</p>

      <div className="mt-6">
        <DashboardFilters filterType={filterType} onFilterTypeChange={setFilterType} />
      </div>

      {filterType === 'performance' && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8 animate-fade-in">
            {performanceMetrics.map((metric) => (
              <Card key={metric.title}>
                <div className="flex items-center justify-between">
                  <h3 className="font-sora text-gray-500 text-sm">{metric.title}</h3>
                  <metric.icon className="w-5 h-5 text-gray-400" />
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-bold text-brand-black-charcoal flex items-baseline gap-2">
                    {metric.value}
                    {metric.subValue && (
                      <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {metric.subValue}
                      </span>
                    )}
                  </p>
                  <p className={`text-xs mt-1 font-medium ${metric.changeType === 'increase' ? 'text-green-600' : 'text-red-600'}`}>
                    {metric.change} vs. período anterior
                  </p>
                </div>
              </Card>
            ))}
          </div>

          <PerformanceChart />
        </div>
      )}

      {filterType === 'financial' && (
        <div className="mt-8 animate-fade-in">
          <p className="text-center text-gray-500">A área financeira será implementada aqui.</p>
        </div>
      )}
    </div>
  );
}
