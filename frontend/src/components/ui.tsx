/**
 * url: /frontend/src/components/ui.tsx
 * About:
 *   Shared UI primitives for ValLG dark theme. Reusable Button, Card, Badge,
 *   Input, Skeleton, EmptyState, and MetricCard components with premium dark
 *   surfaces, high-contrast text, and blue accent colors.
 */

import { type ReactNode, type ButtonHTMLAttributes, type InputHTMLAttributes } from 'react';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-dark-800 rounded-xl border border-dark-600 shadow-[0_2px_8px_rgba(0,0,0,0.3)] ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-6 py-4 border-b border-dark-600 ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-6 py-5 ${className}`}>
      {children}
    </div>
  );
}

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-brand-600 text-white shadow-[0_1px_4px_rgba(91,91,214,0.4)] hover:bg-brand-500 active:bg-brand-700 focus-visible:ring-brand-500',
  secondary: 'bg-dark-700 text-dark-100 border border-dark-500 shadow-sm hover:bg-dark-600 hover:border-dark-400 active:bg-dark-500 focus-visible:ring-brand-500',
  ghost: 'text-dark-200 hover:bg-dark-700 hover:text-dark-100 active:bg-dark-600 focus-visible:ring-brand-500',
  danger: 'bg-red-600 text-white shadow-sm hover:bg-red-500 active:bg-red-700 focus-visible:ring-red-500',
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs font-medium rounded-lg',
  md: 'px-4 py-2 text-sm font-medium rounded-lg',
  lg: 'px-5 py-2.5 text-sm font-semibold rounded-xl',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 transition-all duration-150 ease-in-out disabled:opacity-40 disabled:cursor-not-allowed ${buttonVariants[variant]} ${buttonSizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  icon?: ReactNode;
}

export function Input({ label, hint, error, icon, className = '', id, ...props }: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-dark-100">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-dark-300">
            {icon}
          </div>
        )}
        <input
          id={inputId}
          className={`block w-full rounded-lg border ${error ? 'border-red-500/50 focus-visible:ring-red-500' : 'border-dark-500 focus-visible:ring-brand-500 focus:border-brand-500/50'} bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder:text-dark-300 transition-colors duration-150 ${icon ? 'pl-10' : ''} ${className}`}
          {...props}
        />
      </div>
      {hint && !error && <p className="text-xs text-dark-200">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export function Select({ label, error, children, className = '', id, ...props }: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-dark-100">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`block w-full rounded-lg border ${error ? 'border-red-500/50' : 'border-dark-500'} bg-dark-800 px-3 py-2 text-sm text-dark-100 focus-visible:ring-brand-500 focus:border-brand-500/50 transition-colors duration-150 ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

type BadgeVariant = 'default' | 'brand' | 'success' | 'warning' | 'error' | 'subtle';

const badgeVariants: Record<BadgeVariant, string> = {
  default: 'bg-dark-600 text-dark-100',
  brand: 'bg-brand-600/15 text-brand-300 ring-1 ring-brand-500/20',
  success: 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/20',
  warning: 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20',
  error: 'bg-red-500/15 text-red-400 ring-1 ring-red-500/20',
  subtle: 'bg-dark-700 text-dark-200 ring-1 ring-dark-500',
};

export function Badge({ variant = 'default', children, className = '' }: { variant?: BadgeVariant; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeVariants[variant]} ${className}`}>
      {children}
    </span>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-gradient-to-r from-dark-700 via-dark-600 to-dark-700 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite] rounded-lg ${className}`} />
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      {icon && (
        <div className="w-12 h-12 rounded-xl bg-dark-700 border border-dark-600 flex items-center justify-center text-dark-200 mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-dark-100 mb-1">{title}</h3>
      <p className="text-sm text-dark-200 max-w-sm mb-4">{description}</p>
      {action}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: { value: number; label: string };
  variant?: 'default' | 'brand';
}

export function MetricCard({ label, value, icon, variant = 'default' }: MetricCardProps) {
  return (
    <Card className="animate-slide-up">
      <CardContent className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs sm:text-sm font-medium text-dark-200">{label}</p>
          <p className="text-2xl sm:text-3xl font-bold text-white mt-1 tracking-tight">{value}</p>
        </div>
        <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shrink-0 ${variant === 'brand' ? 'bg-brand-600/15 text-brand-400' : 'bg-dark-700 text-dark-200'}`}>
          {icon}
        </div>
      </CardContent>
    </Card>
  );
}

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6 animate-fade-in">
      <div className="min-w-0">
        <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{title}</h1>
        {description && <p className="text-sm text-dark-200 mt-1">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 sm:gap-3 flex-wrap shrink-0">{actions}</div>}
    </div>
  );
}
