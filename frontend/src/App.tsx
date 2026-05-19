import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";
import IncidentDetail from "./pages/IncidentDetail";
import Topology from "./pages/Topology";
import NLPAssistant from "./pages/NLPAssistant";
import CinematicReplay from "./pages/CinematicReplay";
import IncidentCommandCenter from "./pages/IncidentCommandCenter";
import AIAgents from "./pages/AIAgents";
import InfraAnalytics from "./pages/InfraAnalytics";
import ChaosLab from "./pages/ChaosLab";
import SecurityResilience from "./pages/SecurityResilience";
import SystemSettings from "./pages/SystemSettings";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"                  element={<Dashboard />} />
        <Route path="/incidents"         element={<Incidents />} />
        <Route path="/incidents/:id"     element={<IncidentDetail />} />
        <Route path="/topology"          element={<Topology />} />
        <Route path="/nlp"               element={<NLPAssistant />} />
        <Route path="/replay/:id"        element={<CinematicReplay />} />
        <Route path="/incident-command"  element={<IncidentCommandCenter />} />
        <Route path="/ai-agents"         element={<AIAgents />} />
        <Route path="/analytics"         element={<InfraAnalytics />} />
        <Route path="/chaos-lab"         element={<ChaosLab />} />
        <Route path="/security"          element={<SecurityResilience />} />
        <Route path="/settings"          element={<SystemSettings />} />
      </Routes>
    </Layout>
  );
}
