import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { useAuth } from "@/contexts/AuthContext";
import { useThemeColor } from "@/hooks/use-theme-color";
import { StatusBar } from "expo-status-bar";
import { Button, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const backgroundColor = useThemeColor({}, "background");

  return (
    <SafeAreaView style={[styles.container, { backgroundColor }]}>
      <StatusBar style="auto" />
      <ThemedView style={styles.header}>
        <ThemedText type="title">Profile</ThemedText>
      </ThemedView>

      <View style={styles.content}>
        <View style={styles.infoContainer}>
          <ThemedText type="subtitle">User Information</ThemedText>
          <ThemedText style={styles.infoText}>
            Email: {user?.email || "user@example.com"}
          </ThemedText>
        </View>

        <View style={styles.buttonContainer}>
          <Button title="Sign Out" onPress={() => signOut()} color="#ff3b30" />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: "space-between",
  },
  infoContainer: {
    gap: 10,
  },
  infoText: {
    fontSize: 16,
  },
  buttonContainer: {
    marginBottom: 20,
  },
});
