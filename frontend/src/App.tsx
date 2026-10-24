import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ToastProvider } from "./components/ui";
import { DashboardPage } from "./pages/DashboardPage";
import { DependencyPage } from "./pages/DependencyPage";
import { DocsPage } from "./pages/DocsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HmacPage } from "./pages/HmacPage";
import { IntegrityPage } from "./pages/IntegrityPage";
import { ProvenancePage } from "./pages/ProvenancePage";
import { SignaturePage } from "./pages/SignaturePage";
import { SbomPage } from "./pages/SbomPage";
import { SourcesPage } from "./pages/SourcesPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { VulnerabilityPage } from "./pages/VulnerabilityPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/integrity" element={<IntegrityPage />} />
        <Route path="/hmac" element={<HmacPage />} />
        <Route path="/signatures" element={<SignaturePage />} />
        <Route path="/provenance" element={<ProvenancePage />} />
        <Route path="/dependencies" element={<DependencyPage />} />
        <Route path="/sbom" element={<SbomPage />} />
        <Route path="/vulnerabilities" element={<VulnerabilityPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/reports" element={<HistoryPage />} />
        <Route path="/documentation" element={<DocsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppRoutes />
      </ToastProvider>
    </BrowserRouter>
  );
}
