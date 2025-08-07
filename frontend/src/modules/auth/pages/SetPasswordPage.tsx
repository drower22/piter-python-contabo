import { useState, useEffect, useMemo } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AiFillEye, AiFillEyeInvisible } from 'react-icons/ai';
import { supabase } from '../../../lib/supabase';
import { useAuth } from '../../../contexts/AuthContext';

// Componente para o item da lista de validação
const ValidationItem = ({ text, valid }: { text: string; valid: boolean }) => (
  <li className={`text-sm ${valid ? 'text-green-600' : 'text-gray-500'}`}>
    <span className="mr-2">{valid ? '✓' : '•'}</span>
    {text}
  </li>
);

export function SetPasswordPage() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { session, loading: authLoading } = useAuth();

  // Redireciona se não houver sessão (acesso direto à URL)
  useEffect(() => {
    if (!authLoading && !session) {
      navigate('/login');
    }
  }, [session, authLoading, navigate]);

  // Lógica de validação da senha
  const validation = useMemo(() => {
    const hasUpper = /[A-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
    const hasLength = password.length >= 8;
    return { hasUpper, hasNumber, hasSpecial, hasLength };
  }, [password]);

  const isPasswordValid = Object.values(validation).every(Boolean);
  const doPasswordsMatch = password && password === confirmPassword;
  const canSubmit = isPasswordValid && doPasswordsMatch && !loading;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setError(null);
    setLoading(true);

    // 1. Atualiza a senha no Supabase Auth
    const { error: updateError } = await supabase.auth.updateUser({ password });

    if (updateError) {
      setError(updateError.message);
      setLoading(false);
      return;
    }

    // 2. Se a senha foi atualizada, chama o backend para criar o perfil
    if (session?.user) {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
        const response = await fetch(`${apiUrl}/complete-profile`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: session.user.id,
            email: session.user.email,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Falha ao finalizar o cadastro no backend.');
        }
        
        // 3. Se tudo deu certo, navega para a página principal
        navigate('/');

      } catch (apiError: any) {
        setError(`Erro ao criar perfil: ${apiError.message}`);
      } finally {
        setLoading(false);
      }
    } else {
      setError('Sua sessão expirou. Por favor, tente novamente a partir do link de convite.');
      setLoading(false);
    }
  };
  
  if (authLoading) {
    return <div className="flex h-screen items-center justify-center">Carregando...</div>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="rounded-xl bg-white p-8 shadow-lg">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">Crie sua senha</h2>
            <p className="mt-2 text-sm text-gray-600">Defina uma senha segura para acessar sua conta.</p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {/* Campo Nova Senha */}
            <div className="relative">
              <label htmlFor="password" className="sr-only">Nova Senha</label>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nova Senha"
                className="block w-full rounded-md border-gray-300 px-4 py-3 placeholder-gray-400 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <AiFillEyeInvisible size={20} /> : <AiFillEye size={20} />}
              </button>
            </div>

            {/* Campo Confirmar Senha */}
            <div>
              <label htmlFor="confirm-password"className="sr-only">Confirmar Senha</label>
              <input
                id="confirm-password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirmar Senha"
                className="block w-full rounded-md border-gray-300 px-4 py-3 placeholder-gray-400 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>

            {/* Validação da Senha */}
            <ul className="space-y-1">
              <ValidationItem text="Pelo menos 8 caracteres" valid={validation.hasLength} />
              <ValidationItem text="Uma letra maiúscula" valid={validation.hasUpper} />
              <ValidationItem text="Um número" valid={validation.hasNumber} />
              <ValidationItem text="Um caractere especial (!@#...)" valid={validation.hasSpecial} />
            </ul>
            
            {error && <p className="text-center text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={!canSubmit}
              className="flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-indigo-400"
            >
              {loading ? 'Salvando...' : 'Salvar e Entrar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
