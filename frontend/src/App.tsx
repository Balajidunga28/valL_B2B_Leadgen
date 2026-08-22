/**
 * url: /frontend/src/App.tsx
 * About:
 *   Root React component for ValLG. Configures routing between Dashboard,
 *   Search, Results, Settings, Maps, Directories, Sources, and Login pages.
 *   Provides auth context and API client initialization.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DashboardPage from './pages/DashboardPage';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';
import RecordDetailPage from './pages/RecordDetailPage';
import SettingsPage from './pages/SettingsPage';
import MapsPage from './pages/MapsPage';
import DirectoriesPage from './pages/DirectoriesPage';
import SourcesPage from './pages/SourcesPage';
import DiscoveryPage from './pages/DiscoveryPage';
import Layout from './components/Layout';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
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
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
