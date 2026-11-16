export default function StatusBadge({ status }) {
  const labels = { idle: "Ready", connecting: "Connecting", connected: "Connected", error: "Connection error" };
  return <div className={`status-badge ${status === "connected" ? "connected" : ""}`}><span className="status-dot" />{labels[status] || status}</div>;
}
