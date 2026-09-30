/**
 * Driver API Contracts — Section 14.2
 */

import { DriverRoleCode, DriverStatus } from "./enums.js";

export interface Driver {
  id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  photo_url?: string | null;
  role: DriverRoleCode;
  licence_number?: string | null;
  status: DriverStatus;
  depot_id?: string | null;
  vehicle_id?: string | null;
  created_at: string;
}

export interface DriverListResponse {
  data: Driver[];
  page: number;
  page_size: number;
  total: number;
}

export interface DriverCreateRequest {
  full_name: string;
  email: string;
  password: string;
  phone?: string | null;
  photo_url?: string | null;
  role: DriverRoleCode;
  licence_number?: string | null;
  depot_id?: string | null;
  vehicle_id?: string | null;
}

export interface DriverUpdateRequest {
  full_name?: string;
  email?: string;
  phone?: string | null;
  photo_url?: string | null;
  role?: DriverRoleCode;
  licence_number?: string | null;
  status?: DriverStatus;
  depot_id?: string | null;
  vehicle_id?: string | null;
}

export interface DriverDeactivateRequest {
  reason?: string;
}

export interface DriverDeactivateResponse {
  id: string;
  status: "inactive";
  deactivated_at: string;
}
