const API_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

async function request(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json();
}

export const getDoctors = (freeOnly = false) =>
  request(`/api/doctors${freeOnly ? "?free_only=true" : ""}`);

export const getAppointments = (status = "") =>
  request(`/api/appointments${status ? `?status=${status}` : ""}`);

export { API_URL };
