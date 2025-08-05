

/**
 * @file App.tsx
 * @description Componente raiz da aplicação.
 * Este componente é o contêiner de mais alto nível e é responsável por configurar os provedores globais e o sistema de roteamento.
 * - `AuthProvider`: Envolve a aplicação, fornecendo o contexto de autenticação (estado de login, etc.) para todos os componentes filhos.
 * - `AppRoutes`: Componente que define todas as rotas da aplicação (ex: /login, /dashboard).
 * Análise: A estrutura está limpa e segue as melhores práticas do React, separando a lógica de autenticação e de roteamento em seus próprios módulos.
 */
import { AppRoutes } from './routes';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
