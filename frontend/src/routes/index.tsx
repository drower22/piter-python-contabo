/**
 * @file src/routes/index.tsx
 * @description Define o sistema de roteamento da aplicação.
 * Utiliza `react-router-dom` para mapear URLs a componentes de página específicos.
 * - `ProtectedRoute`: Um componente customizado que verifica se o usuário está autenticado. Se não estiver, redireciona para a página de login.
 * - `MainLayout`: Um layout que envolve as páginas protegidas com o `MainLayout` (barra lateral, etc.).
 * - `createBrowserRouter`: Cria a instância do roteador com todas as definições de rotas, incluindo as rotas filhas protegidas.
 * Análise: A implementação do roteamento está robusta e segura, usando padrões modernos do `react-router-dom` para proteger rotas e compor layouts.
 */
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { LoginPage } from '../modules/auth';
import { SetPasswordPage } from '../modules/auth/pages/SetPasswordPage';
import { DashboardPage } from '../modules/dashboard';
import { UploadPage } from '../modules/upload';
import { SummariesPage } from '../modules/summaries';
import { MainLayout } from '../shared/components/MainLayout';
import { useAuth } from '../contexts/AuthContext';

// Layout para as páginas protegidas, que renderiza as páginas filhas via <Outlet />
const ProtectedLayout = () => (
  <MainLayout>
    <Outlet />
  </MainLayout>
);

// Componente que protege as rotas, verificando a sessão do usuário
const ProtectedRoute = () => {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        Carregando...
      </div>
    );
  }

  return session ? <ProtectedLayout /> : <Navigate to="/login" replace />;
};

export function AppRoutes() {
  return (
    <Routes>
      {/* Rotas Públicas */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/update-password" element={<SetPasswordPage />} />

      {/* Rotas Protegidas com Layout */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/summaries" element={<SummariesPage />} />
      </Route>

      {/* Redirecionamento para rotas não encontradas */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
