import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import Resources from './pages/Resources';
import Hospitals from './pages/Hospitals';
import RiskZones from './pages/RiskZones';
import AnalyticsPage from './pages/AnalyticsPage';
import Reports from './pages/Reports';
import UserPortal from './pages/UserPortal';
import DriverPortal from './pages/DriverPortal';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/user" element={<UserPortal />} />
        <Route path="/driver" element={<DriverPortal />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/hospitals" element={<Hospitals />} />
          <Route path="/risk-zones" element={<RiskZones />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
