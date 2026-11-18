import { useState } from "react";

const API_URL = "http://127.0.0.1:8000/predict";

const fields = [
  { name: "air_temperature", label: "Air Temperature (K)", step: "0.1" },
  { name: "process_temperature", label: "Process Temperature (K)", step: "0.1" },
  { name: "rotational_speed", label: "Rotational Speed (rpm)", step: "1" },
  { name: "torque", label: "Torque (Nm)", step: "0.1" },
  { name: "tool_wear", label: "Tool Wear (min)", step: "1" },
];

export default function PredictionForm({ onPrediction }) {
  const [form, setForm] = useState({
    machine_type: "L",
    air_temperature: "298.1",
    process_temperature: "308.6",
    rotational_speed: "1551",
    torque: "42.8",
    tool_wear: "0",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const payload = {
      machine_type: form.machine_type,
      air_temperature: Number(form.air_temperature),
      process_temperature: Number(form.process_temperature),
      rotational_speed: Number(form.rotational_speed),
      torque: Number(form.torque),
      tool_wear: Number(form.tool_wear),
    };

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Server error ${response.status}: ${await response.text()}`);
      }
      const data = await response.json();
      setResult(data);
      onPrediction({ ...payload, ...data, time: new Date().toISOString() });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md bg-white rounded-xl shadow p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">
        Predictive Maintenance
      </h1>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm text-slate-600 mb-1">Machine Type</label>
          <select
            name="machine_type"
            value={form.machine_type}
            onChange={handleChange}
            className="w-full border rounded px-3 py-2"
          >
            <option value="L">L (Low)</option>
            <option value="M">M (Medium)</option>
            <option value="H">H (High)</option>
          </select>
        </div>

        {fields.map((f) => (
          <div key={f.name}>
            <label className="block text-sm text-slate-600 mb-1">{f.label}</label>
            <input
              type="number"
              name={f.name}
              value={form[f.name]}
              onChange={handleChange}
              step={f.step}
              required
              className="w-full border rounded px-3 py-2"
            />
          </div>
        ))}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Predicting..." : "Predict"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600 break-words">{error}</p>}

      {result && (
        <div
          className={`mt-4 rounded-lg border p-4 ${
            result.prediction === 1
              ? "bg-red-50 border-red-300 text-red-800"
              : "bg-green-50 border-green-300 text-green-800"
          }`}
        >
          <p className="text-lg font-bold">
            {result.prediction === 1 ? "⚠️ " : "✅ "}
            {result.result}
          </p>
          <p className="text-sm mt-2">
            Failure probability:{" "}
            <span className="font-semibold">
                 {Number(result.failure_probability).toFixed(1)}%
            </span>
          </p>
          <p className="text-xs mt-1 opacity-70">
            Machine type: {result.machine_type} | Model: {result.model_name}
          </p>
        </div>
      )}
    </div>
  );
}