import apiClient from "../client";

export interface Household {
  id: string;
  name: string;
  role: string;
}
//TODO: This doesn't work, needs household ID
export const getHouseholds = async (): Promise<Household[]> => {
  const response = await apiClient.get<Household[]>("/api/v1/households");
  return response.data;
};
