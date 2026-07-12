import React, { useState } from 'react';

interface LoginProps {
  setToken: (token: string) => void;
}

export function Login({ setToken }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleToggleMode = () => {
    setIsRegister(!isRegister);
    setError('');
    setUsername('');
    setEmail('');
    setPassword('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const endpoint = isRegister ? '/auth/register' : '/auth/login';
    const body = isRegister ? { username, email, password } : { email, password };

    try {
      const response = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const contentType = response.headers.get('content-type');
      if (!contentType?.includes('application/json')) {
        throw new Error('Server error. Please try again later.');
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Authentication failed');
      }

      if (data.token) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
      } else {
        throw new Error('No token received from server');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="bg-purple-800 p-8 rounded-lg w-full max-w-md shadow-xl">
        <h2 className="text-white text-2xl font-bold mb-6 text-center">
          {isRegister ? 'Create Account' : 'Welcome Back'}
        </h2>

        {error && (
          <div
            className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm"
            role="alert"
            aria-live="polite"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label htmlFor="username" className="block text-purple-200 text-sm mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                placeholder="johndoe"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-gray-700 text-white p-3 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
                required
                disabled={isLoading}
                minLength={3}
                maxLength={50}
              />
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-purple-200 text-sm mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-700 text-white p-3 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
              required
              disabled={isLoading}
              autoComplete={isRegister ? 'email' : 'username'}
            />
          </div>

          <div className="relative">
            <label htmlFor="password" className="block text-purple-200 text-sm mb-1">
              Password
            </label>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-700 text-white p-3 rounded pr-12 focus:outline-none focus:ring-2 focus:ring-purple-400"
              required
              disabled={isLoading}
              minLength={8}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-8 text-purple-300 hover:text-white text-sm"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-purple-500 text-white p-3 rounded hover:bg-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {isRegister ? 'Creating account...' : 'Logging in...'}
              </span>
            ) : (
              isRegister ? 'Sign Up' : 'Login'
            )}
          </button>
        </form>

        <button
          onClick={handleToggleMode}
          disabled={isLoading}
          className="w-full text-purple-300 mt-6 hover:text-white transition-colors text-sm"
        >
          {isRegister ? 'Already have an account? Login' : "Don't have an account? Sign up"}
        </button>
      </div>
    </div>
  );
}
