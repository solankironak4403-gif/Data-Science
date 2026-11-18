import { useState, useEffect } from "react";
import axios from "axios";
import { Activity, Search, RefreshCw, Filter, ArrowUpDown } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function TrafficMonitoring() {
  const [flows, setFlows] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [protocolFilter, setProtocolFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchFlows = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/flows/explainable`);
      setFlows(res.data.flows || []);
      setError("");
    } catch (err) {
      console.error("Traffic load error:", err);
      setError("Unable to load network traffic flows.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlows();
  }, []);

  const filteredFlows = flows.filter((f) => {
    const matchesSearch =
      f.src_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.dst_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(f.dst_port).includes(searchTerm);
    const matchesProtocol =
      protocolFilter === "ALL" || f.protocol.toUpperCase() === protocolFilter;
    return matchesSearch && matchesProtocol;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "22px", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: "10px" }}>
            <Activity color="#3b82f6" size={24} />
            Network Traffic Monitoring
          </h2>
          <p style={{ color: "#64748b", marginTop: "4px", fontSize: "13px" }}>
            Real-time inspection of captured bidirectional network flows.
          </p>
        </div>

        <button
          onClick={fetchFlows}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "8px 14px",
            borderRadius: "6px",
            border: "1px solid #cbd5e1",
            background: "white",
            color: "#475569",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "13px"
          }}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: "flex", gap: "14px", background: "white", padding: "14px 18px", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "8px", background: "#f8fafc", padding: "8px 12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
          <Search size={16} color="#94a3b8" />
          <input
            type="text"
            placeholder="Search by IP address or destination port..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ border: "none", outline: "none", background: "transparent", width: "100%", fontSize: "13px" }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Filter size={16} color="#64748b" />
          <select
            value={protocolFilter}
            onChange={(e) => setProtocolFilter(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", background: "white", fontSize: "13px" }}
          >
            <option value="ALL">All Protocols</option>
            <option value="TCP">TCP Only</option>
            <option value="UDP">UDP Only</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: "10px 14px", borderRadius: "6px" }}>
          {error}
        </div>
      )}

      {/* Traffic Flows Table */}
      <div style={{ background: "white", borderRadius: "10px", padding: "18px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", fontSize: "13px", color: "#64748b" }}>
          <span>Showing <strong>{filteredFlows.length}</strong> of <strong>{flows.length}</strong> total flows</span>
          <span>Protocol Filter: <strong>{protocolFilter}</strong></span>
        </div>

        {loading ? (
          <p style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>Loading network flows...</p>
        ) : filteredFlows.length === 0 ? (
          <p style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>No matching network flows found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Flow ID</th>
                  <th>Source IP</th>
                  <th>Destination IP</th>
                  <th>Port</th>
                  <th>Protocol</th>
                  <th>Classification</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredFlows.map((f) => (
                  <tr key={f.flow_id}>
                    <td style={{ fontWeight: 600 }}>#{f.flow_id}</td>
                    <td title={f.src_ip}>{f.src_ip}</td>
                    <td title={f.dst_ip}>{f.dst_ip}</td>
                    <td>{f.dst_port}</td>
                    <td><span style={{ padding: "2px 8px", background: "#f1f5f9", borderRadius: "4px", fontSize: "12px", fontWeight: 600 }}>{f.protocol}</span></td>
                    <td>
                      <span className={f.label === "ATTACK" ? "attack-label" : "benign-label"}>
                        {f.label}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{(f.confidence * 100).toFixed(1)}%</td>
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

