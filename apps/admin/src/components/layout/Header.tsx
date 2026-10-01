"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/api";

export function Header() {
  const { user, logout, apiConnected, checkHealth } = useAuth();

  return (
    <header style={{
      height: "70px",
      backgroundColor: "var(--color-surface)",
      borderBottom: "1px solid var(--color-border)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 32px",
      position: "sticky",
      top: 0,
      zIndex: 40,
    }}>
      {/* Left: Environment Info */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "5px 12px",
          borderRadius: "var(--radius-full)",
          backgroundColor: apiConnected ? "var(--color-status-success-bg)" : "var(--color-status-danger-bg)",
          border: `1px solid ${apiConnected ? "var(--color-status-success-border)" : "var(--color-status-danger-border)"}`,
          fontSize: "12px",
          fontWeight: 600,
          color: apiConnected ? "var(--color-status-success)" : "var(--color-status-danger)",
          cursor: "pointer",
        }}
        onClick={() => checkHealth()}
        title="Click to re-check API health"
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: apiConnected ? "var(--color-status-success)" : "var(--color-status-danger)",
            }}
          />
          {apiConnected === null ? "Connecting..." : apiConnected ? "Railway API Online" : "API Offline"}
        </div>

        <span style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
          {API_BASE_URL}
        </span>
      </div>

      {/* Right: User session & Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        {user ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: "34px",
                height: "34px",
                borderRadius: "50%",
                background: "linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
                fontWeight: 700,
                fontSize: "14px",
                border: "1px solid var(--color-border)",
              }}>
                {user.full_name?.charAt(0) || "A"}
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text-primary)" }}>
                  {user.full_name}
                </span>
                <span style={{
                  fontSize: "11px",
                  color: "var(--color-primary-bright)",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                }}>
                  {"permission_role" in user ? user.permission_role.replace("_", " ") : "Driver"}
                </span>
              </div>
            </div>

            <button
              onClick={logout}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                fontSize: "12px",
                fontWeight: 500,
                color: "var(--color-text-secondary)",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-border)",
                backgroundColor: "transparent",
                transition: "all var(--transition-fast)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--color-status-danger)";
                e.currentTarget.style.borderColor = "var(--color-status-danger-border)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--color-text-secondary)";
                e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Sign out
            </button>
          </>
        ) : null}
      </div>
    </header>
  );
}
