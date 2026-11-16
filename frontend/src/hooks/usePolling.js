import { useCallback, useEffect, useRef, useState } from "react";

export function usePolling(fetcher, intervalMs, pollIntervalEnabled = false) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Keep fetcher in a ref so the callback identity never changes
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    try {
      const next = await fetcherRef.current();
      setData(next);
      setError(null);
    } catch (requestError) {
      setError(requestError);
    }
  }, []);

  // Fetch initial data once on mount
  useEffect(() => {
    refetch();
  }, [refetch]);

  // Periodic polling only when active (e.g. during an ongoing voice call)
  useEffect(() => {
    if (!pollIntervalEnabled) return undefined;
    const timer = window.setInterval(refetch, intervalMs);
    return () => window.clearInterval(timer);
  }, [pollIntervalEnabled, intervalMs, refetch]);

  return { data, error, refetch };
}
