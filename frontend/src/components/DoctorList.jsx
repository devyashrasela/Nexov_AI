import { useState } from "react";

function SlotChip({ slot }) {
  return <span className={`slot-chip ${slot.is_booked ? "booked" : ""}`}>{slot.time}</span>;
}

export default function DoctorList({ doctors, loading, error, onRetry }) {
  const [freeOnly, setFreeOnly] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  return <section className="card doctors-card">
    <div className="card-header">
      <span>Doctors & slots</span>
      <div className="card-actions">
        {!collapsed && <label className="toggle"><input type="checkbox" checked={freeOnly} onChange={(event) => setFreeOnly(event.target.checked)} /> Show free only</label>}
        <button className="collapse-button" type="button" onClick={() => setCollapsed((value) => !value)} aria-expanded={!collapsed}>
          {collapsed ? "Expand" : "Collapse"}
        </button>
      </div>
    </div>
    {!collapsed && <div className="doctor-list">
      {loading && <div className="empty-state">Loading doctors…</div>}
      {error && <div className="empty-state">{error.message}<button className="text-button" onClick={onRetry}>Retry</button></div>}
      {!loading && !error && doctors?.map((doctor) => {
        const slots = freeOnly ? doctor.slots.filter((slot) => !slot.is_booked) : doctor.slots;
        return <article className="doctor-card" key={doctor.id}><h3>{doctor.name}</h3><p>{doctor.speciality}</p><div className="slots">{slots.length ? slots.map((slot) => <SlotChip key={slot.id} slot={slot} />) : <span className="muted">No matching slots</span>}</div></article>;
      })}
    </div>}
  </section>;
}
