import { useEffect, useRef } from "react";

export default function Transcript({ messages }) {
  const listRef = useRef(null);
  useEffect(() => {
    const element = listRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages]);
  return <section className="card transcript-card">
    <div className="card-header">Live transcript</div>
    <div className="transcript-list" ref={listRef} aria-live="polite">
      {!messages.length && <div className="empty-state">Start a call to see the conversation here.</div>}
      {messages.map((message) => <div key={message.id} className={`message-row ${message.role === "caller" ? "caller" : "agent"}`}>
        <div className={`message-bubble ${message.interim ? "interim" : ""}`}>
          <div>{message.text}</div><small>{message.role === "caller" ? "You" : "Aria"} · {message.createdAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>
        </div>
      </div>)}
    </div>
  </section>;
}
