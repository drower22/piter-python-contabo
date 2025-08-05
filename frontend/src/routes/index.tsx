/**
 * @file src/routes/index.tsx
 * @description Define o sistema de roteamento da aplicação.
 * Utiliza `react-router-dom` para mapear URLs a componentes de página específicos.
 * - `ProtectedRoute`: Um componente customizado que verifica se o usuário está autenticado. Se não estiver, redireciona para a página de login.
 * - `AppLayout`: Um layout que envolve as páginas protegidas com o `MainLayout` (barra lateral, etc.).
 * - `createBrowserRouter`: Cria a instância do roteador com todas as definições de rotas, incluindo as rotas filhas protegidas.
 * Análise: A implementação do roteamento está robusta e segura, usando padrões modernos do `react-router-dom` para proteger rotas e compor layouts.
 */
import { createBrowserRouter, RouterProvider, Outlet, Navigate } from 'react-router-dom';
import { LoginPage } from '../modules/auth';
import { DashboardPage } from '../modules/dashboard';
import { UploadPage } from '../modules/upload';
import { SummariesPage } from '../modules/summaries';
import { MainLayout } from '../shared/components/MainLayout';
import { useAuth } from '../contexts/AuthContext';

const AppLayout = () => (
  <MainLayout>
    <Outlet />
  </MainLayout>
);

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <AppLayout /> : <Navigate to="/login" replace />;
};

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        path: '',
        element: <DashboardPage />,
      },
      {
        path: 'upload',
        element: <UploadPage />,
      },
      {
        path: 'summaries',
        element: <SummariesPage />,
      },
    ],
  },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
