import { Mic, PhoneOff } from "lucide-react";

export default function CallPanel({ status, error, isBotSpeaking, onStart, onEnd }) {
  const active = status === "connected";
  const busy = status === "connecting" || status === "disconnecting";
  return <section className="card call-panel">
    <div className="panel-title">Voice call</div>
    <button className={`call-button ${active ? "end" : ""}`} disabled={busy} onClick={active ? onEnd : onStart}>
      {active ? <><PhoneOff size={18} /> End Call</> : <><Mic size={18} /> {busy ? "Connecting…" : "Start Call"}</>}
    </button>
    <p className="call-meta">{active ? "Mic enabled • Connected to WebRTC" : "Click to start the AI Voice Assistant"}</p>
    {active && <div className="agent-indicator"><span className="audio-orb" /><span>Agent {isBotSpeaking ? "Speaking…" : "Listening…"}</span></div>}
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>;
}
