/**
 * Auth API Contracts — Section 14.1
 */

import { AdminPermissionRole, DriverRoleCode } from "./enums.js";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserSessionDriver {
  id: string;
  type: "driver";
  full_name: string;
  role: DriverRoleCode;
  depot_id?: string | null;
}

export interface UserSessionAdmin {
  id: string;
  type: "admin";
  full_name: string;
  permission_role: AdminPermissionRole;
}

export type UserSession = UserSessionDriver | UserSessionAdmin;

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: UserSession;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  expires_in: number;
}

export interface InviteDriverRequest {
  email: string;
  full_name: string;
  role: DriverRoleCode;
  depot_id?: string | null;
}

export interface InviteDriverResponse {
  invite_id: string;
  status: "pending";
  expires_at: string;
}
