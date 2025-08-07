import type { WeeklyFinancials } from '../../types';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../../../shared/components/ui/tooltip';

// Helper para formatar valores monetários
const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);

// Helper para abreviar valores monetários
const formatCurrencyShort = (value: number) => {
  if (Math.abs(value) >= 1000000) {
    return `R$ ${(value / 1000000).toFixed(1).replace('.', ',')}M`;
  }
  if (Math.abs(value) >= 1000) {
    return `R$ ${(value / 1000).toFixed(1).replace('.', ',')}k`;
  }
  return formatCurrency(value);
};

function ComparisonTag({ percent }: { percent: number }) {
  if (percent > 0.5) {
    return (
      <span className="ml-2 flex items-center text-xs font-medium text-green-600">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" className="mr-0.5 inline">
          <path d="M10 4l5 8H5l5-8z" />
        </svg>
        +{percent.toFixed(1)}%
      </span>
    );
  }
  if (percent < -0.5) {
    return (
      <span className="ml-2 flex items-center text-xs font-medium text-red-600">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" className="mr-0.5 inline">
          <path d="M10 16l-5-8h10l-5 8z" />
        </svg>
        {percent.toFixed(1)}%
      </span>
    );
  }
  return <span className="ml-2 text-xs font-medium text-gray-400">=</span>;
}

interface PerformanceKpisProps {
  data: WeeklyFinancials;
}

export function PerformanceKpis({ data }: PerformanceKpisProps) {
  const { online, direct, totalPedidos, ticketMedio } = data;
  const totalBruto = online.gross + direct.total;

  // Simula variação entre -10% e +10%
  const getComparison = (current: number) => {
    const variation = Math.random() * 0.2 - 0.1;
    const previous = current / (1 + variation);
    const percent = previous !== 0 ? ((current - previous) / previous) * 100 : 0;
    return { percent };
  };

  // Comparativos simulados
  const grossComp = getComparison(totalBruto);
  const pedidosComp = getComparison(totalPedidos);
  const ticketComp = getComparison(ticketMedio);
  const ifoodFeesComp = getComparison(online.ifoodFees);
  const netComp = getComparison(online.net);
  const ifoodIncentivesComp = getComparison(online.ifoodIncentives);
  const incentivosLojaComp = getComparison(direct.incentivosLoja);
  const anunciosPagosComp = getComparison(online.anunciosPagos);
  const entregasLojaComp = getComparison(direct.entregasLoja);
  const taxasEntregadoresComp = getComparison(online.taxasEntregadores);

  return (
    <TooltipProvider>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Faturamento Total */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Faturamento Total</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(totalBruto)}
                <ComparisonTag percent={grossComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(totalBruto)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Total de Pedidos */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Total de Pedidos</p>
          <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
            {totalPedidos}
            <ComparisonTag percent={pedidosComp.percent} />
          </p>
        </div>

        {/* Ticket Médio */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Ticket Médio</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(ticketMedio)}
                <ComparisonTag percent={ticketComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(ticketMedio)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Taxas iFood */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Taxas iFood</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(online.ifoodFees)}
                <ComparisonTag percent={ifoodFeesComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(online.ifoodFees)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Valor Líquido Total */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Valor Líquido Total</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(online.net)}
                <ComparisonTag percent={netComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(online.net)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Incentivos iFood */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Incentivos iFood</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(online.ifoodIncentives)}
                <ComparisonTag percent={ifoodIncentivesComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(online.ifoodIncentives)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Incentivos Loja */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Incentivos Loja</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(direct.incentivosLoja)}
                <ComparisonTag percent={incentivosLojaComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(direct.incentivosLoja)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Anúncios Pagos */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Anúncios Pagos</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(online.anunciosPagos)}
                <ComparisonTag percent={anunciosPagosComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(online.anunciosPagos)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Entregas Loja */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Entregas Loja</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(direct.entregasLoja)}
                <ComparisonTag percent={entregasLojaComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(direct.entregasLoja)}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Taxas Entregadores */}
        <div className="p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]">
          <p className="text-sm text-gray-500 mb-1">Taxas Entregadores</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600 flex items-center justify-center">
                {formatCurrencyShort(online.taxasEntregadores)}
                <ComparisonTag percent={taxasEntregadoresComp.percent} />
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p>{formatCurrency(online.taxasEntregadores)}</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
}
