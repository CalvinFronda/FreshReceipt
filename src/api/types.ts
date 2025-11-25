export interface FoodItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  unit?: string;
  purchase_date: string;
  expiry_date?: string;
}
