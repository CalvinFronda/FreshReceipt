// constants/supabase.ts
import type { Database } from "@/database.types";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { createClient } from "@supabase/supabase-js";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!;

// Expo SecureStore adapter for Supabase
const ExpoSecureStoreAdapter = {
  getItem: (key: string) => {
    if (Platform.OS === "web") {
      return AsyncStorage.getItem(key);
    }else{
        return SecureStore.getItemAsync(key).catch((error) => {
      console.warn("SecureStore.getItemAsync failed", error);
      return null;
    });
    }
    
  },
  setItem: (key: string, value: string) => {
    if (Platform.OS === "web") {
      AsyncStorage.setItem(key, value);
    }else{
    SecureStore.setItemAsync(key, value).catch((error) => {
      console.warn("SecureStore.setItemAsync failed", error);
    });
    }
  },
  removeItem: (key: string) => {
    if (Platform.OS === "web") {
      AsyncStorage.removeItem(key);
    }else{
    SecureStore.deleteItemAsync(key).catch((error) => {
      console.warn("SecureStore.deleteItemAsync failed", error);
    });
    }
  },
};

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: ExpoSecureStoreAdapter,
    autoRefreshToken: true,
    persistSession: Platform.OS !== "web",
    detectSessionInUrl: false,
  },
});

// Database types (we'll generate these later)
export type Tables<T extends keyof Database["public"]["Tables"]> =
  Database["public"]["Tables"][T]["Row"];
