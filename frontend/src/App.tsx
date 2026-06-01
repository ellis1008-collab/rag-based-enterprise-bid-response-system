import { useCallback, useEffect, useMemo, useState } from "react";

import { AppLayout } from "./components/AppLayout";
import { ErrorBlock } from "./components/StateBlock";
import { AgentRunsPage } from "./pages/AgentRunsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgeBasePage } from "./pages/KnowledgeBasePage";
import { ModelSettingsPage } from "./pages/ModelSettingsPage";
import { ResponseMatrixPage } from "./pages/ResponseMatrixPage";
import { RfpProjectDetailPage } from "./pages/RfpProjectDetailPage";
import { RfpProjectListPage } from "./pages/RfpProjectListPage";

function App() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    function handlePopState() {
      setPath(window.location.pathname);
    }
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = useCallback((nextPath: string) => {
    window.history.pushState(null, "", nextPath);
    setPath(nextPath);
  }, []);

  const page = useMemo(() => resolvePage(path, navigate), [path, navigate]);

  return (
    <AppLayout currentPath={path} navigate={navigate}>
      {page}
    </AppLayout>
  );
}

function resolvePage(path: string, navigate: (path: string) => void) {
  if (path === "/") {
    return <DashboardPage navigate={navigate} />;
  }
  if (path === "/projects") {
    return <RfpProjectListPage navigate={navigate} />;
  }
  if (path === "/knowledge") {
    return <KnowledgeBasePage />;
  }
  if (path === "/models") {
    return <ModelSettingsPage />;
  }

  const responsesMatch = path.match(/^\/projects\/(\d+)\/responses$/);
  if (responsesMatch) {
    return <ResponseMatrixPage projectId={Number(responsesMatch[1])} navigate={navigate} />;
  }

  const runsMatch = path.match(/^\/projects\/(\d+)\/runs$/);
  if (runsMatch) {
    return <AgentRunsPage projectId={Number(runsMatch[1])} navigate={navigate} />;
  }

  const projectMatch = path.match(/^\/projects\/(\d+)$/);
  if (projectMatch) {
    return <RfpProjectDetailPage projectId={Number(projectMatch[1])} navigate={navigate} />;
  }

  return <ErrorBlock title="页面不存在" body="请从左侧导航进入可用页面。" />;
}

export default App;
