"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { Driver, RouteSummary, AllocationOverviewResponse } from "@greencore/shared-types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [routes, setRoutes] = useState<RouteSummary[]>([]);
  const [allocationOverview, setAllocationOverview] = useState<AllocationOverviewResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split("T")[0];

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const [driversRes, routesRes, allocRes, healthRes] = await Promise.allSettled([
          api.drivers.list({ page_size: 20 }),
          api.routes.list({ page_size: 20 }),
          api.allocations.getOverview(tomorrowStr),
          api.meta.getHealth(),
        ]);

        if (driversRes.status === "fulfilled") {
          setDrivers(driversRes.value.data || []);
        }
        if (routesRes.status === "fulfilled") {
          setRoutes(routesRes.value.data || []);
        }
        if (allocRes.status === "fulfilled") {
          setAllocationOverview(allocRes.value);
        }
        if (healthRes.status === "fulfilled") {
          setHealthStatus(healthRes.value);
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, [tomorrowStr]);

  const activeDriversCount = drivers.filter((d) => d.status === "active").length;
  const totalDrops = routes.reduce((acc, r) => acc + (r.drop_count || 0), 0);
  const allocatedDrivers = allocationOverview?.drivers.filter((d) => d.already_scheduled).length || 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Top Banner / Welcome */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "16px",
      }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            Operations Dispatch Control
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
            Real-time fleet overview, route allocation status, and network health.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/allocations" className="gc-btn-primary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            Daily Allocations
          </Link>
          <Link href="/import" className="gc-btn-secondary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Import CSV
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: "20px",
      }}>
        {/* KPI 1: Active Drivers */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--color-text-secondary)" }}>
              Registered Drivers
            </span>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              backgroundColor: "rgba(16, 185, 129, 0.15)",
              color: "var(--color-primary-bright)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span style={{ fontSize: "32px", fontWeight: "800", color: "var(--color-text-primary)" }}>
              {loading ? "..." : drivers.length}
            </span>
            <span style={{ fontSize: "13px", color: "var(--color-status-success)", fontWeight: "600" }}>
              {activeDriversCount} active
            </span>
          </div>
          <Link href="/drivers" style={{ fontSize: "12px", color: "var(--color-primary-bright)", display: "flex", alignItems: "center", gap: "4px" }}>
            Manage fleet ↗
          </Link>
        </div>

        {/* KPI 2: Active Routes */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--color-text-secondary)" }}>
              Active Routes
            </span>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              backgroundColor: "rgba(56, 189, 248, 0.15)",
              color: "var(--color-status-info)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="6" cy="19" r="3" />
                <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" />
              </svg>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span style={{ fontSize: "32px", fontWeight: "800", color: "var(--color-text-primary)" }}>
              {loading ? "..." : routes.length}
            </span>
            <span style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
              {totalDrops} total drops
            </span>
          </div>
          <Link href="/routes" style={{ fontSize: "12px", color: "var(--color-status-info)", display: "flex", alignItems: "center", gap: "4px" }}>
            View drops & sequences ↗
          </Link>
        </div>

        {/* KPI 3: Tomorrow's Allocations */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--color-text-secondary)" }}>
              Tomorrow&apos;s Allocations
            </span>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              color: "var(--color-status-warning)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
              </svg>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span style={{ fontSize: "32px", fontWeight: "800", color: "var(--color-text-primary)" }}>
              {loading ? "..." : allocatedDrivers}
            </span>
            <span style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
              of {allocationOverview?.drivers.length || 0} scheduled
            </span>
          </div>
          <Link href="/allocations" style={{ fontSize: "12px", color: "var(--color-status-warning)", display: "flex", alignItems: "center", gap: "4px" }}>
            Review allocation matrix ↗
          </Link>
        </div>

        {/* KPI 4: Railway API Health */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--color-text-secondary)" }}>
              Production Backend
            </span>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              backgroundColor: "rgba(16, 185, 129, 0.15)",
              color: "var(--color-primary-bright)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}>
              <span className="gc-pulse-dot" />
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span style={{ fontSize: "20px", fontWeight: "700", color: "var(--color-primary-bright)", textTransform: "capitalize" }}>
              {healthStatus ? healthStatus.environment : "Production"}
            </span>
            <span style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>
              FastAPI + PostGIS
            </span>
          </div>
          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: "12px", color: "var(--color-primary-bright)", display: "flex", alignItems: "center", gap: "4px" }}
          >
            Interactive Swagger UI ↗
          </a>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "24px" }}>
        {/* Left Column: Routes Overview */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--color-text-primary)" }}>
                Active Route Portfolio
              </h2>
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
                Routes configured for driver execution
              </p>
            </div>
            <Link href="/routes" className="gc-btn-secondary" style={{ padding: "6px 12px", fontSize: "13px" }}>
              All Routes
            </Link>
          </div>

          {loading ? (
            <p style={{ color: "var(--color-text-muted)", padding: "20px 0" }}>Loading routes...</p>
          ) : routes.length === 0 ? (
            <div style={{ padding: "32px", textAlign: "center", color: "var(--color-text-muted)" }}>
              No active routes found. Use <Link href="/import" style={{ color: "var(--color-primary-bright)" }}>Route Import</Link> to upload route cards.
            </div>
          ) : (
            <div className="gc-table-container">
              <table className="gc-table">
                <thead>
                  <tr>
                    <th>Route Name</th>
                    <th>Status</th>
                    <th>Drops</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {routes.slice(0, 5).map((route) => (
                    <tr key={route.id}>
                      <td style={{ fontWeight: "600" }}>{route.route_name}</td>
                      <td>
                        <span className={`gc-badge ${route.status === "active" ? "gc-badge-success" : "gc-badge-neutral"}`}>
                          {route.status}
                        </span>
                      </td>
                      <td>{route.drop_count} drops</td>
                      <td>
                        <Link
                          href={`/routes?id=${route.id}`}
                          style={{ color: "var(--color-primary-bright)", fontSize: "13px", fontWeight: "600" }}
                        >
                          View Drops →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Column: Driver Fleet Quick View */}
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--color-text-primary)" }}>
                Driver Roster
              </h2>
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
                Licenced transport personnel
              </p>
            </div>
            <Link href="/drivers" className="gc-btn-secondary" style={{ padding: "6px 12px", fontSize: "13px" }}>
              Manage
            </Link>
          </div>

          {loading ? (
            <p style={{ color: "var(--color-text-muted)", padding: "20px 0" }}>Loading roster...</p>
          ) : drivers.length === 0 ? (
            <div style={{ padding: "32px", textAlign: "center", color: "var(--color-text-muted)" }}>
              No drivers found.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {drivers.slice(0, 5).map((driver) => (
                <div
                  key={driver.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 14px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "var(--color-surface)",
                    border: "1px solid var(--color-border-subtle)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      backgroundColor: "var(--color-surface-elevated)",
                      color: "var(--color-text-primary)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "13px",
                      fontWeight: "700",
                    }}>
                      {driver.full_name.charAt(0)}
                    </div>
                    <div>
                      <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--color-text-primary)" }}>
                        {driver.full_name}
                      </div>
                      <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                        {driver.role.toUpperCase()}
                      </div>
                    </div>
                  </div>

                  <span className={`gc-badge ${driver.status === "active" ? "gc-badge-success" : "gc-badge-neutral"}`}>
                    {driver.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
