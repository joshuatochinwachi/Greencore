"use client";

import React, { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import type { Driver, DriverRoleCode, DriverStatus } from "@greencore/shared-types";

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeactivateOpen, setIsDeactivateOpen] = useState(false);
  const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    phone: "",
    licence_number: "",
    role: "van" as DriverRoleCode,
  });

  const [editFormData, setEditFormData] = useState<{
    full_name: string;
    phone: string;
    licence_number: string;
    role: DriverRoleCode;
    status: DriverStatus;
  }>({
    full_name: "",
    phone: "",
    licence_number: "",
    role: "van",
    status: "active",
  });

  const [deactivateReason, setDeactivateReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchDrivers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.drivers.list({
        status: statusFilter || undefined,
        role: roleFilter || undefined,
        page_size: 50,
      });
      setDrivers(res.data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load drivers");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, roleFilter]);

  useEffect(() => {
    fetchDrivers();
  }, [fetchDrivers]);

  const showNotification = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.drivers.create({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        phone: formData.phone || null,
        licence_number: formData.licence_number || null,
        role: formData.role,
      });
      setIsCreateOpen(false);
      setFormData({
        full_name: "",
        email: "",
        password: "",
        phone: "",
        licence_number: "",
        role: "van",
      });
      showNotification("success", "Driver registered successfully");
      fetchDrivers();
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to create driver");
    } finally {
      setActionLoading(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDriver) return;
    setActionLoading(true);
    try {
      await api.drivers.update(selectedDriver.id, {
        full_name: editFormData.full_name,
        phone: editFormData.phone || null,
        licence_number: editFormData.licence_number || null,
        role: editFormData.role,
        status: editFormData.status,
      });
      setIsEditOpen(false);
      showNotification("success", "Driver updated successfully (audit diff logged)");
      fetchDrivers();
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to update driver");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDriver) return;
    setActionLoading(true);
    try {
      await api.drivers.deactivate(selectedDriver.id, {
        reason: deactivateReason || "Operational deactivation",
      });
      setIsDeactivateOpen(false);
      setDeactivateReason("");
      showNotification("success", "Driver deactivated and active sessions revoked");
      fetchDrivers();
    } catch (err: any) {
      showNotification("error", err?.message || "Failed to deactivate driver");
    } finally {
      setActionLoading(false);
    }
  };

  const openEditModal = (driver: Driver) => {
    setSelectedDriver(driver);
    setEditFormData({
      full_name: driver.full_name,
      phone: driver.phone || "",
      licence_number: driver.licence_number || "",
      role: driver.role,
      status: driver.status,
    });
    setIsEditOpen(true);
  };

  const openDeactivateModal = (driver: Driver) => {
    setSelectedDriver(driver);
    setDeactivateReason("");
    setIsDeactivateOpen(true);
  };

  const filteredDrivers = drivers.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.full_name.toLowerCase().includes(q) ||
      d.email.toLowerCase().includes(q) ||
      (d.licence_number && d.licence_number.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Page Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            Driver Fleet Management
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
            Manage driver accounts, vehicle classes, and access authorization per Section 14.2
          </p>
        </div>

        <button onClick={() => setIsCreateOpen(true)} className="gc-btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Register Driver
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

      {/* Filter and Search Bar */}
      <div className="gc-card" style={{ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ flex: 1, minWidth: "220px" }}>
          <input
            type="text"
            className="gc-input"
            placeholder="Search by name, email, or licence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <select
            className="gc-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: "auto", minWidth: "140px" }}
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="on_shift">On Shift</option>
            <option value="off_shift">Off Shift</option>
          </select>

          <select
            className="gc-input"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            style={{ width: "auto", minWidth: "140px" }}
          >
            <option value="">All Vehicle Roles</option>
            <option value="van">Van</option>
            <option value="7_5t">7.5 Tonne</option>
            <option value="class1">Class 1 HGV</option>
            <option value="class2">Class 2 Rigid</option>
          </select>

          {(statusFilter || roleFilter || searchQuery) && (
            <button
              onClick={() => {
                setStatusFilter("");
                setRoleFilter("");
                setSearchQuery("");
              }}
              className="gc-btn-secondary"
              style={{ fontSize: "13px" }}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Drivers Table */}
      <div className="gc-table-container">
        {loading ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
            Loading drivers from Railway API...
          </div>
        ) : error ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-status-danger)" }}>
            {error}
          </div>
        ) : filteredDrivers.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-text-muted)" }}>
            No drivers found matching current filters.
          </div>
        ) : (
          <table className="gc-table">
            <thead>
              <tr>
                <th>Driver</th>
                <th>Role / Class</th>
                <th>Status</th>
                <th>Phone</th>
                <th>Licence Number</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDrivers.map((driver) => (
                <tr key={driver.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div
                        style={{
                          width: "32px",
                          height: "32px",
                          borderRadius: "50%",
                          backgroundColor: "var(--color-surface-elevated)",
                          color: "#FFFFFF",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: 700,
                          fontSize: "13px",
                        }}
                      >
                        {driver.full_name.charAt(0)}
                      </div>
                      <div>
                        <div style={{ fontWeight: "600" }}>{driver.full_name}</div>
                        <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>{driver.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
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
                      {driver.role}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`gc-badge ${
                        driver.status === "active"
                          ? "gc-badge-success"
                          : driver.status === "on_shift"
                          ? "gc-badge-info"
                          : "gc-badge-neutral"
                      }`}
                    >
                      {driver.status}
                    </span>
                  </td>
                  <td>{driver.phone || "—"}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "13px" }}>
                    {driver.licence_number || "—"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "8px" }}>
                      <button
                        onClick={() => openEditModal(driver)}
                        className="gc-btn-secondary"
                        style={{ padding: "6px 12px", fontSize: "12px" }}
                      >
                        Edit
                      </button>
                      {driver.status === "active" && (
                        <button
                          onClick={() => openDeactivateModal(driver)}
                          className="gc-btn-danger"
                          style={{ padding: "6px 12px", fontSize: "12px" }}
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal: Create Driver */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register New Driver"
        subtitle="Creates driver record with authentication credentials and vehicle qualification"
      >
        <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label className="gc-label">Full Name *</label>
            <input
              type="text"
              required
              className="gc-input"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              placeholder="e.g. John Miller"
            />
          </div>

          <div>
            <label className="gc-label">Email Address *</label>
            <input
              type="email"
              required
              className="gc-input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="e.g. jmiller@greencore.com"
            />
          </div>

          <div>
            <label className="gc-label">Initial Password *</label>
            <input
              type="password"
              required
              className="gc-input"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="At least 8 characters"
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label className="gc-label">Phone Number</label>
              <input
                type="text"
                className="gc-input"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="e.g. 07123 456789"
              />
            </div>
            <div>
              <label className="gc-label">Licence Number</label>
              <input
                type="text"
                className="gc-input"
                value={formData.licence_number}
                onChange={(e) => setFormData({ ...formData, licence_number: e.target.value })}
                placeholder="e.g. MILL901234JM9AB"
              />
            </div>
          </div>

          <div>
            <label className="gc-label">Vehicle Qualification Role *</label>
            <select
              className="gc-input"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as DriverRoleCode })}
            >
              <option value="van">Van (Standard Commercial)</option>
              <option value="7_5t">7.5 Tonne Rigid</option>
              <option value="class2">Class 2 Rigid HGV</option>
              <option value="class1">Class 1 Articulated HGV</option>
            </select>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="gc-btn-primary"
            >
              {actionLoading ? "Registering..." : "Create Driver Account"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Driver */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Driver Profile"
        subtitle={`Updating ${selectedDriver?.full_name} — field changes are logged to audit trail`}
      >
        <form onSubmit={handleEdit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label className="gc-label">Full Name</label>
            <input
              type="text"
              required
              className="gc-input"
              value={editFormData.full_name}
              onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label className="gc-label">Phone</label>
              <input
                type="text"
                className="gc-input"
                value={editFormData.phone}
                onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="gc-label">Licence Number</label>
              <input
                type="text"
                className="gc-input"
                value={editFormData.licence_number}
                onChange={(e) => setEditFormData({ ...editFormData, licence_number: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label className="gc-label">Role</label>
              <select
                className="gc-input"
                value={editFormData.role}
                onChange={(e) => setEditFormData({ ...editFormData, role: e.target.value as DriverRoleCode })}
              >
                <option value="van">Van</option>
                <option value="7_5t">7.5 Tonne</option>
                <option value="class2">Class 2</option>
                <option value="class1">Class 1</option>
              </select>
            </div>
            <div>
              <label className="gc-label">Status</label>
              <select
                className="gc-input"
                value={editFormData.status}
                onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value as DriverStatus })}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="on_shift">On Shift</option>
                <option value="off_shift">Off Shift</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="gc-btn-primary"
            >
              {actionLoading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Deactivate Driver */}
      <Modal
        isOpen={isDeactivateOpen}
        onClose={() => setIsDeactivateOpen(false)}
        title="Deactivate Driver"
        subtitle="Per Section 14.2: Immediately revokes all active JWT tokens and sessions"
      >
        <form onSubmit={handleDeactivate} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              padding: "12px 14px",
              backgroundColor: "rgba(239, 68, 68, 0.12)",
              border: "1px solid var(--color-status-danger-border)",
              borderRadius: "var(--radius-md)",
              color: "var(--color-status-danger)",
              fontSize: "13px",
            }}
          >
            Are you sure you want to deactivate <strong>{selectedDriver?.full_name}</strong>? They will be logged out on all devices immediately.
          </div>

          <div>
            <label className="gc-label">Reason for Deactivation</label>
            <textarea
              className="gc-input"
              rows={3}
              placeholder="e.g. Left company, medical suspension, or licence review"
              value={deactivateReason}
              onChange={(e) => setDeactivateReason(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              type="button"
              onClick={() => setIsDeactivateOpen(false)}
              className="gc-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="gc-btn-danger"
            >
              {actionLoading ? "Revoking..." : "Confirm Deactivation"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
