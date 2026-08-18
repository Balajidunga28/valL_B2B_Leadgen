/**
 * url: /frontend/src/pages/SignupPage.tsx
 * About:
 *   Signup page for ValLG dark theme. Full-screen split layout with branded
 *   dark left panel and centered registration form. Premium SaaS aesthetic
 *   with subtle glow accents matching the login page.
 */

import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Link, useNavigate } from 'react-router-dom';

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await signup(name, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left: Brand Panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #0c0c14 0%, #10101a 30%, #14141f 60%, #0c0c14 100%)' }}>
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-600/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-brand-400/5 rounded-full blur-[100px]" />
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-brand-500/20 to-transparent" />

        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-brand-600/20 border border-brand-500/30 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white tracking-tight">ValLG</span>
          </div>
          <h2 className="text-3xl xl:text-4xl font-bold text-white leading-tight mb-4">
            Start Generating
            <br />B2B Leads Today
          </h2>
          <p className="text-dark-200 text-base leading-relaxed max-w-md">
            Create your account and get access to verified business leads across India.
            Powered by Google Places, MCA data, and intelligent pipeline extraction.
          </p>
          <div className="mt-10 flex items-center gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">Free</div>
              <div className="text-xs text-dark-300 font-medium">Trial Available</div>
            </div>
            <div className="w-px h-10 bg-dark-500" />
            <div className="text-center">
              <div className="text-2xl font-bold text-white">No</div>
              <div className="text-xs text-dark-300 font-medium">Credit Card</div>
            </div>
            <div className="w-px h-10 bg-dark-500" />
            <div className="text-center">
              <div className="text-2xl font-bold text-white">Instant</div>
              <div className="text-xs text-dark-300 font-medium">Setup</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Signup Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-dark-950">
        <div className="w-full max-w-[400px] animate-fade-in">
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-9 h-9 bg-brand-600 rounded-lg flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.3)]">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
              </svg>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">ValLG</span>
          </div>

          <h1 className="text-2xl font-bold text-white tracking-tight">Create your account</h1>
          <p className="text-sm text-dark-200 mt-1.5">
            Get started with ValLG in seconds
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 animate-scale-in">
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label htmlFor="name" className="block text-sm font-medium text-dark-100">
                Full name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className="block w-full rounded-lg border border-dark-500 bg-dark-800 px-3.5 py-2.5 text-sm text-dark-100 placeholder:text-dark-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500/50 transition-colors"
                autoComplete="name"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-dark-100">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="block w-full rounded-lg border border-dark-500 bg-dark-800 px-3.5 py-2.5 text-sm text-dark-100 placeholder:text-dark-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500/50 transition-colors"
                autoComplete="email"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-sm font-medium text-dark-100">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="block w-full rounded-lg border border-dark-500 bg-dark-800 px-3.5 py-2.5 text-sm text-dark-100 placeholder:text-dark-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500/50 transition-colors"
                autoComplete="new-password"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="confirm-password" className="block text-sm font-medium text-dark-100">
                Confirm password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                className="block w-full rounded-lg border border-dark-500 bg-dark-800 px-3.5 py-2.5 text-sm text-dark-100 placeholder:text-dark-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500/50 transition-colors"
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand-600 text-white text-sm font-semibold rounded-lg hover:bg-brand-500 focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-dark-950 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 shadow-[0_1px_4px_rgba(91,91,214,0.4)]"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Creating account...
                </>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <p className="mt-6 text-xs text-dark-300 text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 transition-colors font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
