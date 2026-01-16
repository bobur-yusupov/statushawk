import { BrowserRouter, Routes, Route, Outlet, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from './layouts/DashboardLayout';
import './App.css'
import OverviewPage from './features/dashboard/OverviewPage';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import LoginPage from './features/auth/LoginPage';
import MonitorsPage from './features/monitors/MonitorsPage';
import MonitorDetailPage from './features/monitors/MonitorDetailPage';
import RegisterPage from './features/auth/RegisterPage';
import SettingsPage from './features/settings/SettingsPage';

const queryClient = new QueryClient();

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path='/login' element={<LoginPage />} />
            <Route path='/register' element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path='/' element={<OverviewPage />} />
                <Route path='/monitors' element={<MonitorsPage />} />
                <Route path='/monitors/:id' element={<MonitorDetailPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route path='*' element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
