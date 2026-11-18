import { useState, useEffect } from "react";
import axios from "axios";

import {
  ShieldCheck,
  LayoutDashboard,
  Activity,
  Network,
  AlertTriangle,
  Settings,
  Search,
  Bell,
  ShieldAlert,
  CircleCheck,
  Sparkles,
  Zap,
  PlusCircle,
  RotateCcw,
  RefreshCw,
  ArrowRight,
  CheckCircle2,
  HelpCircle,
  Info
} from "lucide-react";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import "./App.css";
import Explainability from "./pages/Explainability";
import TrafficMonitoring from "./pages/TrafficMonitoring";
import Predictions from "./pages/Predictions";
import SettingsPage from "./pages/Settings";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [summary, setSummary] = useState({
    total_flows: 0,
    benign_count: 0,
    attack_count: 0,
    average_confidence: 0,
  });

  const [recentPredictions, setRecentPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("info"); // "attack", "benign", "reset", "info"
  const [selectedExplainId, setSelectedExplainId] = useState(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const showToast = (msg, type = "info") => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => {
      setToastMessage("");
    }, 4500);
  };

  // Fetch dashboard data from FastAPI
  const fetchDashboardData = async () => {
    try {
      const [summaryResponse, recentResponse] = await Promise.all([
        axios.get(`${API_URL}/dashboard/summary`),
        axios.get(`${API_URL}/flows/recent`),
      ]);

      setSummary(summaryResponse.data);
      setRecentPredictions(recentResponse.data.predictions || []);
      setLastUpdated(new Date().toLocaleTimeString());
      setError("");
    } catch (err) {
      console.error("API Error:", err);
      setError("Unable to connect to backend. Please ensure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const intervalId = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  // Quick Action: Simulate Live Attack
  const handleTriggerAttack = async () => {
    setActionLoading(true);
    try {
      const res = await axios.post(`${API_URL}/attack/trigger`);
      showToast(
        "🚨 Malicious Attack Injected! AI model flagged it as ATTACK (100% confidence).",
        "attack"
      );
      await fetchDashboardData();
    } catch (err) {
      console.error("Attack trigger error:", err);
      showToast("Failed to trigger test attack. Check backend server.", "info");
    } finally {
      setActionLoading(false);
    }
  };

  // Quick Action: Simulate Benign Safe Traffic
  const handleSimulateBenign = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/traffic/simulate-benign`);
      showToast("🟢 Normal User Traffic Injected! AI model verified it as SAFE (BENIGN).", "benign");
      await fetchDashboardData();
    } catch (err) {
      console.error("Benign trigger error:", err);
      showToast("Failed to simulate benign traffic.", "info");
    } finally {
      setActionLoading(false);
    }
  };

  // Quick Action: Reset Demo Cache
  const handleResetDemo = async () => {
    if (!window.confirm("Reset dashboard to clean baseline demo state?")) return;
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/dashboard/reset`);
      showToast("↺ Dashboard cache reset to clean initial baseline.", "reset");
      await fetchDashboardData();
    } catch (err) {
      console.error("Reset error:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // Jump to Explainability for a specific flow
  const handleExplainFlow = (flowId) => {
    setSelectedExplainId(flowId);
    setCurrentPage("explainability");
  };

  // Prepare chart data in chronological order (oldest to newest)
  const trafficData = recentPredictions
    .slice(0, 10)
    .reverse()
    .map((item) => ({
      time: `#${item.flow_id}`,
      label: item.label,
      confidence: Number((item.confidence * 100).toFixed(1)),
      uncertainty: Number((item.uncertainty * 100).toFixed(1)),
    }));

  // Shorten long IPv6 addresses for clean display
  const formatIp = (ip) => {
    if (!ip || ip === "N/A") return "-";
    if (ip.length > 25 && ip.includes(":")) {
      const parts = ip.split(":");
      return `${parts[0]}:${parts[1]}...${parts[parts.length - 1]}`;
    }
    return ip;
  };

  // Ratio calculations
  const totalSafe = summary.benign_count || 0;
  const totalAttacks = summary.attack_count || 0;
  const totalAll = summary.total_flows || (totalSafe + totalAttacks) || 1;
  const safePercent = Math.round((totalSafe / totalAll) * 100);
  const attackPercent = 100 - safePercent;

  return (
    <div className="app-container">

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={30} />
          <span>ThreatIntel</span>
        </div>

        <p className="menu-heading">MAIN MENU</p>

        <nav>
          <a
            className={`nav-item ${currentPage === "dashboard" ? "active" : ""}`}
            onClick={() => setCurrentPage("dashboard")}
          >
            <LayoutDashboard size={19} />
            Dashboard
          </a>

          <a
            className={`nav-item ${currentPage === "traffic" ? "active" : ""}`}
            onClick={() => setCurrentPage("traffic")}
          >
            <Activity size={19} />
            Network Traffic
          </a>

          <a
            className={`nav-item ${currentPage === "attacks" ? "active" : ""}`}
            onClick={() => setCurrentPage("attacks")}
          >
            <ShieldAlert size={19} />
            Attack Detection
          </a>

          <a
            className={`nav-item ${currentPage === "explainability" ? "active" : ""}`}
            onClick={() => {
              setSelectedExplainId(null);
              setCurrentPage("explainability");
            }}
          >
            <Sparkles size={19} />
            Explainability
          </a>

          <a
            className={`nav-item ${currentPage === "settings" ? "active" : ""}`}
            onClick={() => setCurrentPage("settings")}
          >
            <Settings size={19} />
            Settings
          </a>
        </nav>

        <div className="sidebar-status">
          {error ? (
            <AlertTriangle size={18} color="#ef4444" />
          ) : (
            <CircleCheck size={18} color="#22c55e" />
          )}

          <div>
            <strong>System Status</strong>
            <p>{error ? "Backend offline" : "AI Engine Connected"}</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">

        {/* Topbar */}
        <header className="topbar">
          <div>
            <h2>
              {currentPage === "dashboard" && "Network Threat Intelligence Dashboard"}
              {currentPage === "traffic" && "Network Traffic Monitoring"}
              {currentPage === "attacks" && "Attack Detection & Alerts"}
              {currentPage === "explainability" && "Explainable AI (SHAP & LIME)"}
              {currentPage === "settings" && "System Settings"}
            </h2>
            <p>Machine Learning-Powered Intrusion Detection with Feature Explainability</p>
          </div>

          <div className="topbar-actions">
            <button className="icon-button" onClick={fetchDashboardData} title="Refresh Live Data">
              <RefreshCw size={18} className={actionLoading ? "spin" : ""} />
            </button>
            <div className="profile" title="Admin User">RT</div>
          </div>
        </header>

        {/* Page Switcher */}
        {currentPage === "explainability" && <Explainability initialFlowId={selectedExplainId} />}
        {currentPage === "traffic" && <TrafficMonitoring />}
        {currentPage === "attacks" && (
          <Predictions onSelectExplain={(flow) => handleExplainFlow(flow.flow_id)} />
        )}
        {currentPage === "settings" && <SettingsPage />}

        {/* ===== DASHBOARD MAIN VIEW ===== */}
        {currentPage === "dashboard" && (
          <>
            {/* Top Interactive Banner: Threat Status + Live Testing Buttons */}
            <div
              style={{
                margin: "24px 0 18px",
                padding: "18px 22px",
                borderRadius: "12px",
                background: summary.attack_count > 0 ? "#fef2f2" : "#f0fdf4",
                border: `1.5px solid ${summary.attack_count > 0 ? "#fecaca" : "#bbf7d0"}`,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "14px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)"
              }}
            >
              {/* Left: Status Badge */}
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  style={{
                    width: "44px",
                    height: "44px",
                    borderRadius: "10px",
                    background: summary.attack_count > 0 ? "#fee2e2" : "#dcfce7",
                    display: "grid",
                    placeItems: "center",
                    color: summary.attack_count > 0 ? "#ef4444" : "#16a34a"
                  }}
                >
                  {summary.attack_count > 0 ? <AlertTriangle size={24} /> : <ShieldCheck size={24} />}
                </div>

                <div>
                  <h3
                    style={{
                      fontSize: "16px",
                      fontWeight: "bold",
                      color: summary.attack_count > 0 ? "#991b1b" : "#166534",
                      margin: 0
                    }}
                  >
                    {summary.attack_count > 0
                      ? `⚠️ Threat Detected: ${summary.attack_count} Malicious Attack Flows Flagged`
                      : "🟢 System Secure: Normal Network Traffic"}
                  </h3>
                  <p style={{ margin: "4px 0 0", fontSize: "13px", color: summary.attack_count > 0 ? "#b91c1c" : "#15803d" }}>
                    {summary.attack_count > 0
                      ? "The AI model detected abnormal port scans and anomalous packet rates. Click 'Explain (SHAP)' to see why."
                      : "Continuous live packet sniffer is listening. All network connections conform to safe baseline."}
                  </p>
                </div>
              </div>

              {/* Right: Quick Action Buttons */}
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <button
                  onClick={handleTriggerAttack}
                  disabled={actionLoading}
                  style={{
                    background: "linear-gradient(135deg, #ef4444, #dc2626)",
                    color: "white",
                    border: "none",
                    padding: "9px 15px",
                    borderRadius: "8px",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    boxShadow: "0 2px 6px rgba(239, 68, 68, 0.3)"
                  }}
                  title="Simulate a live PortScan attack right now"
                >
                  <Zap size={16} />
                  Simulate Live Attack
                </button>

                <button
                  onClick={handleSimulateBenign}
                  disabled={actionLoading}
                  style={{
                    background: "#16a34a",
                    color: "white",
                    border: "none",
                    padding: "9px 14px",
                    borderRadius: "8px",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                  }}
                  title="Add safe normal web browsing flow"
                >
                  <PlusCircle size={16} />
                  Add Safe Traffic
                </button>

                <button
                  onClick={handleResetDemo}
                  disabled={actionLoading}
                  style={{
                    background: "#f1f5f9",
                    color: "#475569",
                    border: "1px solid #cbd5e1",
                    padding: "9px 12px",
                    borderRadius: "8px",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                  }}
                  title="Reset to clean initial baseline"
                >
                  <RotateCcw size={15} />
                  Reset
                </button>
              </div>
            </div>

            {/* Toast Feedback Notification */}
            {toastMessage && (
              <div
                style={{
                  marginBottom: "18px",
                  padding: "12px 18px",
                  borderRadius: "8px",
                  background: toastType === "attack" ? "#fee2e2" : toastType === "benign" ? "#dcfce7" : "#e0f2fe",
                  color: toastType === "attack" ? "#991b1b" : toastType === "benign" ? "#166534" : "#075985",
                  fontWeight: 600,
                  fontSize: "13px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  animation: "fadeIn 0.3s ease"
                }}
              >
                {toastType === "attack" ? <AlertTriangle size={17} /> : <CheckCircle2 size={17} />}
                {toastMessage}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {/* 4 Clean Statistics Cards */}
            <section className="stats-grid">
              {/* Card 1: Total Flows */}
              <div className="stat-card">
                <div className="stat-top">
                  <span>Total Traffic Analyzed</span>
                  <Network size={20} color="#3b82f6" />
                </div>
                <h2>{loading ? "..." : summary.total_flows}</h2>
                <p>Total network flows inspected</p>
              </div>

              {/* Card 2: Safe / Benign */}
              <div className="stat-card" style={{ borderLeft: "4px solid #22c55e" }}>
                <div className="stat-top">
                  <span style={{ color: "#16a34a", fontWeight: "bold" }}>Safe (Benign) Traffic</span>
                  <ShieldCheck size={20} color="#22c55e" />
                </div>
                <h2 style={{ color: "#16a34a" }}>{loading ? "..." : summary.benign_count}</h2>
                <p>Normal web & DNS traffic</p>
              </div>

              {/* Card 3: Attacks Detected */}
              <div className="stat-card" style={{ borderLeft: "4px solid #ef4444" }}>
                <div className="stat-top">
                  <span style={{ color: "#dc2626", fontWeight: "bold" }}>Attacks Detected</span>
                  <AlertTriangle size={20} color="#ef4444" />
                </div>
                <h2 style={{ color: "#dc2626" }}>{loading ? "..." : summary.attack_count}</h2>
                <p>Port scans & malicious probes</p>
              </div>

              {/* Card 4: AI Confidence */}
              <div className="stat-card" style={{ borderLeft: "4px solid #3b82f6" }}>
                <div className="stat-top">
                  <span style={{ color: "#2563eb", fontWeight: "bold" }}>Model Confidence</span>
                  <Activity size={20} color="#3b82f6" />
                </div>
                <h2 style={{ color: "#2563eb" }}>
                  {loading ? "..." : `${(summary.average_confidence * 100).toFixed(1)}%`}
                </h2>
                <p>Random Forest certainty level</p>
              </div>
            </section>

            {/* Visual Security Distribution Bar */}
            <div
              style={{
                background: "white",
                padding: "16px 20px",
                borderRadius: "10px",
                border: "1px solid #e2e8f0",
                marginBottom: "24px"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px", fontWeight: 600 }}>
                <span style={{ color: "#16a34a" }}>🟢 Safe Traffic: {safePercent}% ({summary.benign_count} flows)</span>
                <span style={{ color: "#dc2626" }}>🔴 Attack Threats: {attackPercent}% ({summary.attack_count} flows)</span>
              </div>
              <div style={{ width: "100%", height: "12px", background: "#fee2e2", borderRadius: "999px", overflow: "hidden", display: "flex" }}>
                <div style={{ width: `${safePercent}%`, background: "#22c55e", height: "100%", transition: "width 0.4s ease" }} />
                <div style={{ width: `${attackPercent}%`, background: "#ef4444", height: "100%", transition: "width 0.4s ease" }} />
              </div>
            </div>

            {/* Charts & System Architecture */}
            <section className="content-grid">
              <div className="panel traffic-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Network Traffic Analysis</h3>
                    <p>Timeline of model confidence (%) and uncertainty score (%) for recent flows</p>
                  </div>
                </div>

                <div className="chart-container">
                  {trafficData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={trafficData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="time" />
                        <YAxis domain={[0, 100]} unit="%" />
                        <Tooltip />
                        <Area
                          type="monotone"
                          dataKey="confidence"
                          name="Confidence (%)"
                          stroke="#2563eb"
                          fill="#2563eb"
                          fillOpacity={0.15}
                        />
                        <Area
                          type="monotone"
                          dataKey="uncertainty"
                          name="Uncertainty (%)"
                          stroke="#f59e0b"
                          fill="#f59e0b"
                          fillOpacity={0.18}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="empty-state">
                      <Activity size={30} />
                      <p>No prediction data available yet.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* System Architecture Card */}
              <div className="panel system-panel">
                <h3>System Architecture</h3>

                <div className="system-info">
                  <span>ML Model</span>
                  <strong>Random Forest Classifier</strong>
                </div>

                <div className="system-info">
                  <span>Feature Extraction</span>
                  <strong>78 Features (CICFlowMeter)</strong>
                </div>

                <div className="system-info">
                  <span>Backend Engine</span>
                  <strong className="connected">FastAPI (Python)</strong>
                </div>

                <div className="system-info">
                  <span>Data Store</span>
                  <strong className="connected">Live Cache + MySQL</strong>
                </div>

                <div className="system-info">
                  <span>Explainability (XAI)</span>
                  <strong style={{ color: "#7c3aed" }}>SHAP & LIME</strong>
                </div>
              </div>
            </section>

            {/* Recent Predictions Table with One-Click Explain */}
            <section className="panel recent-panel">
              <div className="panel-heading" style={{ marginBottom: "14px" }}>
                <div>
                  <h3>Recent Network Predictions (Live Feed)</h3>
                  <p>Real-time stream of classified connections. Click <strong>"Explain"</strong> to see why the AI made each decision.</p>
                </div>

                <span style={{ fontSize: "12px", background: "#f1f5f9", padding: "6px 12px", borderRadius: "6px", color: "#64748b" }}>
                  Showing latest {recentPredictions.length} flows
                </span>
              </div>

              {loading ? (
                <div className="empty-state">
                  <p>Loading network traffic...</p>
                </div>
              ) : recentPredictions.length > 0 ? (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Flow ID</th>
                        <th>Source IP</th>
                        <th>Destination IP</th>
                        <th>Protocol</th>
                        <th>Detection Result</th>
                        <th>Confidence</th>
                        <th>Uncertainty</th>
                        <th>AI Explainability</th>
                      </tr>
                    </thead>

                    <tbody>
                      {recentPredictions.map((item) => (
                        <tr key={item.flow_id} style={{ background: item.label === "ATTACK" ? "#fef2f2" : "inherit" }}>
                          <td style={{ fontWeight: 600 }}>#{item.flow_id}</td>
                          <td title={item.source_ip}>{formatIp(item.source_ip)}</td>
                          <td title={item.destination_ip}>{formatIp(item.destination_ip)}</td>
                          <td>
                            <span style={{ fontSize: "12px", background: "#f1f5f9", padding: "3px 8px", borderRadius: "4px" }}>
                              {item.protocol || "TCP"}
                            </span>
                          </td>

                          <td>
                            <span
                              className={
                                item.label === "ATTACK"
                                  ? "attack-label"
                                  : "benign-label"
                              }
                            >
                              {item.label === "ATTACK" ? "🚨 ATTACK" : "✓ BENIGN"}
                            </span>
                          </td>

                          <td style={{ fontWeight: 600, color: item.label === "ATTACK" ? "#dc2626" : "#16a34a" }}>
                            {(item.confidence * 100).toFixed(1)}%
                          </td>

                          <td style={{ color: item.uncertainty > 0.3 ? "#d97706" : "#64748b" }}>
                            {(item.uncertainty * 100).toFixed(1)}%
                          </td>

                          <td>
                            <button
                              onClick={() => handleExplainFlow(item.flow_id)}
                              style={{
                                background: item.label === "ATTACK" ? "#fee2e2" : "#eff6ff",
                                color: item.label === "ATTACK" ? "#b91c1c" : "#2563eb",
                                border: `1px solid ${item.label === "ATTACK" ? "#fca5a5" : "#bfdbfe"}`,
                                padding: "5px 10px",
                                borderRadius: "6px",
                                fontSize: "12px",
                                fontWeight: 600,
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                gap: "5px"
                              }}
                              title="Inspect SHAP feature contribution bar chart for this connection"
                            >
                              <Sparkles size={13} />
                              Explain (SHAP)
                              <ArrowRight size={13} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <Activity size={30} />
                  <p>No network predictions found.</p>
                </div>
              )}
            </section>

            {/* Educational / Viva Guide Card */}
            <div
              style={{
                background: "white",
                padding: "20px 24px",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                marginTop: "10px",
                boxShadow: "0 2px 6px rgba(0,0,0,0.02)"
              }}
            >
              <h4 style={{ fontSize: "15px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
                <HelpCircle size={18} color="#3b82f6" />
                Quick Guide: Understanding This Security Intelligence System
              </h4>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
                <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                  <strong style={{ color: "#16a34a", display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", fontSize: "13px" }}>
                    <ShieldCheck size={16} /> 1. Safe (BENIGN) Traffic
                  </strong>
                  <p style={{ fontSize: "12px", color: "#64748b", margin: 0, lineHeight: 1.5 }}>
                    Legitimate user connections such as web browsing (HTTPS/Port 443), DNS resolution (Port 53), and cloud API calls.
                  </p>
                </div>

                <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                  <strong style={{ color: "#dc2626", display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", fontSize: "13px" }}>
                    <AlertTriangle size={16} /> 2. Network Attack (ATTACK)
                  </strong>
                  <p style={{ fontSize: "12px", color: "#64748b", margin: 0, lineHeight: 1.5 }}>
                    Malicious network behaviors including rapid TCP SYN port scanning, DoS floods, and unauthorized host probing.
                  </p>
                </div>

                <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                  <strong style={{ color: "#7c3aed", display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", fontSize: "13px" }}>
                    <Sparkles size={16} /> 3. Explainability (SHAP & LIME)
                  </strong>
                  <p style={{ fontSize: "12px", color: "#64748b", margin: 0, lineHeight: 1.5 }}>
                    Instead of a black box, SHAP shows the exact features (e.g. packet rate, packet size) that convinced the AI to flag the threat.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        <footer>
          Explainable Network Threat Intelligence System • ML-Based Attack Detection with SHAP & LIME
        </footer>

      </main>
    </div>
  );
}

export default App;
