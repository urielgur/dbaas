import { apiClient } from "../api/client";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MeResponse {
  username: string;
  is_admin: boolean;
  created_at: string;
}

export async function loginRequest(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", {
    username,
    password,
  });
  return data;
}

export async function getMeRequest(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>("/auth/me");
  return data;
}
