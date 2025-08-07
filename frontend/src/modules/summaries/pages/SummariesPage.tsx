import { SummaryList } from '../components/SummaryList';

export function SummariesPage() {
  return (
    <div>
      <h1 className="font-sora text-3xl font-bold text-brand-black-charcoal">Resumos</h1>
      <p className="font-inter text-gray-600 mt-2">Escolha um modelo de resumo para enviar ou agendar.</p>

      <div className="mt-8 bg-white rounded-xl shadow border p-6">
        <SummaryList />
      </div>
    </div>
  );
}
