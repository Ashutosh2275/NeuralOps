import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";
import IncidentDetail from "./pages/IncidentDetail";
import Investigations from "./pages/Investigations";
import Topology from "./pages/Topology";
import Workloads from "./pages/Workloads";
import { Knowledge } from "./pages/Knowledge";
import { Tools } from "./pages/Tools";
import { Audit } from "./pages/Audit";
import { SystemSettings } from "./pages/SystemSettings";

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* ── Operations Domain ── */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:id" element={<Investigations />} />

        {/* ── Environment Domain ── */}
        <Route path="/topology" element={<Topology />} />
        <Route path="/workloads" element={<Workloads />} />
        <Route path="/workloads/:namespace/:pod" element={<Workloads />} />

        {/* ── Intelligence Domain ── */}
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="/knowledge/:documentId" element={<Knowledge />} />

        {/* ── Technical Diagnostic Tools ── */}
        <Route path="/tools" element={<Tools />} />

        {/* ── Governance Domain ── */}
        <Route path="/audit" element={<Audit />} />
        <Route path="/settings" element={<SystemSettings />} />
      </Routes>
    </Layout>
  );
}
