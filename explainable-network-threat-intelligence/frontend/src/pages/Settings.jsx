import { useState } from "react";
import { Settings as SettingsIcon, Shield, Sliders, Database, Server, Info, CheckCircle } from "lucide-react";

export default function Settings() {
  const [threshold, setThreshold] = useState(0.70);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [defaultMethod, setDefaultMethod] = useState("shap");
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "900px" }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: "22px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "10px" }}>
          <SettingsIcon color="#3b82f6" size={24} />
          System Settings & Configuration
        </h2>
        <p style={{ color: "#64748b", marginTop: "4px", fontSize: "13px" }}>
          Manage detection parameters, explainability preferences, and system thresholds.
        </p>
      </div>

      {saved && (
        <div style={{ background: "#dcfce7", color: "#15803d", padding: "12px 16px", borderRadius: "8px", display: "flex", alignItems: "center", gap: "8px", fontWeight: 600, fontSize: "13px" }}>
          <CheckCircle size={18} />
          Settings updated successfully!
        </div>
      )}

      {/* Settings Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>

        {/* Card 1: Threat Detection Parameters */}
        <div style={{ background: "white", padding: "20px", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "15px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
            <Sliders size={18} color="#3b82f6" />
            Detection & Uncertainty
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                Confidence Threshold: {(threshold * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                style={{ width: "100%" }}
              />
              <span style={{ fontSize: "11px", color: "#64748b" }}>
                Flows with confidence &lt; {(threshold * 100).toFixed(0)}% are marked for Manual Review.
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                Dashboard Auto-Refresh (Seconds)
              </label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                style={{ width: "100%", padding: "8px 10px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "13px" }}
              >
                <option value={3}>3 Seconds (High Frequency)</option>
                <option value={5}>5 Seconds (Recommended)</option>
                <option value={10}>10 Seconds</option>
                <option value={30}>30 Seconds</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card 2: Explainability Defaults */}
        <div style={{ background: "white", padding: "20px", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "15px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
            <Shield size={18} color="#3b82f6" />
            Explainable AI Defaults
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                Default Explanation Method
              </label>
              <select
                value={defaultMethod}
                onChange={(e) => setDefaultMethod(e.target.value)}
                style={{ width: "100%", padding: "8px 10px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "13px" }}
              >
                <option value="shap">SHAP (TreeExplainer - Game Theory)</option>
                <option value="lime">LIME (Tabular - Local Surrogate)</option>
              </select>
            </div>

            <div style={{ padding: "12px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "12px", color: "#64748b", lineHeight: "1.5" }}>
              <Info size={14} color="#3b82f6" style={{ display: "inline", marginRight: "4px" }} />
              <strong>SHAP</strong> provides mathematically fair feature attribution. <strong>LIME</strong> creates simplified human-readable condition rules.
            </div>
          </div>
        </div>

        {/* Card 3: Model Architecture Info */}
        <div style={{ background: "white", padding: "20px", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "15px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
            <Server size={18} color="#3b82f6" />
            Machine Learning Engine
          </h3>
          <ul style={{ listStyle: "none", fontSize: "13px", color: "#475569", display: "flex", flexDirection: "column", gap: "8px" }}>
            <li><strong>Model:</strong> Random Forest Classifier (100 Trees)</li>
            <li><strong>Training Dataset:</strong> CIC-IDS2017 Benchmark</li>
            <li><strong>Input Schema:</strong> 78 Network Flow Features</li>
            <li><strong>Target Classes:</strong> 0 (BENIGN), 1 (ATTACK)</li>
            <li><strong>API Endpoint:</strong> <code>http://127.0.0.1:8000</code></li>
          </ul>
        </div>

        {/* Card 4: Database Infrastructure */}
        <div style={{ background: "white", padding: "20px", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "15px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
            <Database size={18} color="#3b82f6" />
            Database & Persistence
          </h3>
          <ul style={{ listStyle: "none", fontSize: "13px", color: "#475569", display: "flex", flexDirection: "column", gap: "8px" }}>
            <li><strong>Database Engine:</strong> MySQL 8.4 Server</li>
            <li><strong>Database Name:</strong> <code>network_threat_intelligence</code></li>
            <li><strong>Tables:</strong> <code>network_flows</code>, <code>attack_predictions</code></li>
            <li><strong>Status:</strong> Active & Connected</li>
          </ul>
        </div>

      </div>

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          onClick={handleSave}
          style={{
            padding: "10px 22px",
            background: "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "13px"
          }}
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
}

