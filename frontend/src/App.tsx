import { Component, useEffect, type ErrorInfo, type ReactNode } from "react";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { motion, MotionConfig, useReducedMotion } from "framer-motion";
import AppShell from "./components/AppShell";
import { EmptyState, LoadingSkeleton, Toast } from "./components/ui";
import Home from "./pages/Home";
import Items from "./pages/Items";
import AddItem from "./pages/AddItem";
import ItemDetail from "./pages/ItemDetail";
import Reminders from "./pages/Reminders";
import Consumables from "./pages/Consumables";
import Repairs from "./pages/Repairs";
import Assistant from "./pages/Assistant";
import Statistics from "./pages/Statistics";
import { useStore } from "./store";
import ShareItem from "./pages/ShareItem";
class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI rendering error", error.message, info.componentStack);
  }
  render() {
    return this.state.failed ? (
      <main className="page">
        <EmptyState
          title="页面暂时遇到问题"
          description="请刷新重试；本地档案仍保存在数据库。"
          action={
            <button className="button primary" onClick={() => location.reload()}>
              重新加载
            </button>
          }
        />
      </main>
    ) : (
      this.props.children
    );
  }
}
export default function App() {
  return location.pathname.startsWith("/share/") ? <ShareItem /> : <ManagementApp />;
}
function ManagementApp() {
  const { data, loading, error, refresh, toast } = useStore();
  const location = useLocation();
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);
  useEffect(() => {
    const timer = setInterval(() => void refresh(), 60000);
    const focus = () => void refresh();
    window.addEventListener("focus", focus);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", focus);
    };
  }, [refresh]);
  return (
    <MotionConfig reducedMotion="user">
      <ErrorBoundary>
        <AppShell>
          {loading ? (
            <main className="page">
              <LoadingSkeleton />
            </main>
          ) : error && !data ? (
            <main className="page">
              <EmptyState
                title="暂时无法连接本地服务"
                description={error}
                action={
                  <button className="button primary" onClick={() => void refresh()}>
                    重新连接
                  </button>
                }
              />
              <p className="notice">
                请先运行后端，再启动前端。只查看 UI 可使用 ?uiDemo=1（合成数据）。
              </p>
            </main>
          ) : (
            <motion.div
              key={location.pathname}
              initial={reduce ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/items" element={<Items />} />
                <Route path="/items/new" element={<AddItem />} />
                <Route path="/items/:id" element={<ItemDetail />} />
                <Route path="/reminders" element={<Reminders />} />
                <Route path="/consumables" element={<Consumables />} />
                <Route path="/repairs" element={<Repairs />} />
                <Route path="/assistant" element={<Assistant />} />
                <Route path="/statistics" element={<Statistics />} />
                <Route
                  path="*"
                  element={
                    <main className="page">
                      <EmptyState title="没有找到这个页面" action={<Link to="/">回到首页</Link>} />
                    </main>
                  }
                />
              </Routes>
            </motion.div>
          )}
          <Toast message={toast} />
          <button className="visually-hidden" onClick={() => navigate("/consumables")}>
            耗材快捷入口
          </button>
        </AppShell>
      </ErrorBoundary>
    </MotionConfig>
  );
}
