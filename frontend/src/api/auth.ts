/**
 * url: /frontend/src/api/auth.ts
 * About:
 *   Auth API functions for ValLG frontend. Handles login, logout,
 *   and current user retrieval. Stores JWT token in localStorage.
 */

import { apiClient } from './client';
import type { AuthResponse, User } from '../types';

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await apiClient.post<{ token: string; user: User }>('/auth/login', {
    email,
    password,
  });
  localStorage.setItem('vallg_token', response.token);
  return { token: response.token, user: response.user };
}

export async function signup(name: string, email: string, password: string): Promise<AuthResponse> {
  const response = await apiClient.post<{ token: string; user: User }>('/auth/signup', {
    name,
    email,
    password,
  });
  localStorage.setItem('vallg_token', response.token);
  return { token: response.token, user: response.user };
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
  localStorage.removeItem('vallg_token');
}

export async function getCurrentUser(): Promise<User> {
  return apiClient.get<User>('/auth/me');
}
