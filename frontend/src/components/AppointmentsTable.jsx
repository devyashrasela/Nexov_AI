import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

function maskPhone(phone) {
  return phone ? `${phone.slice(0, 2)}•••••${phone.slice(-3)}` : "—";
}

export default function AppointmentsTable({ appointments, loading, error, onRetry }) {
  const [filter, setFilter] = useState("");
  const [showPhone, setShowPhone] = useState(false);
  const visible = (appointments || []).filter((item) => !filter || item.status === filter);
  return <section className="card appointments-card">
    <div className="card-header"><span>Appointments</span><div className="filter-tabs">{["", "booked", "cancelled"].map((item) => <button className={filter === item ? "active" : ""} key={item} onClick={() => setFilter(item)}>{item || "All"}</button>)}</div></div>
    {loading && <div className="empty-state">Loading appointments…</div>}
    {error && <div className="empty-state">{error.message}<button className="text-button" onClick={onRetry}>Retry</button></div>}
    {!loading && !error && <div className="table-wrap"><table><thead><tr><th>ID</th><th>Phone <button className="icon-button" aria-label="Toggle phone visibility" onClick={() => setShowPhone(!showPhone)}>{showPhone ? <EyeOff size={14} /> : <Eye size={14} />}</button></th><th>Doctor</th><th>Date & time</th><th>Status</th></tr></thead><tbody>
      {visible.map((item) => <tr key={item.id}><td>#{item.id}</td><td>{showPhone ? item.phone_number : maskPhone(item.phone_number)}</td><td><strong>{item.doctor.name}</strong><span className="table-muted">{item.doctor.speciality}</span></td><td>{item.date}<span className="table-muted">{item.time}</span></td><td><span className={`status-pill ${item.status}`}>{item.status}</span></td></tr>)}
    </tbody></table>{!visible.length && <div className="empty-state">No appointments yet.</div>}</div>}
  </section>;
}
