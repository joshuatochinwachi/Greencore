/**
 * Greencore Domain Enums — Section 15 of GREENCORE_DOCUMENTATION.md
 */

// 15.1 Driver licence roles
export type DriverRoleCode = "van" | "7_5t" | "class1" | "class2";

// 15.2 Driver status
export type DriverStatus = "active" | "inactive";

// 15.3 Vehicle status
export type VehicleStatus = "active" | "in_repair" | "retired";

// 15.4 Vehicle type (mirrors driver roles)
export type VehicleType = "van" | "7_5t" | "class1_hgv" | "class2_hgv";

// 15.5 Route status
export type RouteStatus = "active" | "inactive";

// 15.6 Drop status
export type DropStatus =
  | "not_started"
  | "en_route"
  | "arrived"
  | "delivered"
  | "partial"
  | "failed"
  | "closed"
  | "no_access"
  | "other";

// 15.7 Route-edit conflict warning codes
export type RouteConflictWarningCode =
  | "vehicle_class_mismatch"
  | "route_capacity_exceeded"
  | "duplicate_drop"
  | "time_window_conflict";

// 15.8 Delivery status (mirrors drop status)
export type DeliveryStatus = DropStatus;

// 15.9 Delivery failure reasons
export type DeliveryFailureReason =
  | "shop_closed"
  | "no_access"
  | "loading_bay_unavailable"
  | "road_closed"
  | "customer_refused"
  | "wrong_address"
  | "vehicle_issue"
  | "product_unavailable"
  | "other";

// 15.10 Allocation status
export type AllocationStatus = "draft" | "confirmed" | "notified";

// 15.11 Chat message scope
export type ChatScope = "route" | "depot" | "global";

// 15.12 Announcement target type
export type AnnouncementTargetType =
  | "all"
  | "driver"
  | "route"
  | "depot"
  | "vehicle_category";

// 15.13 Admin permission roles
export type AdminPermissionRole =
  | "super_admin"
  | "ops_manager"
  | "route_manager"
  | "payroll_hr"
  | "read_only";

// 15.14 Incident report type
export type IncidentType =
  | "accident"
  | "road_closure"
  | "vehicle_breakdown"
  | "serious_delay"
  | "dangerous_location"
  | "delivery_problem"
  | "emergency";

// 15.15 Defect report type
export type DefectType =
  | "tyre"
  | "warning_light"
  | "brakes"
  | "lights"
  | "damage"
  | "other";

// 15.16 Defect report status
export type DefectStatus = "open" | "acknowledged" | "resolved";

// 15.17 Notification type
export type NotificationType =
  | "route_allocated"
  | "shift_reminder"
  | "route_changed"
  | "admin_announcement";
