import axios from "axios";

// In the future, we can use a proper environment variable or configuration service
// For now, we'll default to localhost for development
const DEV_API_URL = "http://localhost:8000";
const PROD_API_URL = "https://api.freshreceipt.com"; // Placeholder

const baseURL = __DEV__ ? DEV_API_URL : PROD_API_URL;

const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

let currentHouseholdId: string | null = null;

export const setClientHouseholdId = (id: string | null) => {
  currentHouseholdId = id;
};

apiClient.interceptors.request.use(async (config) => {
  // Add Authorization header from Supabase session
  try {
    const { supabase } = await import("@/constants/supabase");
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.access_token) {
      config.headers["Authorization"] = `Bearer ${session.access_token}`;
    }
  } catch (error) {
    console.warn("Failed to get auth token", error);
  }

  // Add household ID header
  //   if (currentHouseholdId) {
  //     config.headers["X-Household-ID"] = currentHouseholdId;
  //   }
  // TODO: We need to select a household before setting it in context
  config.headers["X-Household-ID"] = "1d1b7a85-7542-4291-83f7-cc962462f519";
  return config;
});

export default apiClient;
