import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:5000";
const PAGE_SIZE = 600; // readings shown at once (10 minutes)

const SENSORS = {
  temperatureC: "Temperature (°C)",
  vibrationMmS: "Vibration (mm/s)",
  speedRpm: "Speed (rpm)",
};

export default function App() {
  const [summary, setSummary] = useState(null);
  const [readings, setReadings] = useState([]);
  const [sensor, setSensor] = useState("temperatureC");
  const [page, setPage] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/summary`)
      .then((res) => res.json())
      .then(setSummary)
      .catch(() => setError(`Can't reach the API at ${API}. Start it with "dotnet run" in api/PredictiveMaintenanceApi.`));
  }, []);

  useEffect(() => {
    fetch(`${API}/readings?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`)
      .then((res) => res.json())
      .then(setReadings)
      .catch(() => {});
  }, [page]);

  const data = readings.map((r) => ({
    time: r.timestamp.slice(11, 19),
    value: r[sensor],
    flagged: r.predictedAnomaly ? r[sensor] : null,
  }));

  const lastPage = summary ? Math.ceil(summary.total / PAGE_SIZE) - 1 : 0;
  const percent = (x) => Math.round(x * 100);

  return (
    <main>
      <h1>Packaging machine sensors</h1>

      {error && <p className="error">{error}</p>}

      {summary && (
        <p className="summary">
          The model flagged {summary.flagged} of {summary.total} readings. It
          found {percent(summary.recall)}% of the simulated faults, and{" "}
          {percent(summary.precision)}% of its alerts were real faults.
        </p>
      )}

      <div className="tabs">
        {Object.entries(SENSORS).map(([key, label]) => (
          <button
            key={key}
            className={key === sensor ? "active" : ""}
            onClick={() => setSensor(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="chart">
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={data}>
            <CartesianGrid stroke="#e3e6ea" vertical={false} />
            <XAxis dataKey="time" minTickGap={60} />
            <YAxis domain={["auto", "auto"]} width={50} />
            <Tooltip />
            <Line dataKey="value" stroke="#2f6fa3" dot={false} strokeWidth={1.5} isAnimationActive={false} name="Reading" />
            <Line dataKey="flagged" stroke="none" dot={{ r: 3, fill: "#d1432b", stroke: "none" }} isAnimationActive={false} name="Flagged" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="note">Red dots are readings the model flagged as abnormal.</p>

      <div className="pager">
        <button onClick={() => setPage(page - 1)} disabled={page === 0}>
          Earlier
        </button>
        <span>
          Readings {page * PAGE_SIZE + 1} to {page * PAGE_SIZE + readings.length}
        </span>
        <button onClick={() => setPage(page + 1)} disabled={page >= lastPage}>
          Later
        </button>
      </div>
    </main>
  );
}
