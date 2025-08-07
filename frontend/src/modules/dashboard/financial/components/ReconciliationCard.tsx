import * as React from 'react';
import type { WeeklyFinancials } from '../../types';
import { Button } from '../../../../shared/components/ui/button';
import { AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../../../shared/components/ui/dialog';

interface ReconciliationCardProps {
  financialData: WeeklyFinancials;
}

export function ReconciliationCard({ financialData }: ReconciliationCardProps) {
  const { reconciliation } = financialData;
  const [modalOpen, setModalOpen] = React.useState(false);

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border">
      <h3 className="font-sora font-semibold text-brand-purple mb-2">Conciliação e Extrato</h3>
      <p className="text-sm text-gray-500 mb-4">Status da Conciliação</p>
      <div className="flex justify-between items-center bg-gray-50 p-4 rounded-lg">
        <p className="text-sm text-gray-700">Existem {reconciliation.pendingItems} itens pendentes de verificação.</p>
        <Button variant="outline" size="sm" onClick={() => setModalOpen(true)}>
          <AlertTriangle className="mr-2" size={16}/>
          Ver Detalhes da Pendência
        </Button>
      </div>
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
  <DialogHeader>
    <DialogTitle>Detalhes das Pendências de Conciliação</DialogTitle>
    <DialogDescription>
      <div className="py-4">
        <p className="text-sm text-gray-700 mb-4">
          Abaixo estão listados os pedidos com divergências encontradas na conciliação financeira desta semana:
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm border rounded-lg">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-4 py-2 text-left font-semibold">ID do Pedido</th>
                <th className="px-4 py-2 text-left font-semibold">Valor</th>
                <th className="px-4 py-2 text-left font-semibold">Status</th>
                <th className="px-4 py-2 text-left font-semibold">Divergência</th>
              </tr>
            </thead>
            <tbody>
              {/* MOCK: Substitua por reconciliation.pendingOrders.map(...) quando houver dados reais */}
              {[{
                id: '123456', valor: 89.90, status: 'Aguardando conciliação', divergencia: 'Valor recebido menor que o esperado'
              }, {
                id: '123457', valor: 120.00, status: 'Aguardando repasse', divergencia: 'Repasse não realizado'
              }].map((pedido) => (
                <tr key={pedido.id} className="border-b last:border-b-0">
                  <td className="px-4 py-2 font-mono">{pedido.id}</td>
                  <td className="px-4 py-2">R$ {pedido.valor.toFixed(2)}</td>
                  <td className="px-4 py-2">{pedido.status}</td>
                  <td className="px-4 py-2">
                    <span className="inline-block bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-semibold">
                      {pedido.divergencia}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DialogDescription>
  </DialogHeader>
</DialogContent>
      </Dialog>
    </div>
  );
}