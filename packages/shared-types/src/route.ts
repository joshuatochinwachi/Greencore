/**
 * Route & Drop API Contracts — Section 14.3
 */

import { DropStatus, RouteConflictWarningCode, RouteStatus, VehicleType } from "./enums.js";

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface Drop {
  id: string;
  sequence: number;
  account_number?: string | null;
  customer_name: string;
  address?: string | null;
  postcode?: string | null;
  location?: GeoPoint | null;
  delivery_instructions?: string | null;
  access_instructions?: string | null;
  tray_instructions?: string | null;
  opening_hours?: Record<string, string> | null;
  contact_phone?: string | null;
  fixed_position: boolean;
  must_precede_drop_id?: string | null;
  required_vehicle_class?: VehicleType | null;
  status: DropStatus;
}

export interface RouteSummary {
  id: string;
  route_name: string;
  depot_id?: string | null;
  status: RouteStatus;
  max_drops?: number | null;
  drop_count: number;
}

export interface RouteDetail {
  id: string;
  route_name: string;
  depot_id?: string | null;
  start_point?: GeoPoint | null;
  end_point?: GeoPoint | null;
  status: RouteStatus;
  max_drops?: number | null;
  drops: Drop[];
}

export interface DropCreateRequest {
  customer_name: string;
  account_number?: string | null;
  address?: string | null;
  postcode?: string | null;
  location?: GeoPoint | null;
  delivery_instructions?: string | null;
  access_instructions?: string | null;
  tray_instructions?: string | null;
  opening_hours?: Record<string, string> | null;
  contact_phone?: string | null;
  sequence?: number | null;
  fixed_position?: boolean;
  must_precede_drop_id?: string | null;
  required_vehicle_class?: VehicleType | null;
}

export interface DropUpdateRequest {
  customer_name?: string;
  account_number?: string | null;
  address?: string | null;
  postcode?: string | null;
  location?: GeoPoint | null;
  delivery_instructions?: string | null;
  access_instructions?: string | null;
  tray_instructions?: string | null;
  opening_hours?: Record<string, string> | null;
  contact_phone?: string | null;
  sequence?: number | null;
  fixed_position?: boolean;
  must_precede_drop_id?: string | null;
  required_vehicle_class?: VehicleType | null;
  status?: DropStatus;
}

export interface DropMoveRequest {
  target_route_id: string;
  sequence: number;
  force?: boolean;
}

export interface DropMoveResponse {
  moved: boolean;
  warnings: RouteConflictWarningCode[];
}

export interface RouteImportPreviewResponse {
  import_id: string;
  detected_columns: string[];
  row_count: number;
  sample_rows: Record<string, string>[];
}

export interface RouteImportCommitRequest {
  import_id: string;
  column_mapping: Record<string, string>;
  default_route_name?: string;
  depot_id?: string | null;
}

export interface RouteImportError {
  row: number;
  reason: string;
}

export interface RouteImportCommitResponse {
  imported: number;
  failed: number;
  errors: RouteImportError[];
}
