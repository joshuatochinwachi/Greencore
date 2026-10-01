"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/api";

export default function LoginPage() {
  const { login, apiConnected } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email, password });
    } catch (err: any) {
      setError(err?.message || "Invalid credentials or backend unreachable.");
    } finally {
      setLoading(false);
    }
  };

  const fillSeedAdmin = () => {
    setEmail("admin@test.greencore.app");
    setPassword("Password123!");
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background: `
          radial-gradient(ellipse at 50% 20%, rgba(27, 94, 58, 0.25) 0%, transparent 60%),
          radial-gradient(ellipse at 80% 80%, rgba(52, 211, 153, 0.08) 0%, transparent 50%),
          var(--color-bg-base)
        `,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "440px",
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-xl)",
          padding: "36px",
          boxShadow: "var(--shadow-lg)",
          backdropFilter: "blur(12px)",
        }}
      >
        {/* Header with Emblem */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, #10B981, #1B5E3A)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 24px rgba(16, 185, 129, 0.4)",
              marginBottom: "16px",
            }}
          >
            <span style={{ fontSize: "28px", fontWeight: "800", color: "#FFFFFF" }}>G</span>
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            Greencore Operations
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "6px" }}>
            Sign in to access driver allocations, live routes & drop management
          </p>
        </div>

        {/* Backend Connectivity Status */}
        <div
          style={{
            marginBottom: "24px",
            padding: "10px 14px",
            borderRadius: "var(--radius-md)",
            backgroundColor: apiConnected ? "var(--color-status-success-bg)" : "var(--color-status-danger-bg)",
            border: `1px solid ${apiConnected ? "var(--color-status-success-border)" : "var(--color-status-danger-border)"}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: apiConnected ? "var(--color-status-success)" : "var(--color-status-danger)",
              }}
            />
            <span style={{ color: apiConnected ? "var(--color-status-success)" : "var(--color-status-danger)", fontWeight: 600 }}>
              {apiConnected === null ? "Testing connection..." : apiConnected ? "Connected to Railway API" : "Backend Disconnected"}
            </span>
          </div>
          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "var(--color-primary-bright)", textDecoration: "underline", fontSize: "11px" }}
          >
            Docs ↗
          </a>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              marginBottom: "20px",
              padding: "12px 14px",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--color-status-danger-bg)",
              border: "1px solid var(--color-status-danger-border)",
              color: "var(--color-status-danger)",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div>
            <label className="gc-label" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              className="gc-input"
              placeholder="e.g. admin@test.greencore.app"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="gc-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="gc-input"
              placeholder="Enter your admin password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="gc-btn-primary"
            style={{ width: "100%", padding: "12px", marginTop: "6px", fontSize: "15px" }}
          >
            {loading ? "Authenticating..." : "Sign In to Operations"}
          </button>
        </form>

        {/* Seed helper — only visible in development environments */}
        {process.env.NODE_ENV !== "production" && (
          <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "1px solid var(--color-border-subtle)", textAlign: "center" }}>
            <p style={{ fontSize: "12px", color: "var(--color-text-muted)", marginBottom: "10px" }}>
              Local Development Mode
            </p>
            <button
              type="button"
              onClick={fillSeedAdmin}
              style={{
                padding: "8px 14px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--color-surface-elevated)",
                border: "1px solid var(--color-border)",
                color: "var(--color-primary-bright)",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all var(--transition-fast)",
              }}
            >
              Auto-fill Dev Super Admin (admin@test.greencore.app)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
