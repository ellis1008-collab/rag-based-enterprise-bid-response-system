import type { ReactNode } from "react";

type AppLayoutProps = {
  children: ReactNode;
  currentPath: string;
  navigate: (path: string) => void;
};

const navItems = [
  { path: "/", label: "仪表盘" },
  { path: "/projects", label: "招标项目" },
  { path: "/knowledge", label: "知识库" },
  { path: "/models", label: "模型配置" },
];

export function AppLayout({ children, currentPath, navigate }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-bidpilot-surface text-bidpilot-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-bidpilot-line bg-white lg:block">
        <div className="flex h-16 items-center border-b border-bidpilot-line px-6">
          <div className="text-base font-semibold">招投标智能响应系统</div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <button
              key={item.path}
              className={`w-full rounded-md px-3 py-2 text-left text-sm font-medium ${
                isActive(currentPath, item.path)
                  ? "bg-teal-50 text-teal-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
              type="button"
              onClick={() => navigate(item.path)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-bidpilot-line bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
          <div className="mb-3 text-base font-semibold">招投标智能响应系统</div>
          <div className="flex gap-2 overflow-x-auto">
            {navItems.map((item) => (
              <button
                key={item.path}
                className={`shrink-0 rounded-md px-3 py-1.5 text-sm ${
                  isActive(currentPath, item.path) ? "bg-teal-50 text-teal-700" : "bg-slate-100 text-slate-600"
                }`}
                type="button"
                onClick={() => navigate(item.path)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function isActive(currentPath: string, itemPath: string) {
  if (itemPath === "/") {
    return currentPath === "/";
  }
  return currentPath.startsWith(itemPath);
}
