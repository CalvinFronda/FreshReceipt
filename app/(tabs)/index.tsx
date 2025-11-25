import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { useThemeColor } from "@/hooks/use-theme-color";
import { StatusBar } from "expo-status-bar";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useFoodItems } from "@/src/api/hooks/useFoodItems";
import { FoodItem } from "@/src/api/types";
import { ActivityIndicator } from "react-native";

export default function InventoryScreen() {
  const backgroundColor = useThemeColor({}, "background");
  const { data: inventory, isLoading, error, refetch } = useFoodItems();

  const renderItem = ({ item }: { item: FoodItem }) => (
    <View style={styles.itemContainer}>
      <View style={styles.itemInfo}>
        <ThemedText type="defaultSemiBold" style={styles.itemName}>
          {item.name}
        </ThemedText>
        <ThemedText style={styles.itemDetails}>
          {item.quantity} {item.unit ? item.unit : ""} • Purchased:{" "}
          {new Date(item.purchase_date).toLocaleDateString()}
        </ThemedText>
      </View>
      <View style={styles.itemPrice}>
        <ThemedText type="defaultSemiBold">${item.price.toFixed(2)}</ThemedText>
        {item.expiry_date && (
          <Text style={styles.expiryDate}>
            Exp: {new Date(item.expiry_date).toLocaleDateString()}
          </Text>
        )}
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <SafeAreaView
        style={[
          styles.container,
          { backgroundColor, justifyContent: "center", alignItems: "center" },
        ]}
      >
        <ActivityIndicator size="large" />
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView
        style={[
          styles.container,
          { backgroundColor, justifyContent: "center", alignItems: "center" },
        ]}
      >
        <ThemedText>Error loading inventory</ThemedText>
        <ThemedText>{error.message}</ThemedText>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor }]}>
      <StatusBar style="auto" />
      <ThemedView style={styles.header}>
        <ThemedText type="title">Inventory</ThemedText>
      </ThemedView>
      <FlatList
        data={inventory}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        onRefresh={refetch}
        refreshing={isLoading}
      />
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
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  itemContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
  },
  itemInfo: {
    flex: 1,
    marginRight: 10,
  },
  itemName: {
    fontSize: 16,
    marginBottom: 4,
  },
  itemDetails: {
    fontSize: 14,
    color: "#888",
  },
  itemPrice: {
    alignItems: "flex-end",
  },
  expiryDate: {
    fontSize: 12,
    color: "#e74c3c",
    marginTop: 2,
  },
  separator: {
    height: 1,
    backgroundColor: "#f0f0f0",
    opacity: 0.5,
  },
});
