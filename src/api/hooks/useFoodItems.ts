import { useQuery } from "@tanstack/react-query";
import { getFoodItems } from "../services/foodItems";
import { FoodItem } from "../types";

export const useFoodItems = () => {
  return useQuery<FoodItem[], Error>({
    queryKey: ["foodItems"],
    queryFn: getFoodItems,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
