

export interface StoreOption {
  id: string;
  name: string;
}

interface StoreSelectorProps {
  stores: StoreOption[];
  selectedStoreId: string;
  onChange: (storeId: string) => void;
  className?: string;
}

export function StoreSelector({ stores, selectedStoreId, onChange, className }: StoreSelectorProps) {
  return (
    <select
      className={`w-full px-4 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-purple-light mb-4 ${className || ''}`}
      value={selectedStoreId}
      onChange={e => onChange(e.target.value)}
      aria-label="Selecionar loja"
    >
      {stores.map(store => (
        <option key={store.id} value={store.id}>
          {store.name}
        </option>
      ))}
    </select>
  );
}
