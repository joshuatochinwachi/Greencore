"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import type {
  RouteSummary,
  RouteDetail,
  Drop,
  DropCreateRequest,
  VehicleType,
  RouteConflictWarningCode,
} from "@greencore/shared-types";

export default function RoutesPage() {
  const searchParams = useSearchParams();
  const initialRouteId = searchParams.get("id");

  const [routes, setRoutes] = useState<RouteSummary[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(initialRouteId);
  const [routeDetail, setRouteDetail] = useState<RouteDetail | null>(null);
  const [loadingRoutes, setLoadingRoutes] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [isCreateRouteOpen, setIsCreateRouteOpen] = useState(false);
  const [isAddDropOpen, setIsAddDropOpen] = useState(false);
  const [isMoveDropOpen, setIsMoveDropOpen] = useState(false);
  const [movingDrop, setMovingDrop] = useState<Drop | null>(null);

  // Create Route Form
  const [newRouteName, setNewRouteName] = useState("");
  const [newRouteMaxDrops, setNewRouteMaxDrops] = useState<number | undefined>(undefined);

  // Add Drop Form
  const [dropForm, setDropForm] = useState<DropCreateRequest>({
    customer_name: "",
    account_number: "",
    postcode: "",
    address: "",
    delivery_instructions: "",
    access_instructions: "",
    tray_instructions: "",
    required_vehicle_class: null,
    fixed_position: false,
  });

  // Move Drop State
  const [targetRouteId, setTargetRouteId] = useState("");
  const [targetSequence, setTargetSequence] = useState<number>(1);
  const [moveWarnings, setMoveWarnings] = useState<RouteConflictWarningCode[]>([]);
  const [forceOverride, setForceOverride] = useState(false);

  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "warning"; message: string } | null>(null);

  const showNotification = (type: "success" | "error" | "warning", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const fetchRoutes = useCallback(async () => {
    try {
      setLoadingRoutes(true);
      const res = await api.routes.list({ page_size: 50 });
      setRoutes(res.data || []);
      if (!selectedRouteId && res.data && res.data.length > 0) {
        setSelectedRouteId(res.data[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load routes");
    } finally {
      setLoadingRoutes(false);
    }
  }, [selectedRouteId]);

  const fetchRouteDetail = useCallback(async (routeId: string) => {
    try {
      setLoadingDetail(true);
      const detail = await api.routes.get(routeId);
      setRouteDetail(detail);
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to load route drops");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    fetchRoutes();
  }, [fetchRoutes]);

  useEffect(() => {
    if (selectedRouteId) {
      fetchRouteDetail(selectedRouteId);
    }
  }, [selectedRouteId, fetchRouteDetail]);

  const handleCreateRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRouteName) return;
    setActionLoading(true);
    try {
      const created = await api.routes.create({
        route_name: newRouteName,
        max_drops: newRouteMaxDrops || null,
      });
      setIsCreateRouteOpen(false);
      setNewRouteName("");
      setNewRouteMaxDrops(undefined);
      showNotification("success", `Route ${created.route_name} created successfully`);
      await fetchRoutes();
      setSelectedRouteId(created.id);
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to create route");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddDrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRouteId) return;
    setActionLoading(true);
    try {
      await api.routes.createDrop(selectedRouteId, dropForm);
      setIsAddDropOpen(false);
      setDropForm({
        customer_name: "",
        account_number: "",
        postcode: "",
        address: "",
        delivery_instructions: "",
        access_instructions: "",
        tray_instructions: "",
        required_vehicle_class: null,
        fixed_position: false,
      });
      showNotification("success", "Drop added with auto-sequencing");
      fetchRouteDetail(selectedRouteId);
      fetchRoutes();
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to add drop");
    } finally {
      setActionLoading(false);
    }
  };

  const openMoveModal = (drop: Drop) => {
    setMovingDrop(drop);
    const otherRoutes = routes.filter((r) => r.id !== selectedRouteId);
    setTargetRouteId(otherRoutes.length > 0 ? otherRoutes[0].id : "");
    setTargetSequence(1);
    setMoveWarnings([]);
    setForceOverride(false);
    setIsMoveDropOpen(true);
  };

  const handleMoveDrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!movingDrop || !targetRouteId) return;
    setActionLoading(true);

    try {
      const res = await api.routes.moveDrop(movingDrop.id, {
        target_route_id: targetRouteId,
        sequence: targetSequence,
        force: forceOverride,
      });

      if (!res.moved && res.warnings && res.warnings.length > 0) {
        // Warning encountered per Section 15.7 & 17.4
        setMoveWarnings(res.warnings);
        showNotification("warning", `Conflict warnings detected: ${res.warnings.join(", ")}`);
        return;
      }

      setIsMoveDropOpen(false);
      setMovingDrop(null);
      setMoveWarnings([]);
      setForceOverride(false);
      showNotification("success", "Drop successfully transferred and sequence updated");
      if (selectedRouteId) fetchRouteDetail(selectedRouteId);
      fetchRoutes();
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to move drop");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            Routes & Drops
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
            Maintain delivery sequences, drop instructions, and conflict checks (Section 14.3)
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={() => setIsCreateRouteOpen(true)} className="gc-btn-secondary">
            + New Route
          </button>
          <button
            onClick={() => setIsAddDropOpen(true)}
            disabled={!selectedRouteId}
            className="gc-btn-primary"
          >
            + Add Drop
          </button>
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md)",
            backgroundColor:
              notification.type === "success"
                ? "var(--color-status-success-bg)"
                : notification.type === "warning"
                ? "var(--color-status-warning-bg)"
                : "var(--color-status-danger-bg)",
            border: `1px solid ${
              notification.type === "success"
                ? "var(--color-status-success-border)"
                : notification.type === "warning"
                ? "var(--color-status-warning-border)"
                : "var(--color-status-danger-border)"
            }`,
            color:
              notification.type === "success"
                ? "var(--color-status-success)"
                : notification.type === "warning"
                ? "var(--color-status-warning)"
                : "var(--color-status-danger)",
            fontSize: "14px",
            fontWeight: 500,
          }}
        >
          {notification.message}
        </div>
      )}

      {/* Main Layout: Routes Left Bar + Drops Table Right */}
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
        {/* Left Side: Route Selector List */}
        <div className="gc-card" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "12px", height: "fit-content" }}>
          <div style={{ fontSize: "13px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-text-muted)" }}>
            Select Route
          </div>

          {loadingRoutes ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--color-text-muted)" }}>
              Loading routes...
            </div>
          ) : routes.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--color-text-muted)" }}>
              No routes available.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {routes.map((r) => {
                const isSelected = selectedRouteId === r.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRouteId(r.id)}
                    style={{
                      textAlign: "left",
                      padding: "12px 14px",
                      borderRadius: "var(--radius-md)",
                      backgroundColor: isSelected ? "var(--color-surface-elevated)" : "transparent",
                      border: isSelected ? "1px solid var(--color-border-focus)" : "1px solid transparent",
                      color: isSelected ? "#FFFFFF" : "var(--color-text-primary)",
                      cursor: "pointer",
                      transition: "all var(--transition-fast)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ fontWeight: 600, fontSize: "14px" }}>{r.route_name}</span>
                      <span className={`gc-badge ${r.status === "active" ? "gc-badge-success" : "gc-badge-neutral"}`} style={{ fontSize: "10px", padding: "2px 6px" }}>
                        {r.status}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                      {r.drop_count} drops {r.max_drops ? `(max ${r.max_drops})` : ""}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side: Drops in Selected Route */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {routeDetail && (
            <div className="gc-card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--color-text-primary)" }}>
                  {routeDetail.route_name}
                </h2>
                <div style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginTop: "2px" }}>
                  {routeDetail.drops?.length || 0} stops in delivery order
                </div>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <span className="gc-badge gc-badge-info">
                  {routeDetail.drops?.length || 0} Drops Configured
                </span>
              </div>
            </div>
          )}

          <div className="gc-table-container">
            {loadingDetail ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
                Loading drops for route...
              </div>
            ) : !routeDetail || !routeDetail.drops || routeDetail.drops.length === 0 ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
                No drops assigned to this route yet. Click &quot;+ Add Drop&quot; above to create one.
              </div>
            ) : (
              <table className="gc-table">
                <thead>
                  <tr>
                    <th style={{ width: "60px" }}>Seq</th>
                    <th>Customer & Account</th>
                    <th>Location / Postcode</th>
                    <th>Instructions</th>
                    <th>Vehicle Req</th>
                    <th style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {routeDetail.drops.map((drop) => (
                    <tr key={drop.id}>
                      <td>
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: "28px",
                            height: "28px",
                            borderRadius: "50%",
                            backgroundColor: "var(--color-surface-elevated)",
                            color: "var(--color-primary-bright)",
                            fontWeight: 700,
                            fontSize: "13px",
                          }}
                        >
                          {drop.sequence}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--color-text-primary)" }}>
                          {drop.customer_name}
                        </div>
                        {drop.account_number && (
                          <div style={{ fontSize: "11px", color: "var(--color-text-muted)", fontFamily: "var(--font-mono)" }}>
                            Acc: {drop.account_number}
                          </div>
                        )}
                      </td>
                      <td>
                        <div style={{ fontSize: "13px" }}>{drop.address || "—"}</div>
                        <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", fontWeight: 600 }}>
                          {drop.postcode}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: "12px", maxWidth: "250px", color: "var(--color-text-secondary)" }}>
                          {drop.delivery_instructions || "No specific instructions"}
                        </div>
                      </td>
                      <td>
                        {drop.required_vehicle_class ? (
                          <span
                            style={{
                              padding: "3px 8px",
                              borderRadius: "var(--radius-xs)",
                              backgroundColor: "var(--color-surface-elevated)",
                              fontSize: "11px",
                              fontWeight: 600,
                              textTransform: "uppercase",
                              color: "var(--color-status-warning)",
                            }}
                          >
                            {drop.required_vehicle_class}
                          </span>
                        ) : (
                          <span style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Any</span>
                        )}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <button
                          onClick={() => openMoveModal(drop)}
                          className="gc-btn-secondary"
                          style={{ padding: "5px 10px", fontSize: "12px" }}
                        >
                          Move Drop
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Create Route */}
      <Modal
        isOpen={isCreateRouteOpen}
        onClose={() => setIsCreateRouteOpen(false)}
        title="Create New Delivery Route"
      >
        <form onSubmit={handleCreateRoute} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label className="gc-label">Route Name *</label>
            <input
              type="text"
              required
              className="gc-input"
              value={newRouteName}
              onChange={(e) => setNewRouteName(e.target.value)}
              placeholder="e.g. LONDON CENTRAL 04"
            />
          </div>

          <div>
            <label className="gc-label">Max Drop Capacity (Optional)</label>
            <input
              type="number"
              className="gc-input"
              value={newRouteMaxDrops || ""}
              onChange={(e) => setNewRouteMaxDrops(e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="e.g. 35"
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsCreateRouteOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="gc-btn-primary"
            >
              {actionLoading ? "Creating..." : "Save Route"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Add Drop */}
      <Modal
        isOpen={isAddDropOpen}
        onClose={() => setIsAddDropOpen(false)}
        title="Add Drop to Route"
        subtitle={`Appends stop to ${routeDetail?.route_name}`}
        maxWidth="600px"
      >
        <form onSubmit={handleAddDrop} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "12px" }}>
            <div>
              <label className="gc-label">Customer / Business Name *</label>
              <input
                type="text"
                required
                className="gc-input"
                value={dropForm.customer_name}
                onChange={(e) => setDropForm({ ...dropForm, customer_name: e.target.value })}
                placeholder="e.g. Sainsburys Superstore"
              />
            </div>
            <div>
              <label className="gc-label">Account #</label>
              <input
                type="text"
                className="gc-input"
                value={dropForm.account_number || ""}
                onChange={(e) => setDropForm({ ...dropForm, account_number: e.target.value })}
                placeholder="e.g. ACC8821"
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "12px" }}>
            <div>
              <label className="gc-label">Postcode *</label>
              <input
                type="text"
                required
                className="gc-input"
                value={dropForm.postcode || ""}
                onChange={(e) => setDropForm({ ...dropForm, postcode: e.target.value })}
                placeholder="e.g. SW1A 1AA"
              />
            </div>
            <div>
              <label className="gc-label">Full Address</label>
              <input
                type="text"
                className="gc-input"
                value={dropForm.address || ""}
                onChange={(e) => setDropForm({ ...dropForm, address: e.target.value })}
                placeholder="e.g. 10 High Street, Westminster"
              />
            </div>
          </div>

          <div>
            <label className="gc-label">Delivery Instructions</label>
            <textarea
              className="gc-input"
              rows={2}
              value={dropForm.delivery_instructions || ""}
              onChange={(e) => setDropForm({ ...dropForm, delivery_instructions: e.target.value })}
              placeholder="e.g. Deliver via goods in bay 2. Ring buzzer."
            />
          </div>

          <div>
            <label className="gc-label">Required Vehicle Class</label>
            <select
              className="gc-input"
              value={dropForm.required_vehicle_class || ""}
              onChange={(e) =>
                setDropForm({
                  ...dropForm,
                  required_vehicle_class: (e.target.value as VehicleType) || null,
                })
              }
            >
              <option value="">Any Vehicle Class</option>
              <option value="van">Van</option>
              <option value="7_5t">7.5 Tonne</option>
              <option value="class2_rigid">Class 2 Rigid</option>
              <option value="class1_hgv">Class 1 Articulated HGV</option>
            </select>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsAddDropOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="gc-btn-primary"
            >
              {actionLoading ? "Adding..." : "Add Drop to Sequence"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Move Drop with Conflict Warnings (Section 15.7 & 17.4) */}
      <Modal
        isOpen={isMoveDropOpen}
        onClose={() => setIsMoveDropOpen(false)}
        title="Move Drop to Another Route"
        subtitle={`Transfer stop "${movingDrop?.customer_name}" to a different route sequence`}
      >
        <form onSubmit={handleMoveDrop} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label className="gc-label">Target Route *</label>
            <select
              className="gc-input"
              value={targetRouteId}
              onChange={(e) => {
                setTargetRouteId(e.target.value);
                setMoveWarnings([]);
              }}
            >
              {routes
                .filter((r) => r.id !== selectedRouteId)
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.route_name} ({r.drop_count} drops)
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="gc-label">Insert at Sequence Position *</label>
            <input
              type="number"
              min={1}
              required
              className="gc-input"
              value={targetSequence}
              onChange={(e) => setTargetSequence(parseInt(e.target.value) || 1)}
            />
          </div>

          {/* Conflict Warnings Banner (Section 17.4) */}
          {moveWarnings.length > 0 && (
            <div
              style={{
                padding: "14px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-status-warning-bg)",
                border: "1px solid var(--color-status-warning-border)",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              <div style={{ color: "var(--color-status-warning)", fontWeight: 700, fontSize: "14px" }}>
                ⚠️ Route Conflict Warning Detected
              </div>
              <ul style={{ paddingLeft: "20px", fontSize: "13px", color: "var(--color-text-primary)" }}>
                {moveWarnings.map((w, idx) => (
                  <li key={idx}>
                    {w === "vehicle_class_mismatch"
                      ? "Vehicle class mismatch: Drop requires a specific vehicle qualification."
                      : w === "capacity_exceeded"
                      ? "Capacity exceeded: Target route exceeds its maximum configured drop count."
                      : `Warning: ${w}`}
                  </li>
                ))}
              </ul>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
                <input
                  type="checkbox"
                  id="forceOverride"
                  checked={forceOverride}
                  onChange={(e) => setForceOverride(e.target.checked)}
                />
                <label htmlFor="forceOverride" style={{ fontSize: "13px", color: "var(--color-text-primary)", fontWeight: 600 }}>
                  Acknowledge and Force Override (logged to audit trail)
                </label>
              </div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsMoveDropOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading || (moveWarnings.length > 0 && !forceOverride)}
              className="gc-btn-primary"
            >
              {actionLoading ? "Transferring..." : moveWarnings.length > 0 ? "Confirm Override & Move" : "Transfer Drop"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
