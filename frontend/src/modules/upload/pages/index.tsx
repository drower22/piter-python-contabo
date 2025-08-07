import { UploadForm } from '../components/upload/UploadForm';
import { UploadHistoryTable } from '../components/history/UploadHistoryTable';

/**
 * @file src/modules/upload/pages/index.tsx
 * @description Componente que renderiza a página para upload de planilhas.
 * Esta página servirá como a interface para os usuários enviarem seus arquivos de vendas.
 * Análise: Atualmente, este componente é um placeholder. Ele exibe um título e um subtítulo, mas a funcionalidade principal de upload de arquivos ainda não foi implementada. As classes do Tailwind para o título e o texto estão aplicadas corretamente.
 */
export function UploadPage() {
  return (
    <div>
      <h1 className="font-sora text-3xl font-bold text-brand-black-charcoal">Upload de Planilhas</h1>
      <p className="font-inter text-gray-600 mt-2">Envie seus arquivos para análise.</p>

      {/* Card principal para a funcionalidade de upload */}
      <div className="mt-8 bg-white rounded-xl shadow border p-6">
        <UploadForm />
      </div>

      {/* Seção de Histórico */}
      <div className="mt-12">
        <h2 className="font-sora text-2xl font-bold text-brand-black-charcoal">Histórico de Uploads</h2>
        <div className="mt-6">
          <UploadHistoryTable />
        </div>
      </div>
    </div>
  );
}
