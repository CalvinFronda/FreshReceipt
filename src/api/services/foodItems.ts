import apiClient from "../client";
import { FoodItem } from "../types";

export const getFoodItems = async (): Promise<FoodItem[]> => {
  const response = await apiClient.get<FoodItem[]>(
    "api/v1/households/food-items"
  );

  return response.data;
};
