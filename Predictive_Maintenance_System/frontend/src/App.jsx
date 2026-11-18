import { useState, useEffect, useCallback } from "react";
import Dashboard from "./components/Dashboard";

const BACKEND_URL = "http://127.0.0.1:8000";

export default function App() {
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("pm_history")) || [];
    } catch {
      return [];
    }
  });
  const [dbStatus, setDbStatus] = useState(null);

  const fetchHistoryAndStatus = useCallback(async () => {
    try {
      // 1. Fetch DB status
      const statusRes = await fetch(`${BACKEND_URL}/database-status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setDbStatus(statusData);
      }

      // 2. Fetch history from Database
      const histRes = await fetch(`${BACKEND_URL}/history?limit=50`);
      if (histRes.ok) {
        const histData = await histRes.json();
        if (Array.isArray(histData) && histData.length > 0) {
          setHistory(histData);
        }
      }
    } catch (err) {
      console.warn("Backend not yet reachable on startup:", err.message);
    }
  }, []);

  useEffect(() => {
    fetchHistoryAndStatus();
  }, [fetchHistoryAndStatus]);

  useEffect(() => {
    try {
      localStorage.setItem("pm_history", JSON.stringify(history));
    } catch {
      // ignore storage errors
    }
  }, [history]);

  const handleClear = async () => {
    try {
      await fetch(`${BACKEND_URL}/history`, { method: "DELETE" });
    } catch (err) {
      console.warn("Could not delete history on backend:", err.message);
    }
    setHistory([]);
    try {
      localStorage.removeItem("pm_history");
    } catch {
      // ignore
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-4 sm:p-6">
      <Dashboard
        history={history}
        dbStatus={dbStatus}
        onAdd={(item) => setHistory((prev) => [item, ...prev])}
        onClear={handleClear}
      />
    </div>
  );
}
