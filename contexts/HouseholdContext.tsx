import { setClientHouseholdId } from "@/src/api/client";
import { getHouseholds } from "@/src/api/services/households";
import * as SecureStore from "expo-secure-store";
import React, { createContext, useContext, useEffect, useState } from "react";

type HouseholdContextType = {
  householdId: string | null;
  selectHousehold: (id: string) => Promise<void>;
  clearHousehold: () => Promise<void>;
  loading: boolean;
};
// TODO: This all might go away to make a more general context api
const HouseholdContext = createContext<HouseholdContextType>(
  {} as HouseholdContextType
);

const HOUSEHOLD_ID_KEY = "freshreceipt_household_id";

export function HouseholdProvider({ children }: { children: React.ReactNode }) {
  const [householdId, setHouseholdId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Sync householdId with API client whenever it changes
  useEffect(() => {
    setClientHouseholdId(householdId);
  }, [householdId]);

  useEffect(() => {
    loadHouseholdId();
  }, []);

  const loadHouseholdId = async () => {
    try {
      const id = await SecureStore.getItemAsync(HOUSEHOLD_ID_KEY);
      if (id) {
        setHouseholdId(id);
      } else {
        // If no ID in storage, fetch from API and select the first one
        try {
          const households = await getHouseholds();
          if (households.length > 0) {
            const firstHouseholdId = households[0].id;
            await selectHousehold(firstHouseholdId);
          }
        } catch (apiError) {
          console.warn(
            "Failed to fetch households for auto-selection",
            apiError
          );
        }
      }
    } catch (error) {
      console.warn("Failed to load household ID", error);
    } finally {
      setLoading(false);
    }
  };

  const selectHousehold = async (id: string) => {
    try {
      await SecureStore.setItemAsync(HOUSEHOLD_ID_KEY, id);
      setHouseholdId(id);
      setClientHouseholdId(id);
    } catch (error) {
      console.warn("Failed to save household ID", error);
      throw error;
    }
  };

  const clearHousehold = async () => {
    try {
      await SecureStore.deleteItemAsync(HOUSEHOLD_ID_KEY);
      setHouseholdId(null);
      setClientHouseholdId(null);
    } catch (error) {
      console.warn("Failed to clear household ID", error);
      throw error;
    }
  };

  return (
    <HouseholdContext.Provider
      value={{ householdId, selectHousehold, clearHousehold, loading }}
    >
      {children}
    </HouseholdContext.Provider>
  );
}

export const useHousehold = () => useContext(HouseholdContext);
