import { useState, useEffect } from "react";
import axios from "axios";
import { ShieldAlert, ShieldCheck, AlertTriangle, Eye, Sparkles } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Predictions({ onSelectExplain }) {
  const [flows, setFlows] = useState([]);
  const [filterMode, setFilterMode] = useState("ALL_SECURITY"); // "ALL_SECURITY", "ATTACK_ONLY", "LOW_CONFIDENCE"
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFlows = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${API_URL}/flows/explainable`);
        setFlows(res.data.flows || []);
      } catch (err) {
        console.error("Alerts load error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchFlows();
  }, []);

  const attackFlows = flows.filter((f) => f.label === "ATTACK");
  const lowConfFlows = flows.filter((f) => f.confidence < 0.70);

  const displayedFlows =
    filterMode === "ATTACK_ONLY"
      ? attackFlows
      : filterMode === "LOW_CONFIDENCE"
      ? lowConfFlows
      : flows;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "22px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "10px" }}>
            <ShieldAlert color="#ef4444" size={24} />
            Attack Detection & Threat Alerts
          </h2>
          <p style={{ color: "#64748b", marginTop: "4px", fontSize: "13px" }}>
            Real-time security alert console flagging malicious flows and low-confidence anomalies.
          </p>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: "flex", gap: "8px", background: "#e2e8f0", padding: "4px", borderRadius: "8px" }}>
          <button
            onClick={() => setFilterMode("ALL_SECURITY")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "none",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              background: filterMode === "ALL_SECURITY" ? "#3b82f6" : "transparent",
              color: filterMode === "ALL_SECURITY" ? "white" : "#475569",
            }}
          >
            All Flows ({flows.length})
          </button>

          <button
            onClick={() => setFilterMode("ATTACK_ONLY")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "none",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              background: filterMode === "ATTACK_ONLY" ? "#ef4444" : "transparent",
              color: filterMode === "ATTACK_ONLY" ? "white" : "#475569",
            }}
          >
            Attacks ({attackFlows.length})
          </button>

          <button
            onClick={() => setFilterMode("LOW_CONFIDENCE")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "none",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              background: filterMode === "LOW_CONFIDENCE" ? "#f59e0b" : "transparent",
              color: filterMode === "LOW_CONFIDENCE" ? "white" : "#475569",
            }}
          >
            Low Confidence ({lowConfFlows.length})
          </button>
        </div>
      </div>

      {/* Security Status Banner */}
      <div style={{
        background: attackFlows.length > 0 ? "#fee2e2" : "#f0fdf4",
        border: attackFlows.length > 0 ? "1px solid #fecaca" : "1px solid #bbf7d0",
        padding: "16px 20px",
        borderRadius: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {attackFlows.length > 0 ? (
            <AlertTriangle color="#dc2626" size={24} />
          ) : (
            <ShieldCheck color="#16a34a" size={24} />
          )}
          <div>
            <h4 style={{ fontSize: "14px", fontWeight: "bold", color: attackFlows.length > 0 ? "#991b1b" : "#166534" }}>
              {attackFlows.length > 0
                ? `Active Threat Warning: ${attackFlows.length} Malicious Flow(s) Detected!`
                : "Network State: Clean (No Malicious Attacks Detected)"}
            </h4>
            <p style={{ fontSize: "12px", color: attackFlows.length > 0 ? "#b91c1c" : "#15803d", marginTop: "2px" }}>
              {attackFlows.length > 0
                ? "Immediate investigation recommended. Inspect feature attributions with SHAP/LIME below."
                : "All current live traffic streams conform to expected benign traffic baselines."}
            </p>
          </div>
        </div>

        <span style={{ fontSize: "12px", fontWeight: 600, color: "#64748b" }}>
          Threshold: 0.70 Confidence
        </span>
      </div>

      {/* Alerts Table */}
      <div style={{ background: "white", borderRadius: "10px", padding: "18px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        {loading ? (
          <p style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>Loading threat telemetry...</p>
        ) : displayedFlows.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>
            <ShieldCheck size={36} color="#22c55e" style={{ margin: "0 auto 10px" }} />
            <p style={{ fontWeight: 600 }}>No security threats in this category.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Flow ID</th>
                  <th>Source IP</th>
                  <th>Destination IP</th>
                  <th>Port</th>
                  <th>Threat Label</th>
                  <th>Confidence</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {displayedFlows.map((f) => (
                  <tr key={f.flow_id}>
                    <td style={{ fontWeight: 600 }}>#{f.flow_id}</td>
                    <td title={f.src_ip}>{f.src_ip}</td>
                    <td title={f.dst_ip}>{f.dst_ip}</td>
                    <td>{f.dst_port}</td>
                    <td>
                      <span className={f.label === "ATTACK" ? "attack-label" : "benign-label"}>
                        {f.label}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{(f.confidence * 100).toFixed(1)}%</td>
                    <td>
                      {onSelectExplain && (
                        <button
                          onClick={() => onSelectExplain(f)}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            padding: "4px 10px",
                            background: "#eff6ff",
                            color: "#2563eb",
                            border: "1px solid #bfdbfe",
                            borderRadius: "6px",
                            fontSize: "12px",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          <Sparkles size={13} />
                          Explain
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

