import { useCallback, useState } from "react";

export function useTranscript() {
  const [messages, setMessages] = useState([]);
  const clear = useCallback(() => setMessages([]), []);
  const addMessage = useCallback((role, text, interim = false) => {
    if (!text) return;
    setMessages((current) => {
      if (current.at(-1)?.interim && current.at(-1)?.role === role) {
        return [...current.slice(0, -1), { ...current.at(-1), text, interim }];
      }
      return [...current, { id: crypto.randomUUID(), role, text, interim, createdAt: new Date() }];
    });
  }, []);
  return { messages, addMessage, clear };
}
