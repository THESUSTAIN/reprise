import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Logo from '../components/Logo';
import { LogIn, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'register') {
        const { authApi } = await import('../lib/api');
        await authApi.register({ email, password, name });
      }
      await login(email, password);
      toast.success('Connexion réussie');
      navigate(from, { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Échec de la connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      data-testid="login-page"
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'linear-gradient(135deg,#142b45 0%,#1B3A5B 55%,#0c1d31 100%)' }}
    >
      <div className="w-full max-w-md rounded-2xl bg-white/95 backdrop-blur shadow-2xl p-8">
        <div className="flex justify-center mb-6">
          <Logo variant="onLight" size="lg" />
        </div>
        <h1 className="text-2xl font-bold text-[#142b45] text-center mb-1">
          {mode === 'login' ? 'Connexion' : 'Créer un compte'}
        </h1>
        <p className="text-sm text-[#6b6358] text-center mb-6">
          Accédez à votre cockpit MyExtension-ai
        </p>

        <form onSubmit={submit} className="space-y-4">
          {mode === 'register' && (
            <input
              data-testid="login-name"
              type="text" placeholder="Nom complet" value={name}
              onChange={(e) => setName(e.target.value)} required
              className="w-full h-11 px-4 rounded-lg border border-[#dfe5ee] focus:border-[#1f4377] outline-none text-[#142b45]"
            />
          )}
          <input
            data-testid="login-email"
            type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} required
            className="w-full h-11 px-4 rounded-lg border border-[#dfe5ee] focus:border-[#1f4377] outline-none text-[#142b45]"
          />
          <input
            data-testid="login-password"
            type="password" placeholder="Mot de passe" value={password}
            onChange={(e) => setPassword(e.target.value)} required
            className="w-full h-11 px-4 rounded-lg border border-[#dfe5ee] focus:border-[#1f4377] outline-none text-[#142b45]"
          />
          <button
            data-testid="login-submit"
            type="submit" disabled={loading}
            className="w-full h-11 rounded-lg text-white font-medium flex items-center justify-center gap-2 disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg,#1f4377,#142b45)' }}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
            {mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
          </button>
        </form>

        <button
          data-testid="login-toggle-mode"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          className="w-full text-center text-sm text-[#1f4377] mt-4 hover:underline"
        >
          {mode === 'login' ? "Pas encore de compte ? S'inscrire" : 'Déjà un compte ? Se connecter'}
        </button>

        <button
          data-testid="login-demo"
          onClick={() => { setEmail('test@zayado.net'); setPassword('Test1234!'); setMode('login'); }}
          className="w-full text-center text-xs text-[#9a9384] mt-3 hover:text-[#6b6358]"
        >
          Remplir le compte de démonstration
        </button>
      </div>
    </div>
  );
}
