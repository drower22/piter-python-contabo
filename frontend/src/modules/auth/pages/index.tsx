/**
 * @file src/modules/auth/pages/index.tsx
 * @description Componente que renderiza a página de login.
 * Esta página é exibida para usuários não autenticados. Contém um formulário para entrada de credenciais.
 * - `useAuth`: Hook para acessar a função `login` do contexto de autenticação.
 * - `useNavigate`: Hook para redirecionar o usuário para a dashboard após o login.
 * - `handleSubmit`: Função que previne o comportamento padrão do formulário, executa o login e redireciona o usuário.
 * Análise: A página utiliza componentes de UI reutilizáveis (`Button`, `Input`), o que é uma boa prática. A lógica de autenticação é simples (mock) mas está corretamente integrada com o `AuthContext`. O layout e o estilo são totalmente controlados pelo Tailwind CSS.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { useAuth } from '../../../contexts/AuthContext';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const { error: authError } = await login(email, password);

    if (authError) {
      setError(authError.message === 'Invalid login credentials' ? 'E-mail ou senha inválidos.' : 'Ocorreu um erro. Tente novamente.');
    } else {
      // The onAuthStateChange listener in AuthContext will handle the session update.
      // We can navigate away, and protected routes will handle the rest.
      navigate('/');
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-brand-gray-lilac flex items-center justify-center p-4 font-inter">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-brand-black-charcoal font-sora">Bem-vindo de volta!</h1>
          <p className="mt-2 text-gray-600">Acesse sua conta para continuar.</p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="font-inter text-sm font-medium text-gray-700 block mb-2">
              E-mail
            </label>
            <Input 
              type="email" 
              id="email" 
              placeholder="seu@email.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="font-inter text-sm font-medium text-gray-700 block mb-2">
              Senha
            </label>
            <Input 
              type="password" 
              id="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">
              {error}
            </div>
          )}

          <div className="text-right">
            <a href="#" className="font-inter text-sm text-brand-purple-dark hover:underline">
              Esqueceu a senha?
            </a>
          </div>

          <Button type="submit" disabled={loading}>
            {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>
      </div>
    </div>
  );
}
