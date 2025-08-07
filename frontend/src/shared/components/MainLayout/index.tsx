/**
 * @file src/components/MainLayout/index.tsx
 * @description Componente de layout principal para as páginas internas da aplicação.
 * Este componente cria a estrutura visual com uma barra lateral de navegação fixa e uma área de conteúdo principal.
 * - `Sidebar`: Contém o logo, a lista de navegação e o botão de logout.
 * - `Navigation`: Os links de navegação usam `useLocation` para destacar a rota ativa.
 * - `Main Content`: A área onde o conteúdo da página atual (`children`) é renderizado.
 * Análise: O layout é construído com Flexbox (`flex h-screen`), o que é uma abordagem moderna e robusta. As classes do Tailwind são usadas extensivamente para estilizar todos os aspectos do componente, desde as cores da marca até o espaçamento e a tipografia. A lógica para o link ativo está correta.
 */
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, BarChart2, LogOut } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { StoreSelector } from '../ui/StoreSelector';

interface MainLayoutProps {
  children: ReactNode;
}

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
  { icon: Upload, label: 'Upload de Planilhas', href: '/upload' },
  { icon: BarChart2, label: 'Resumos', href: '/summaries' },
];

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation();
  const { logout } = useAuth();

  return (
    <div className="flex h-screen bg-brand-gray-lilac font-inter">
      {/* --- Sidebar --- */}
      <aside className="w-64 flex-shrink-0 bg-white flex flex-col border-r border-gray-200">
        {/* Logo */}
        <div className="h-20 flex items-center justify-center px-6 border-b border-gray-200">
          <h1 className="font-sora text-2xl font-bold text-brand-purple-dark">Dex Parceiros</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href || (item.href === '/upload' && location.pathname.startsWith('/upload'));
            return (
              <Link
                key={item.label}
                to={item.href}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                  isActive
                    ? 'bg-brand-purple-light text-brand-purple-dark'
                    : 'text-gray-600 hover:bg-brand-gray-lilac hover:text-brand-purple-dark'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Store Selector - acima do botão sair */}
        <div className="px-4 pt-2">
          {/* TODO: Receber stores, selectedStoreId e onChange via props/context */}
          <StoreSelector
            stores={[
              { id: '1', name: 'Loja A' },
              { id: '2', name: 'Loja B' },
            ]}
            selectedStoreId={'1'}
            onChange={() => {}}
          />
        </div>

        {/* Logout Button */}
        <div className="p-4 border-t border-gray-200">
          <button 
            onClick={logout}
            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm font-medium text-gray-600 rounded-lg hover:bg-brand-gray-lilac hover:text-brand-purple-dark transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      {/* --- Main Content Area --- */}
      <main className="flex-1 p-10 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
