import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";
import IncidentDetail from "./pages/IncidentDetail";
import Topology from "./pages/Topology";
import NLPAssistant from "./pages/NLPAssistant";
import CinematicReplay from "./pages/CinematicReplay";
import EnterpriseCommandCenter from "./pages/EnterpriseCommandCenter";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/topology" element={<Topology />} />
        <Route path="/nlp" element={<NLPAssistant />} />
        <Route path="/replay/:id" element={<CinematicReplay />} />
        <Route path="/command-center" element={<EnterpriseCommandCenter />} />
      </Routes>
    </Layout>
  );
}

