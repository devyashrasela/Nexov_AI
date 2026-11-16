import { useCallback, useEffect, useRef, useState } from "react";

export function useVoiceCall({ onTranscript, onActivity, onDataChanged }) {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const clientRef = useRef(null);
  const audioElRef = useRef(null);

  const start = useCallback(async () => {
    setStatus("connecting");
    setError("");

    try {
      const { PipecatClient, RTVIEvent } = await import("@pipecat-ai/client-js");
      const { SmallWebRTCTransport } = await import("@pipecat-ai/small-webrtc-transport");

      // Setup audio element for playing bot voice
      let audio = audioElRef.current;
      if (!audio) {
        audio = document.createElement("audio");
        audio.id = "pipecat-bot-audio";
        audio.autoplay = true;
        audio.playsInline = true;
        document.body.appendChild(audio);
        audioElRef.current = audio;
      }

      const transport = new SmallWebRTCTransport({
        webrtcRequestParams: {
          endpoint: `${import.meta.env.VITE_API_URL || "http://localhost:7860"}/api/offer`,
        },
      });

      const client = new PipecatClient({
        transport,
        enableMic: true,
      });
      clientRef.current = client;
      const transcriptSources = { user: null, bot: null };
      const getEventData = (event) => event?.data ?? event;
      const getEventText = (event) => {
        const data = getEventData(event);
        return typeof data === "string" ? data : data?.text;
      };

      // Attach audio track when remote bot track starts
      const handleTrack = (track, participant) => {
        if (!participant?.local && track && track.kind === "audio") {
          audio.srcObject = new MediaStream([track]);
          audio.play().catch((playError) => {
            console.warn("Audio autoplay blocked or failed:", playError);
          });
        }
      };

      client.on("trackStarted", handleTrack);
      if (RTVIEvent?.TrackStarted) {
        client.on(RTVIEvent.TrackStarted, handleTrack);
      }

      const addUserTranscript = (event) => {
        if (transcriptSources.user === "legacy") return;
        transcriptSources.user = "current";
        const data = getEventData(event);
        const text = getEventText(event);
        if (text) onTranscript("caller", text, !data?.final);
      };
      const addLegacyUserTranscript = (event) => {
        if (transcriptSources.user === "current") return;
        transcriptSources.user = "legacy";
        const data = getEventData(event);
        const text = getEventText(event);
        if (text) onTranscript("caller", text, !data?.final);
      };
      const addBotTranscript = (event) => {
        if (transcriptSources.bot === "legacy") return;
        transcriptSources.bot = "current";
        const data = getEventData(event);
        const text = getEventText(event);
        if (text) onTranscript("agent", text, data?.spoken_status !== "completed");
      };
      const addLegacyBotTranscript = (event) => {
        if (transcriptSources.bot === "current") return;
        transcriptSources.bot = "legacy";
        const text = getEventText(event);
        if (text) onTranscript("agent", text, false);
      };

      // Current RTVI transcript events, with compatibility fallbacks for older servers.
      client.on(RTVIEvent?.UserInput || "userInput", addUserTranscript);
      client.on(RTVIEvent?.BotOutput || "botOutput", addBotTranscript);
      client.on(RTVIEvent?.UserTranscript || "userTranscript", (event) => {
        addLegacyUserTranscript(event);
      });
      client.on(RTVIEvent?.BotTranscript || "botTranscript", (event) => {
        addLegacyBotTranscript(event);
      });

      // Speaking indicators
      client.on("botStartedSpeaking", () => {
        setIsBotSpeaking(true);
        onActivity("speaking");
      });
      client.on("botStoppedSpeaking", () => {
        setIsBotSpeaking(false);
        onActivity("connected");
      });

      // Function calls & updates
      client.on("llmFunctionCall", onDataChanged);
      client.on("llmFunctionCallStopped", onDataChanged);

      client.on("disconnected", () => {
        setStatus("idle");
        setIsBotSpeaking(false);
        onActivity("idle");
      });

      client.on("error", (err) => {
        console.error("Voice client error:", err, JSON.stringify(err));
        const message =
          err?.message ||
          err?.error?.message ||
          err?.data?.message ||
          err?.data?.error ||
          (typeof err?.data === "string" ? err.data : "") ||
          "Voice connection error.";
        setError(message);
      });

      await client.connect();

      // Check if tracks already exist after connect
      const existingTracks = client.tracks?.();
      const botAudio = existingTracks?.bot?.audio;
      if (botAudio) {
        handleTrack(botAudio, { local: false });
      }

      setStatus("connected");
      onActivity("connected");
    } catch (connectionError) {
      console.error("Connection failed:", connectionError);
      setStatus("error");
      setError(connectionError.message || "Unable to connect to the voice assistant.");
    }
  }, [onActivity, onDataChanged, onTranscript]);

  const end = useCallback(async () => {
    setStatus("disconnecting");
    try {
      await clientRef.current?.disconnect();
    } catch (disconnectErr) {
      console.warn("Disconnect error:", disconnectErr);
    } finally {
      clientRef.current = null;
      if (audioElRef.current) {
        audioElRef.current.srcObject = null;
      }
      setIsBotSpeaking(false);
      setStatus("idle");
      onActivity("idle");
    }
  }, [onActivity]);

  useEffect(() => {
    return () => {
      clientRef.current?.disconnect();
      if (audioElRef.current) {
        audioElRef.current.srcObject = null;
        audioElRef.current.remove();
        audioElRef.current = null;
      }
    };
  }, []);

  return { status, error, isBotSpeaking, start, end };
}
