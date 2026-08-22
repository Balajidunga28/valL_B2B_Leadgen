import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import Layout from './components/Layout';

const LoginPage = lazy(() => import('./pages/LoginPage'));
const SignupPage = lazy(() => import('./pages/SignupPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const RecordDetailPage = lazy(() => import('./pages/RecordDetailPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const MapsPage = lazy(() => import('./pages/MapsPage'));
const DirectoriesPage = lazy(() => import('./pages/DirectoriesPage'));
const SourcesPage = lazy(() => import('./pages/SourcesPage'));
const DiscoveryPage = lazy(() => import('./pages/DiscoveryPage'));

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-screen bg-dark-950">
            <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        }>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="discovery" element={<DiscoveryPage />} />
              <Route path="results" element={<ResultsPage />} />
              <Route path="results/:recordId" element={<RecordDetailPage />} />
              <Route path="maps" element={<MapsPage />} />
              <Route path="directories" element={<DirectoriesPage />} />
              <Route path="sources" element={<SourcesPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
