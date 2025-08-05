/**
 * @file src/contexts/AuthContext.tsx
 * @description Implementa o contexto de autenticação para gerenciar o estado de login do usuário.
 * - `AuthContext`: O contexto React que armazena o estado de autenticação.
 * - `AuthProvider`: O componente provedor que envolve a aplicação e fornece o valor do contexto.
 * - `useAuth`: Um hook customizado para acessar facilmente o contexto (isAuthenticated, login, logout) de qualquer componente.
 * Análise: Esta é uma implementação de mock para desenvolvimento. O estado de autenticação (`isAuthenticated`) é gerenciado pelo `useState` e não é persistido (ex: no localStorage), o que significa que o usuário é deslogado a cada atualização da página. Para a fase de desenvolvimento da UI, isso é perfeitamente adequado.
 */
import { createContext, useState, useContext } from 'react';
import type { ReactNode } from 'react';
import type { FC } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = () => {
    // In a real app, you'd have logic to verify credentials
    setIsAuthenticated(true);
  };

  const logout = () => {
    // In a real app, you'd clear tokens, etc.
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
