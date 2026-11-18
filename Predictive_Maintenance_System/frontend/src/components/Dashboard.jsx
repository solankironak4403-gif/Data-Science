import { useState, useEffect } from "react";

const API_URL = "http://127.0.0.1:8000/predict";

const SLIDERS = [
  { key: "air_temperature", label: "Air temperature", icon: "🌡️", unit: "K", min: 295, max: 305, step: 0.1, caution: 302, high: 304, hint: "Air around the machine" },
  { key: "process_temperature", label: "Process temperature", icon: "🔥", unit: "K", min: 305, max: 314, step: 0.1, caution: 311, high: 313, hint: "Heat inside the process" },
  { key: "rotational_speed", label: "Rotational speed", icon: "⚙️", unit: "rpm", min: 1100, max: 2900, step: 10, caution: 2200, high: 2600, hint: "How fast the tool spins" },
  { key: "torque", label: "Torque", icon: "🔩", unit: "Nm", min: 3, max: 80, step: 0.1, caution: 55, high: 65, hint: "Turning force on the tool" },
  { key: "tool_wear", label: "Tool wear", icon: "🛠️", unit: "min", min: 0, max: 250, step: 1, caution: 150, high: 200, hint: "How long the tool was used" },
];

const COLORS = { ok: "#16a34a", caution: "#f59e0b", high: "#dc2626" };

// Presets change only the sliders. The machine type stays as the user selected it.
const PRESETS = {
  normal: { air_temperature: 298.1, process_temperature: 308.6, rotational_speed: 1550, torque: 42.8, tool_wear: 0 },
  risky: { air_temperature: 298, process_temperature: 309, rotational_speed: 1300, torque: 65, tool_wear: 220 },
};

// Overstrain limit (torque x tool wear) depends on the machine type
const STRAIN_LIMIT = { L: 11000, M: 12000, H: 13000 };

const TYPE_TIPS = {
  L: "Type L (low quality) handles the least strain. Keep loads gentle and inspect it more often.",
  M: "Type M (medium quality) handles medium strain. Avoid long heavy runs and follow the normal inspection plan.",
  H: "Type H (high quality) handles the most strain, so a failure here points to a real overload. Check the tool and the cooling system carefully.",
};

const fmt = (n) => Math.round(n).toLocaleString();

function statusOf(s, v) {
  if (v >= s.high) return "high";
  if (v >= s.caution) return "caution";
  return "ok";
}

// failure_probability from the backend is a percentage (23 means 23%)
function riskOf(prob) {
  if (prob >= 50)
    return { label: "Critical", color: "#dc2626", soft: "#fef2f2", message: "High failure risk. Stop and inspect the machine now." };
  if (prob >= 30)
    return { label: "Caution", color: "#f59e0b", soft: "#fffbeb", message: "Some risk. Plan an inspection soon." };
  return { label: "Healthy", color: "#16a34a", soft: "#f0fdf4", message: "The machine looks healthy. Keep the normal schedule." };
}

// Simple rule check based on the AI4I 2020 dataset description
function analyse(v) {
  const diff = v.process_temperature - v.air_temperature;
  const power = (v.torque * v.rotational_speed * 2 * Math.PI) / 60;
  const strain = v.torque * v.tool_wear;
  const limit = STRAIN_LIMIT[v.machine_type] ?? 11000;
  return {
    diff,
    power,
    strain,
    limit,
    osf: strain > limit,
    hdf: diff < 8.6 && v.rotational_speed < 1380,
    pwf: power < 3500 || power > 9000,
    twf: v.tool_wear >= 200,
  };
}

function buildAdvice(v, a) {
  const t = v.machine_type;
  const list = [];

  if (a.osf) {
    const steps = [];
    if (v.tool_wear > 0) {
      steps.push(`Lower the torque. With ${v.tool_wear} min of tool wear, keep torque under ${Math.floor(a.limit / v.tool_wear)} Nm.`);
    }
    steps.push("Replace or sharpen the tool. A fresh tool can carry a much higher torque safely.");
    steps.push("Reduce the cutting load (smaller depth of cut or slower feed).");
    list.push({
      id: "osf",
      icon: "🏋️",
      title: "Overstrain failure",
      why: `Torque × tool wear is ${fmt(a.strain)} minNm. The limit for Type ${t} is ${fmt(a.limit)} minNm.`,
      steps,
    });
  }

  if (a.hdf) {
    list.push({
      id: "hdf",
      icon: "🌡️",
      title: "Heat dissipation failure",
      why: `The gap between process and air temperature is only ${a.diff.toFixed(1)} K (it should be above 8.6 K) and the speed is low (${v.rotational_speed} rpm).`,
      steps: [
        "Check coolant level and flow. Clean filters, vents and fans.",
        "Raise the rotational speed above 1,380 rpm if the job allows it.",
        "Improve room ventilation or let the machine cool before the next run.",
      ],
    });
  }

  if (a.pwf) {
    const high = a.power > 9000;
    list.push({
      id: "pwf",
      icon: "⚡",
      title: "Power failure",
      why: `Power is about ${fmt(a.power)} W. The safe range is 3,500 to 9,000 W.`,
      steps: high
        ? [
            "Reduce the torque or the speed so the power drops below 9,000 W.",
            "Check the motor and electrical supply for overheating.",
            "Run the machine at a lower load until it is inspected.",
          ]
        : [
            "The machine is under-loaded or slipping. Check belts, couplings and the drive.",
            "Increase the load or speed carefully to get back above 3,500 W.",
            "Inspect the motor for faults.",
          ],
    });
  }

  if (a.twf) {
    list.push({
      id: "twf",
      icon: "🛠️",
      title: "Tool wear failure",
      why: `Tool wear is ${v.tool_wear} min. Failures become likely between 200 and 240 min.`,
      steps: [
        "Replace the tool now.",
        "Plan tool changes before 200 min of use.",
        "Record the tool life so the next change is not missed.",
      ],
    });
  }

  if (list.length === 0) {
    list.push({
      id: "other",
      icon: "🔍",
      title: "Risky combination of values",
      why: "The model found a risky pattern, but none of the standard rules matched. Some failures in this dataset are random.",
      steps: [
        "Inspect the machine and the tool.",
        "Compare the current values with a normal run using the Normal machine button.",
        "Log the result and watch the next few predictions.",
      ],
    });
  }

  return list;
}

function Card({ title, children, className = "", style }) {
  return (
    <div className={`rounded-2xl bg-white shadow-sm border border-slate-200 p-5 ${className}`} style={style}>
      {title && <h2 className="text-base font-semibold text-slate-800 mb-4">{title}</h2>}
      {children}
    </div>
  );
}

function HealthRing({ value, color }) {
  const r = 70;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative w-44 h-44 shrink-0">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90">
        <circle cx="80" cy="80" r={r} fill="none" stroke="#e5e7eb" strokeWidth="14" />
        <circle
          cx="80"
          cy="80"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${(c * value) / 100} ${c}`}
          style={{ transition: "stroke-dasharray 0.6s", filter: `drop-shadow(0 0 6px ${color}66)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-extrabold text-slate-800">{value.toFixed(0)}%</span>
        <span className="text-xs text-slate-500">Machine health</span>
      </div>
    </div>
  );
}

function SliderField({ s, value, onChange }) {
  const st = statusOf(s, value);
  const color = COLORS[st];
  const pct = ((value - s.min) / (s.max - s.min)) * 100;
  const cPct = ((s.caution - s.min) / (s.max - s.min)) * 100;
  const hPct = ((s.high - s.min) / (s.max - s.min)) * 100;
  const zones = `linear-gradient(to right, ${COLORS.ok} 0%, ${COLORS.ok} ${cPct}%, ${COLORS.caution} ${cPct}%, ${COLORS.caution} ${hPct}%, ${COLORS.high} ${hPct}%, ${COLORS.high} 100%)`;

  return (
    <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-700">
          <span className="mr-1">{s.icon}</span>
          {s.label}
        </label>
        <span
          className="text-sm font-bold px-3 py-0.5 rounded-full"
          style={{ backgroundColor: color + "22", color }}
        >
          {value.toFixed(s.step < 1 ? 1 : 0)} {s.unit}
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-2">{s.hint}</p>
      <input
        type="range"
        className="pm-slider"
        min={s.min}
        max={s.max}
        step={s.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ "--c": color, "--fill": `${pct}%` }}
      />
      <div className="h-1.5 rounded-full opacity-60 mt-1" style={{ background: zones }} />
      <div className="flex justify-between text-[11px] text-slate-400 mt-1">
        <span>{s.min}</span>
        <span>{s.max}</span>
      </div>
    </div>
  );
}

export default function Dashboard({ history, onAdd, onClear, dbStatus }) {
  const [form, setForm] = useState({ machine_type: "L", ...PRESETS.normal });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);

  async function predict(values, save) {
    setLoading(true);
    setError("");
    const payload = {
      machine_type: values.machine_type,
      air_temperature: Number(values.air_temperature),
      process_temperature: Number(values.process_temperature),
      rotational_speed: Math.round(Number(values.rotational_speed)),
      torque: Number(values.torque),
      tool_wear: Math.round(Number(values.tool_wear)),
    };
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.status === 422) {
        throw new Error("Invalid input. Please check the slider values.");
      }
      if (!response.ok) {
        throw new Error(`Server error ${response.status}`);
      }
      const data = await response.json();
      // keep the inputs with the result so the advice matches this prediction
      setResult({ ...data, input: payload });
      if (save) onAdd({ ...payload, ...data, time: new Date().toISOString() });
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot reach the backend. Is it running at http://127.0.0.1:8000 ?"
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  // Live mode: predict when the sliders stop moving (not saved to history)
  useEffect(() => {
    if (!live) return;
    const timer = setTimeout(() => predict(form, false), 500);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, live]);

  const prob = result ? Number(result.failure_probability) : 0;
  const health = Math.max(0, Math.min(100, 100 - prob));
  const risk = riskOf(prob);

  const analysis = result ? analyse(result.input) : null;
  const advice = result && result.prediction === 1 ? buildAdvice(result.input, analysis) : [];

  const total = history.length;
  const alerts = history.filter((h) => h.prediction === 1).length;
  const avgRisk = total
    ? history.reduce((sum, h) => sum + Number(h.failure_probability || 0), 0) / total
    : 0;
  const chartItems = history.slice(0, 20).reverse();

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-800 text-white p-6 mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/10" />
        <div className="absolute right-24 -bottom-12 w-32 h-32 rounded-full bg-white/5" />
        <div className="relative">
          <h1 className="text-2xl font-extrabold">🛠️ Predictive Maintenance Dashboard</h1>
          <p className="text-sm text-blue-200 mt-1">
            Move the sliders, click Predict, and see if the machine may fail.
          </p>
        </div>
        <div className="relative flex items-center gap-2">
          {dbStatus && (
            <div
              className="text-xs bg-white/20 rounded-full px-3 py-1.5 flex items-center gap-1.5"
              title={dbStatus.message || `Connected to ${dbStatus.database}`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  dbStatus.type?.includes("MySQL") ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              <span className="font-medium">DB: {dbStatus.type}</span>
            </div>
          )}
          <div className="text-xs bg-white/15 rounded-full px-3 py-1.5">
            Model: {result ? result.model_name : "Random Forest"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* LEFT: inputs */}
        <Card title="1. Machine settings" className="lg:col-span-2">
          <p className="text-sm font-medium text-slate-700 mb-2">Machine type</p>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              ["L", "Low"],
              ["M", "Medium"],
              ["H", "High"],
            ].map(([code, name]) => (
              <button
                key={code}
                onClick={() => setForm({ ...form, machine_type: code })}
                className={`py-2 rounded-lg text-sm font-medium border transition ${
                  form.machine_type === code
                    ? "bg-blue-600 text-white border-blue-600 shadow"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
                }`}
              >
                {code} ({name})
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2 mb-5">
            <button
              onClick={() => setForm({ ...form, ...PRESETS.normal })}
              className="py-2 rounded-lg text-sm bg-green-50 text-green-700 border border-green-200 hover:bg-green-100"
            >
              ✅ Normal machine
            </button>
            <button
              onClick={() => setForm({ ...form, ...PRESETS.risky })}
              className="py-2 rounded-lg text-sm bg-red-50 text-red-700 border border-red-200 hover:bg-red-100"
            >
              ⚠️ Risky machine
            </button>
          </div>

          <div className="space-y-3">
            {SLIDERS.map((s) => (
              <SliderField
                key={s.key}
                s={s}
                value={Number(form[s.key])}
                onChange={(val) => setForm({ ...form, [s.key]: val })}
              />
            ))}
          </div>

          <button
            onClick={() => predict(form, true)}
            disabled={loading}
            className="w-full mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold shadow hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Predicting..." : "🔮 Predict failure"}
          </button>

          <label className="flex items-center gap-2 mt-3 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={live}
              onChange={(e) => setLive(e.target.checked)}
              className="accent-blue-600"
            />
            Live mode: update the result while I move the sliders
          </label>

          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </Card>

        {/* RIGHT: results */}
        <div className="lg:col-span-3 space-y-5">
          <Card
            title="2. Prediction result"
            style={result ? { backgroundColor: risk.soft, borderColor: risk.color + "55" } : undefined}
          >
            {!result ? (
              <div className="py-10 text-center text-slate-500">
                No result yet. Click <b>Predict failure</b> on the left.
              </div>
            ) : (
              <>
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <HealthRing value={health} color={risk.color} />
                  <div className="text-center sm:text-left">
                    <span
                      className="inline-block px-3 py-1 rounded-full text-sm font-bold text-white"
                      style={{ backgroundColor: risk.color }}
                    >
                      {risk.label}
                    </span>
                    <p className="text-2xl font-extrabold text-slate-800 mt-2">{result.result}</p>
                    <p className="text-sm text-slate-600 mt-1">{risk.message}</p>
                    <p className="text-sm text-slate-500 mt-3">
                      Failure probability: <b style={{ color: risk.color }}>{prob.toFixed(1)}%</b>
                      <span className="mx-2">|</span>
                      Machine type: <b>{result.input.machine_type}</b>
                    </p>
                  </div>
                </div>

                {/* Rule checks */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-5">
                  {[
                    { name: "Overstrain", bad: analysis.osf, detail: `${fmt(analysis.strain)} / ${fmt(analysis.limit)}` },
                    { name: "Heat", bad: analysis.hdf, detail: `${analysis.diff.toFixed(1)} K gap` },
                    { name: "Power", bad: analysis.pwf, detail: `${fmt(analysis.power)} W` },
                    { name: "Tool wear", bad: analysis.twf, detail: `${result.input.tool_wear} min` },
                  ].map((c) => (
                    <div
                      key={c.name}
                      className="rounded-lg bg-white/80 border p-2 text-center"
                      style={{ borderColor: c.bad ? "#fca5a5" : "#bbf7d0" }}
                    >
                      <p className="text-xs text-slate-500">{c.name}</p>
                      <p className={`text-sm font-bold ${c.bad ? "text-red-600" : "text-green-600"}`}>
                        {c.bad ? "⚠ Warning" : "✓ OK"}
                      </p>
                      <p className="text-[11px] text-slate-400">{c.detail}</p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </Card>

          {/* Recommended solution (only when a failure is predicted) */}
          {result && result.prediction === 1 && (
            <Card title="🧰 Recommended solution">
              <p className="text-sm text-slate-600 mb-4">
                The likely cause is estimated from standard rules for the AI4I dataset. Your model
                only says that a failure is likely.
              </p>
              <div className="space-y-4">
                {advice.map((item) => (
                  <div key={item.id} className="rounded-xl border border-red-200 bg-red-50/60 p-4">
                    <p className="font-bold text-red-700">
                      {item.icon} {item.title}
                    </p>
                    <p className="text-sm text-slate-700 mt-1">
                      <b>Why:</b> {item.why}
                    </p>
                    <p className="text-sm font-semibold text-slate-800 mt-3">What to do:</p>
                    <ol className="list-decimal list-inside text-sm text-slate-700 space-y-1 mt-1">
                      {item.steps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-xl bg-blue-50 border border-blue-200 p-3 text-sm text-blue-900">
                <b>Type {result.input.machine_type} tip:</b> {TYPE_TIPS[result.input.machine_type]}
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Safe order: stop the machine, inspect it, fix the cause, then run a test prediction again.
              </p>
            </Card>
          )}

          <div className="grid grid-cols-3 gap-4">
            <Card>
              <p className="text-sm text-slate-500">Total predictions</p>
              <p className="text-3xl font-extrabold text-slate-800 mt-1">{total}</p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Active alerts</p>
              <p className={`text-3xl font-extrabold mt-1 ${alerts > 0 ? "text-red-600" : "text-slate-800"}`}>
                {alerts}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Average risk</p>
              <p className="text-3xl font-extrabold text-slate-800 mt-1">{avgRisk.toFixed(1)}%</p>
            </Card>
          </div>

          <Card title="3. Failure probability (last 20 predictions)">
            {chartItems.length === 0 ? (
              <p className="text-sm text-slate-500">The chart appears after you click Predict failure.</p>
            ) : (
              <>
                <div className="flex items-end justify-center gap-2 h-40 border-b border-slate-200">
                  {chartItems.map((h, i) => {
                    const p = Math.max(0, Math.min(100, Number(h.failure_probability)));
                    return (
                      <div
                        key={i}
                        title={`${p.toFixed(1)}%`}
                        className="flex-1 max-w-[44px] rounded-t-lg"
                        style={{ height: `${Math.max(p, 3)}%`, backgroundColor: riskOf(p).color }}
                      />
                    );
                  })}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Green = healthy, yellow = caution, red = critical. Hover a bar to see the number.
                </p>
              </>
            )}
          </Card>

          <Card title="4. Recent predictions">
            {history.length === 0 ? (
              <p className="text-sm text-slate-500">Nothing saved yet.</p>
            ) : (
              <div className="space-y-3">
                {history.slice(0, 6).map((h, i) => {
                  const p = Number(h.failure_probability);
                  const r = riskOf(p);
                  return (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 font-semibold flex items-center justify-center">
                          {h.machine_type}
                        </span>
                        <span className="text-slate-700">
                          Torque {h.torque} Nm, wear {h.tool_wear} min
                          <span className="block text-xs text-slate-400">
                            {new Date(h.time).toLocaleString()}
                          </span>
                        </span>
                      </div>
                      <span className="font-semibold" style={{ color: r.color }}>
                        {r.label} ({p.toFixed(1)}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
            {history.length > 0 && (
              <button
                onClick={onClear}
                className="mt-4 text-xs text-slate-500 underline hover:text-red-600"
              >
                Clear history
              </button>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}