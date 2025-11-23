import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { useThemeColor } from "@/hooks/use-theme-color";
import { StatusBar } from "expo-status-bar";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

// Mocking the FoodItem model from api/app/models/food_item.py
interface FoodItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  unit?: string;
  purchase_date: string; // ISO string for simplicity in frontend
  expiry_date?: string;
}

const MOCK_INVENTORY: FoodItem[] = [
  {
    id: "1",
    name: "Organic Bananas",
    price: 2.99,
    quantity: 1,
    unit: "bunch",
    purchase_date: "2023-10-25T10:00:00Z",
    expiry_date: "2023-11-01T00:00:00Z",
  },
  {
    id: "2",
    name: "Almond Milk",
    price: 4.49,
    quantity: 1,
    unit: "carton",
    purchase_date: "2023-10-26T14:30:00Z",
    expiry_date: "2023-11-15T00:00:00Z",
  },
  {
    id: "3",
    name: "Sourdough Bread",
    price: 5.5,
    quantity: 1,
    unit: "loaf",
    purchase_date: "2023-10-27T09:15:00Z",
    expiry_date: "2023-11-03T00:00:00Z",
  },
  {
    id: "4",
    name: "Eggs (Dozen)",
    price: 3.99,
    quantity: 2,
    unit: "carton",
    purchase_date: "2023-10-28T11:00:00Z",
    expiry_date: "2023-11-20T00:00:00Z",
  },
  {
    id: "5",
    name: "Spinach",
    price: 2.49,
    quantity: 1,
    unit: "bag",
    purchase_date: "2023-10-29T16:45:00Z",
    expiry_date: "2023-11-05T00:00:00Z",
  },
];

export default function InventoryScreen() {
  const backgroundColor = useThemeColor({}, "background");

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

  return (
    <SafeAreaView style={[styles.container, { backgroundColor }]}>
      <StatusBar style="auto" />
      <ThemedView style={styles.header}>
        <ThemedText type="title">Inventory</ThemedText>
      </ThemedView>
      <FlatList
        data={MOCK_INVENTORY}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
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
