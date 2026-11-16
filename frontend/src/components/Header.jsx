import { AudioLines } from "lucide-react";
import StatusBadge from "./StatusBadge";

export default function Header({ status }) {
  return <header className="header">
    <div className="brand"><AudioLines className="brand-icon" size={30} /><span>City Care Clinic</span><span className="brand-subtitle">Voice Appointment Assistant</span></div>
    <StatusBadge status={status} />
  </header>;
}
