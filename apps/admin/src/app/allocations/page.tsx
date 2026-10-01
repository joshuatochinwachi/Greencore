"use client";

import React, { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import type {
  AllocationOverviewResponse,
  AssignmentItem,
  AllocationConfirmResponse,
} from "@greencore/shared-types";

export default function AllocationsPage() {
  const getTomorrowString = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  };

  const [selectedDate, setSelectedDate] = useState<string>(getTomorrowString());
  const [data, setData] = useState<AllocationOverviewResponse | null>(null);
  const [assignments, setAssignments] = useState<Record<string, string>>({}); // routeId -> driverId
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Confirm Modal
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [confirmResult, setConfirmResult] = useState<AllocationConfirmResponse | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchAllocations = useCallback(async (date: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.allocations.getOverview(date);
      setData(res);

      // Hydrate existing allocations
      const initialMap: Record<string, string> = {};
      res.allocations?.forEach((alloc) => {
        initialMap[alloc.route_id] = alloc.driver_id;
      });
      setAssignments(initialMap);
    } catch (err: any) {
      setError(err?.message || "Failed to load allocation data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllocations(selectedDate);
  }, [selectedDate, fetchAllocations]);

  const handleDriverSelect = (routeId: string, driverId: string) => {
    setAssignments((prev) => {
      const next = { ...prev };
      if (!driverId) {
        delete next[routeId];
      } else {
        next[routeId] = driverId;
      }
      return next;
    });
  };

  const handleConfirmSubmit = async () => {
    if (!data) return;
    setActionLoading(true);

    const payloadAssignments: AssignmentItem[] = Object.entries(assignments).map(([routeId, driverId]) => ({
      route_id: routeId,
      driver_id: driverId,
    }));

    try {
      const res = await api.allocations.confirm({
        date: selectedDate,
        assignments: payloadAssignments,
      });
      setConfirmResult(res);
      setNotification({
        type: "success",
        message: `Successfully confirmed ${res.confirmed} allocations and dispatched ${res.notifications_sent} notifications!`,
      });
      fetchAllocations(selectedDate);
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err?.message || "Failed to confirm allocations",
      });
      setIsConfirmOpen(false);
    } finally {
      setActionLoading(false);
    }
  };

  const assignedCount = Object.keys(assignments).length;
  const totalRoutes = data?.routes?.length || 0;

  // Find duplicate drivers in current draft
  const driverCounts: Record<string, number> = {};
  Object.values(assignments).forEach((dId) => {
    if (dId) driverCounts[dId] = (driverCounts[dId] || 0) + 1;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            Nightly Route Allocations
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
            Assign drivers to tomorrow&apos;s routes and broadcast push notifications (Section 6.1 & 14.4)
          </p>
        </div>

        <button
          onClick={() => {
            setConfirmResult(null);
            setIsConfirmOpen(true);
          }}
          disabled={assignedCount === 0 || loading}
          className="gc-btn-primary"
          style={{ padding: "12px 20px" }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Confirm & Send Notifications ({assignedCount})
        </button>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md)",
            backgroundColor: notification.type === "success" ? "var(--color-status-success-bg)" : "var(--color-status-danger-bg)",
            border: `1px solid ${notification.type === "success" ? "var(--color-status-success-border)" : "var(--color-status-danger-border)"}`,
            color: notification.type === "success" ? "var(--color-status-success)" : "var(--color-status-danger)",
            fontSize: "14px",
            fontWeight: 500,
          }}
        >
          {notification.message}
        </div>
      )}

      {/* Date Selector & Quick Toggles */}
      <div className="gc-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <label className="gc-label" style={{ margin: 0 }}>
            Allocation Date:
          </label>
          <input
            type="date"
            className="gc-input"
            style={{ width: "auto" }}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => {
              const d = new Date();
              setSelectedDate(d.toISOString().split("T")[0]);
            }}
            className="gc-btn-secondary"
            style={{ fontSize: "12px", padding: "6px 12px" }}
          >
            Today
          </button>
          <button
            onClick={() => setSelectedDate(getTomorrowString())}
            className="gc-btn-secondary"
            style={{ fontSize: "12px", padding: "6px 12px" }}
          >
            Tomorrow
          </button>
          <button
            onClick={() => {
              const d = new Date();
              d.setDate(d.getDate() + 2);
              setSelectedDate(d.toISOString().split("T")[0]);
            }}
            className="gc-btn-secondary"
            style={{ fontSize: "12px", padding: "6px 12px" }}
          >
            +2 Days
          </button>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="gc-badge gc-badge-info">
            {assignedCount} / {totalRoutes} Routes Assigned
          </span>
        </div>
      </div>

      {/* Main Allocation Matrix */}
      <div className="gc-table-container">
        {loading ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
            Loading available routes and drivers for {selectedDate}...
          </div>
        ) : error ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-status-danger)" }}>
            {error}
          </div>
        ) : !data || data.routes.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
            No routes found to allocate for this date.
          </div>
        ) : (
          <table className="gc-table">
            <thead>
              <tr>
                <th>Route Name</th>
                <th>Drop Count</th>
                <th>Assigned Driver</th>
                <th>Driver Role</th>
                <th>Status / Warnings</th>
              </tr>
            </thead>
            <tbody>
              {data.routes.map((route) => {
                const assignedDriverId = assignments[route.id] || "";
                const assignedDriver = data.drivers.find((d) => d.id === assignedDriverId);
                const hasDuplicate = assignedDriverId && driverCounts[assignedDriverId] > 1;

                return (
                  <tr key={route.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: "var(--color-text-primary)", fontSize: "15px" }}>
                        {route.route_name}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
                        {route.drop_count} drops
                      </span>
                    </td>
                    <td>
                      <select
                        className="gc-input"
                        value={assignedDriverId}
                        onChange={(e) => handleDriverSelect(route.id, e.target.value)}
                        style={{
                          minWidth: "220px",
                          borderColor: hasDuplicate ? "var(--color-status-danger)" : undefined,
                        }}
                      >
                        <option value="">— Select Driver —</option>
                        {data.drivers.map((driver) => (
                          <option key={driver.id} value={driver.id}>
                            {driver.full_name} ({driver.role.toUpperCase()})
                            {driver.already_scheduled ? " [Scheduled]" : ""}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {assignedDriver ? (
                        <span
                          style={{
                            padding: "3px 8px",
                            borderRadius: "var(--radius-xs)",
                            backgroundColor: "var(--color-surface-elevated)",
                            fontSize: "12px",
                            fontWeight: 600,
                            textTransform: "uppercase",
                          }}
                        >
                          {assignedDriver.role}
                        </span>
                      ) : (
                        <span style={{ color: "var(--color-text-muted)", fontSize: "12px" }}>Unallocated</span>
                      )}
                    </td>
                    <td>
                      {hasDuplicate ? (
                        <span className="gc-badge gc-badge-danger">
                          Duplicate Driver
                        </span>
                      ) : assignedDriver ? (
                        <span className="gc-badge gc-badge-success">
                          Ready to Confirm
                        </span>
                      ) : (
                        <span className="gc-badge gc-badge-neutral">
                          Unassigned
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Confirmation Modal (Section 6.1) */}
      <Modal
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        title="Confirm Nightly Route Allocations"
        subtitle={`Publishing assignments for ${selectedDate}`}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {confirmResult ? (
            <div
              style={{
                padding: "16px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-status-success-bg)",
                border: "1px solid var(--color-status-success-border)",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              <div style={{ color: "var(--color-status-success)", fontWeight: 700, fontSize: "16px" }}>
                ✓ Allocations Published
              </div>
              <div style={{ fontSize: "14px", color: "var(--color-text-primary)" }}>
                • <strong>{confirmResult.confirmed}</strong> route assignments committed.<br />
                • <strong>{confirmResult.notifications_sent}</strong> push notifications sent to mobile apps.<br />
                • Audit log entry: <code style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}>{confirmResult.audit_log_entry_id}</code>
              </div>
              <div style={{ marginTop: "12px", display: "flex", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setIsConfirmOpen(false)}
                  className="gc-btn-primary"
                >
                  Done
                </button>
              </div>
            </div>
          ) : (
            <>
              <div
                style={{
                  padding: "14px",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid var(--color-status-success-border)",
                  fontSize: "13px",
                  color: "var(--color-text-primary)",
                }}
              >
                You are about to confirm <strong>{assignedCount}</strong> route assignments for shift date <strong>{selectedDate}</strong>.
                Each allocated driver will receive an automated notification in their Greencore Driver app.
              </div>

              {Object.values(driverCounts).some((c) => c > 1) && (
                <div
                  style={{
                    padding: "12px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "var(--color-status-danger-bg)",
                    border: "1px solid var(--color-status-danger-border)",
                    color: "var(--color-status-danger)",
                    fontSize: "13px",
                    fontWeight: 600,
                  }}
                >
                  ⚠️ Warning: One or more drivers are assigned to multiple routes!
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setIsConfirmOpen(false)}
                  className="gc-btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleConfirmSubmit}
                  className="gc-btn-primary"
                >
                  {actionLoading ? "Broadcasting..." : `Confirm & Notify ${assignedCount} Drivers`}
                </button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
}
