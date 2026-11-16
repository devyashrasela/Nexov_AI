import { useCallback, useRef, useState } from "react";
import Header from "./components/Header";
import CallPanel from "./components/CallPanel";
import Transcript from "./components/Transcript";
import DoctorList from "./components/DoctorList";
import AppointmentsTable from "./components/AppointmentsTable";
import { getAppointments, getDoctors } from "./api";
import { usePolling } from "./hooks/usePolling";
import { useTranscript } from "./hooks/useTranscript";
import { useVoiceCall } from "./hooks/useVoiceCall";

export default function App() {
  const transcript = useTranscript();
  const doctorsFetcher = useCallback(() => getDoctors(false), []);
  const appointmentsFetcher = useCallback(() => getAppointments(), []);

  // Track call status for enabling/disabling 3s polling fallback
  const [isCallActive, setIsCallActive] = useState(false);

  const doctorPolling = usePolling(doctorsFetcher, 3000, isCallActive);
  const appointmentPolling = usePolling(appointmentsFetcher, 3000, isCallActive);

  // Keep refetch callbacks stable
  const doctorRefetch = useRef(doctorPolling.refetch);
  doctorRefetch.current = doctorPolling.refetch;
  const appointmentRefetch = useRef(appointmentPolling.refetch);
  appointmentRefetch.current = appointmentPolling.refetch;

  const refreshData = useCallback(() => {
    doctorRefetch.current();
    appointmentRefetch.current();
  }, []);

  const handleActivity = useCallback((activity) => {
    if (activity === "connected") setIsCallActive(true);
    if (activity === "idle") {
      setIsCallActive(false);
      transcript.clear();
    }
  }, [transcript.clear]);
  const handleDataChanged = useCallback(() => refreshData(), [refreshData]);

  const voice = useVoiceCall({
    onTranscript: transcript.addMessage,
    onActivity: handleActivity,
    onDataChanged: handleDataChanged,
  });

  const status = voice.status;

  const start = useCallback(async () => {
    transcript.clear();
    await voice.start();
  }, [transcript, voice]);

  const end = useCallback(async () => {
    await voice.end();
    transcript.clear();
  }, [transcript.clear, voice]);

  return (
    <main className="viewport">
      <Header status={status} />
      <div className="dashboard-grid">
        <div className="left-col">
          <CallPanel
            status={status}
            error={voice.error}
            isBotSpeaking={voice.isBotSpeaking}
            onStart={start}
            onEnd={end}
          />
          <Transcript messages={transcript.messages} />
        </div>
        <div className="right-col">
          <DoctorList
            doctors={doctorPolling.data || []}
            loading={!doctorPolling.data && !doctorPolling.error}
            error={doctorPolling.error}
            onRetry={doctorPolling.refetch}
          />
          <AppointmentsTable
            appointments={appointmentPolling.data || []}
            loading={!appointmentPolling.data && !appointmentPolling.error}
            error={appointmentPolling.error}
            onRetry={appointmentPolling.refetch}
          />
        </div>
      </div>
    </main>
  );
}
