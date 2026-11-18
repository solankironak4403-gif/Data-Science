import { useState, useEffect } from "react";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import {
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Cpu,
  Layers,
  ArrowRight,
  Info,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Explainability({ initialFlowId }) {
  const [flows, setFlows] = useState([]);
  const [selectedFlow, setSelectedFlow] = useState(null);
  const [method, setMethod] = useState("shap"); // "shap" or "lime"
  const [topN, setTopN] = useState(10);
  const [explanation, setExplanation] = useState(null);
  const [loadingFlows, setLoadingFlows] = useState(true);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [error, setError] = useState("");

  // 1. Fetch explainable flows from backend on mount
  useEffect(() => {
    const fetchFlows = async () => {
      setLoadingFlows(true);
      try {
        const res = await axios.get(`${API_URL}/flows/explainable`);
        const flowList = res.data.flows || [];
        setFlows(flowList);
        if (flowList.length > 0) {
          if (initialFlowId) {
            const match = flowList.find((f) => f.flow_id === initialFlowId);
            setSelectedFlow(match || flowList[0]);
          } else {
            setSelectedFlow(flowList[0]);
          }
        }
        setError("");
      } catch (err) {
        console.error("Failed to load explainable flows:", err);
        setError("Unable to load network flows for explanation.");
      } finally {
        setLoadingFlows(false);
      }
    };

    fetchFlows();
  }, []);

  // 2. Fetch explanation whenever selected flow, method, or topN changes
  useEffect(() => {
    if (!selectedFlow) return;

    const fetchExplanation = async () => {
      setLoadingExplain(true);
      setError("");
      try {
        const payload = {
          flow: selectedFlow.features || selectedFlow,
          method: method,
          top_n: Number(topN),
        };
        const res = await axios.post(`${API_URL}/explain`, payload);
        setExplanation(res.data);
      } catch (err) {
        console.error("Failed to generate explanation:", err);
        setError("Error generating explanation. Check backend logs.");
      } finally {
        setLoadingExplain(false);
      }
    };

    fetchExplanation();
  }, [selectedFlow, method, topN]);

  // Format chart data for Recharts
  const chartData = (explanation?.top_features || []).map((item) => ({
    feature: item.feature.length > 25 ? item.feature.substring(0, 25) + "..." : item.feature,
    fullFeature: item.feature,
    value: item.value !== undefined && item.value !== null ? item.value : "N/A",
    importance: item.importance,
    effect: item.effect,
  }));

  return (
    <div className="explainability-page" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      
      {/* Page Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "24px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "10px" }}>
            <Sparkles color="#3b82f6" size={26} />
            Explainable AI (XAI) Dashboard
          </h2>
          <p style={{ color: "#64748b", marginTop: "4px", fontSize: "14px" }}>
            Interpretable Machine Learning: Discover why the Random Forest classified each network flow as Benign or Attack.
          </p>
        </div>

        {/* Method Switcher Buttons */}
        <div style={{ display: "flex", gap: "10px", background: "#e2e8f0", padding: "4px", borderRadius: "8px" }}>
          <button
            onClick={() => setMethod("shap")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
              background: method === "shap" ? "#3b82f6" : "transparent",
              color: method === "shap" ? "white" : "#475569",
              transition: "all 0.2s ease",
            }}
          >
            <Cpu size={16} />
            SHAP (TreeExplainer)
          </button>

          <button
            onClick={() => setMethod("lime")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
              background: method === "lime" ? "#3b82f6" : "transparent",
              color: method === "lime" ? "white" : "#475569",
              transition: "all 0.2s ease",
            }}
          >
            <Layers size={16} />
            LIME (Surrogate)
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: "#fee2e2", borderLeft: "4px solid #ef4444", padding: "12px 16px", borderRadius: "6px", color: "#991b1b" }}>
          <strong>Notice: </strong>{error}
        </div>
      )}

      {/* Main Grid: Flow Selection on Left / Top, Explanation Chart on Right / Bottom */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "24px" }}>

        {/* Left Column: Network Flows Table */}
        <div style={{ background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: "bold", color: "#1e293b" }}>
              Select a Network Flow to Explain
            </h3>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              {flows.length} live flows available
            </span>
          </div>

          {loadingFlows ? (
            <p style={{ color: "#64748b", padding: "20px", textAlign: "center" }}>Loading captured flows...</p>
          ) : flows.length === 0 ? (
            <p style={{ color: "#64748b", padding: "20px", textAlign: "center" }}>No flows recorded yet. Run live detection first.</p>
          ) : (
            <div className="table-container" style={{ maxHeight: "450px", overflowY: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Flow</th>
                    <th>Source IP</th>
                    <th>Port</th>
                    <th>Proto</th>
                    <th>Prediction</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {flows.map((f) => {
                    const isSelected = selectedFlow?.flow_id === f.flow_id;
                    return (
                      <tr
                        key={f.flow_id}
                        onClick={() => setSelectedFlow(f)}
                        style={{
                          cursor: "pointer",
                          backgroundColor: isSelected ? "#eff6ff" : "inherit",
                          borderLeft: isSelected ? "4px solid #3b82f6" : "4px solid transparent",
                          transition: "background 0.15s ease",
                        }}
                      >
                        <td style={{ fontWeight: 600 }}>#{f.flow_id}</td>
                        <td title={f.src_ip}>{f.src_ip.length > 18 ? f.src_ip.substring(0, 18) + "..." : f.src_ip}</td>
                        <td>{f.dst_port}</td>
                        <td>{f.protocol}</td>
                        <td>
                          <span className={f.label === "ATTACK" ? "attack-label" : "benign-label"}>
                            {f.label}
                          </span>
                        </td>
                        <td style={{ fontWeight: 500 }}>
                          {(f.confidence * 100).toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Quick Flow Details Card */}
          {selectedFlow && (
            <div style={{ marginTop: "16px", padding: "14px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                <span><strong>Source:</strong> {selectedFlow.src_ip}</span>
                <span><strong>Destination:</strong> {selectedFlow.dst_ip}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginTop: "6px" }}>
                <span><strong>Target Port:</strong> {selectedFlow.dst_port} ({selectedFlow.protocol})</span>
                <span><strong>Current Status:</strong> {selectedFlow.label}</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: SHAP / LIME Explanation Chart */}
        <div style={{ background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px" }}>
                {method.toUpperCase()} Feature Contribution
                {explanation && (
                  <span style={{ fontSize: "12px", padding: "2px 8px", borderRadius: "999px", background: explanation.label === "ATTACK" ? "#fee2e2" : "#dcfce7", color: explanation.label === "ATTACK" ? "#b91c1c" : "#15803d" }}>
                    {explanation.label} ({ (explanation.confidence * 100).toFixed(1) }%)
                  </span>
                )}
              </h3>
              <p style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>
                {method === "shap"
                  ? "Positive SHAP (Red) pushes towards Attack; Negative SHAP (Blue) pushes towards Benign."
                  : "Positive LIME weights support Attack prediction; Negative weights support Benign."}
              </p>
            </div>

            {/* Top N Selector */}
            <select
              value={topN}
              onChange={(e) => setTopN(e.target.value)}
              style={{ padding: "6px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "13px" }}
            >
              <option value={5}>Top 5 Features</option>
              <option value={10}>Top 10 Features</option>
              <option value={15}>Top 15 Features</option>
            </select>
          </div>

          {loadingExplain ? (
            <div style={{ height: "350px", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>
              Computing {method.toUpperCase()} explanation values...
            </div>
          ) : chartData.length === 0 ? (
            <div style={{ height: "350px", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>
              Select a flow to view feature explanations.
            </div>
          ) : (
            <div>
              {/* Horizontal Bar Chart */}
              <div style={{ height: "340px", width: "100%" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    layout="vertical"
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 70, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis
                      dataKey="feature"
                      type="category"
                      tick={{ fontSize: 11 }}
                      width={130}
                    />
                    <Tooltip
                      formatter={(val, name, item) => [
                        `${val > 0 ? "+" : ""}${val} (${item.payload.effect})`,
                        "Importance",
                      ]}
                      labelFormatter={(label, items) => {
                        if (items && items[0]) {
                          return `${items[0].payload.fullFeature} (Value: ${items[0].payload.value})`;
                        }
                        return label;
                      }}
                    />
                    <ReferenceLine x={0} stroke="#94a3b8" />
                    <Bar dataKey="importance">
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.importance >= 0 ? "#ef4444" : "#3b82f6"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Explanatory Legend */}
              <div style={{ display: "flex", justifyContent: "center", gap: "24px", marginTop: "12px", fontSize: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "12px", height: "12px", background: "#ef4444", borderRadius: "2px" }}></span>
                  <span style={{ color: "#475569" }}>Pushes towards <strong>ATTACK</strong> (+ contribution)</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "12px", height: "12px", background: "#3b82f6", borderRadius: "2px" }}></span>
                  <span style={{ color: "#475569" }}>Pushes towards <strong>BENIGN</strong> (- contribution)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature Breakdown Table */}
      {explanation && explanation.top_features && (
        <div style={{ background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h3 style={{ fontSize: "16px", fontWeight: "bold", color: "#1e293b", marginBottom: "14px" }}>
            Detailed Feature Breakdown ({method.toUpperCase()})
          </h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Feature Name</th>
                  <th>Feature Value</th>
                  <th>Contribution Score</th>
                  <th>Directional Effect</th>
                </tr>
              </thead>
              <tbody>
                {explanation.top_features.map((feat, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>#{idx + 1}</td>
                    <td style={{ fontWeight: 500 }}>{feat.feature}</td>
                    <td>{feat.value !== undefined && feat.value !== null ? String(feat.value) : "Rule Condition"}</td>
                    <td style={{ fontWeight: 600, color: feat.importance >= 0 ? "#b91c1c" : "#1d4ed8" }}>
                      {feat.importance >= 0 ? `+${feat.importance.toFixed(4)}` : feat.importance.toFixed(4)}
                    </td>
                    <td>
                      <span style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "12px",
                        fontWeight: 600,
                        color: feat.importance >= 0 ? "#b91c1c" : "#15803d",
                        background: feat.importance >= 0 ? "#fee2e2" : "#dcfce7",
                        padding: "3px 10px",
                        borderRadius: "999px"
                      }}>
                        {feat.importance >= 0 ? <ShieldAlert size={14} /> : <ShieldCheck size={14} />}
                        {feat.effect}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Educational Card for University Evaluators */}
      <div style={{ background: "#f8fafc", borderRadius: "12px", padding: "18px 22px", border: "1px solid #e2e8f0" }}>
        <h4 style={{ fontSize: "14px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "8px" }}>
          <Info size={16} color="#3b82f6" />
          Technical Note: SHAP vs. LIME Comparison
        </h4>
        <p style={{ fontSize: "13px", color: "#475569", marginTop: "6px", lineHeight: "1.6" }}>
          <strong>SHAP (TreeExplainer)</strong> computes exact Shapley values derived from game theory, guaranteeing fair additive attribution ($\sum \phi_i = f(x) - E[f(x)]$). It is globally consistent and deterministic.
          <br />
          <strong>LIME (Local Interpretable Model-agnostic Explanations)</strong> builds a local linear surrogate model around the individual prediction by perturbing feature values, providing intuitive human-readable threshold rules.
        </p>
      </div>

    </div>
  );
}

