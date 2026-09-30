/**
 * Allocation API Contracts — Section 14.4
 */

import { AllocationStatus, DriverRoleCode } from "./enums.js";

export interface AllocationDriver {
  id: string;
  full_name: string;
  role: DriverRoleCode;
  already_scheduled: boolean;
  vehicle_id?: string | null;
}

export interface AllocationRoute {
  id: string;
  route_name: string;
  drop_count: number;
  allocated: boolean;
}

export interface AllocationItem {
  id: string;
  shift_date: string;
  driver_id: string;
  route_id: string;
  vehicle_id?: string | null;
  planned_start?: string | null;
  status: AllocationStatus;
}

export interface AllocationOverviewResponse {
  date: string;
  drivers: AllocationDriver[];
  routes: AllocationRoute[];
  allocations: AllocationItem[];
}

export interface AssignmentItem {
  driver_id: string;
  route_id: string;
  vehicle_id?: string | null;
  planned_start?: string | null;
}

export interface AllocationConfirmRequest {
  date: string;
  assignments: AssignmentItem[];
}

export interface AllocationConfirmResponse {
  confirmed: number;
  notifications_sent: number;
  audit_log_entry_id: string;
}
