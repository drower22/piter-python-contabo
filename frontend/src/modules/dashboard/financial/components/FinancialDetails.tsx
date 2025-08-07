import type { WeeklyFinancials } from '../../types';
import { MinimalAccordion } from '@/shared/components/ui/MinimalAccordion';
import { Receipt, Wallet, AlertTriangle, CreditCard, BadgePercent, QrCode } from 'lucide-react';

// Helper para formatar valores monetários
const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

interface FinancialDetailsProps {
  financialData: WeeklyFinancials;
}

export function FinancialDetails({ financialData }: FinancialDetailsProps) {
  const { online, direct } = financialData;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Repasses iFood (Online) */}
      <div className="p-6 bg-white rounded-xl shadow-sm border flex flex-col">
        <h3 className="font-sora font-semibold text-brand-purple mb-4">Repasses iFood (Online)</h3>
        <div className="border-t my-4"></div>
        <div className="space-y-4 flex-grow">
          {/* Card Total Vendas Online */}
          <div className="flex items-center justify-between bg-white rounded-lg shadow-sm px-4 py-3 border border-gray-200">
            <div className="flex items-center gap-2">
              <Receipt size={20} className="text-gray-400" />
              <span className="text-gray-800 font-medium">Total Vendas Online</span>
            </div>
            <span className="font-mono font-bold text-brand-purple text-base">{formatCurrency(online.gross)}</span>
          </div>

          {/* Card Total em Descontos com acordeão */}
          <div className="bg-white rounded-lg shadow-sm px-4 py-3 border border-gray-200">
            <MinimalAccordion label={
              <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2 w-full">
                <AlertTriangle size={18} className="text-gray-400 col-start-1 row-span-1" />
                <span className="text-gray-800 font-medium col-start-2 row-span-1">Total em Descontos</span>
                <span className="font-mono font-bold text-red-500 col-start-3 row-span-1 justify-self-end">{formatCurrency(-online.ifoodFees)}</span>
              </div>
            }>
              <div className="flex flex-col gap-1 border-l-2 border-red-200 bg-white px-4 py-2 mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Taxas iFood</span>
                  <span className="font-mono text-red-600">{formatCurrency(-online.ifoodFees)}</span>
                </div>
                {/* Outros descontos detalhados */}
              </div>
            </MinimalAccordion>
          </div>

          {/* Card Total Líquido a Receber */}
          <div className="flex items-center justify-between bg-white rounded-lg shadow-sm px-4 py-3 border border-gray-200">
            <div className="flex items-center gap-2">
              <Wallet size={20} className="text-gray-400" />
              <span className="text-gray-800 font-medium">Total Líquido a Receber</span>
            </div>
            <span className="font-mono font-bold text-brand-purple text-base">{formatCurrency(online.net)}</span>
          </div>
        </div>
      </div>

      {/* Vendas Diretas (Loja) */}
      <div className="p-6 bg-white rounded-xl shadow-sm border flex flex-col">
        <h3 className="font-sora font-semibold text-brand-purple mb-4">Vendas Diretas (Loja)</h3>
        <div className="border-t my-4"></div>
        <div className="space-y-3 text-sm flex-grow">
          <div className="flex justify-between items-center">
            <span className="text-gray-600 flex items-center gap-2">
              <CreditCard size={22} className="text-[#a78bfa]" />
              Crédito
            </span>
            <span className="font-mono font-medium">{formatCurrency(direct.methods.credit)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 flex items-center gap-2">
              <BadgePercent size={22} className="text-[#a78bfa]" />
              Débito
            </span>
            <span className="font-mono font-medium">{formatCurrency(direct.methods.debit)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 flex items-center gap-2">
              <QrCode size={22} className="text-[#a78bfa]" />
              Pix
            </span>
            <span className="font-mono font-medium">{formatCurrency(direct.methods.pix)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 flex items-center gap-2">
              <Wallet size={22} className="text-[#a78bfa]" />
              Dinheiro
            </span>
            <span className="font-mono font-medium">{formatCurrency(direct.methods.cash)}</span>
          </div>
        </div>
        <div className="border-t my-4"></div>
        <div className="flex justify-between items-center text-base font-bold"><span className="text-gray-800">Total Arrecadado</span><span className="font-mono text-brand-purple">{formatCurrency(direct.total)}</span></div>
      </div>
    </div>
  );
}