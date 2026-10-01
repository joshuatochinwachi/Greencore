"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";

const NAV_ITEMS = [
  {
    name: "Dashboard",
    href: "/",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="9" rx="1" />
        <rect x="14" y="3" width="7" height="5" rx="1" />
        <rect x="14" y="12" width="7" height="9" rx="1" />
        <rect x="3" y="16" width="7" height="5" rx="1" />
      </svg>
    ),
  },
  {
    name: "Drivers",
    href: "/drivers",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    name: "Routes & Drops",
    href: "/routes",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="19" r="3" />
        <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" />
        <circle cx="18" cy="5" r="3" />
      </svg>
    ),
  },
  {
    name: "Allocations",
    href: "/allocations",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
  },
  {
    name: "Route Import",
    href: "/import",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside style={{
      width: "260px",
      minHeight: "100vh",
      backgroundColor: "var(--color-surface)",
      borderRight: "1px solid var(--color-border)",
      display: "flex",
      flexDirection: "column",
      position: "fixed",
      top: 0,
      left: 0,
      bottom: 0,
      zIndex: 50,
    }}>
      {/* Brand Header */}
      <div style={{
        padding: "24px 20px",
        borderBottom: "1px solid var(--color-border-subtle)",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}>
        <div style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: "linear-gradient(135deg, #10B981, #1B5E3A)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 16px rgba(16, 185, 129, 0.35)",
        }}>
          <span style={{ fontSize: "20px", fontWeight: "800", color: "#FFFFFF" }}>G</span>
        </div>
        <div>
          <div style={{ fontSize: "16px", fontWeight: "700", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
            GREENCORE
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Operations Admin
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: "16px 12px", flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 14px",
                borderRadius: "var(--radius-md)",
                color: isActive ? "#FFFFFF" : "var(--color-text-secondary)",
                backgroundColor: isActive ? "var(--color-surface-elevated)" : "transparent",
                fontWeight: isActive ? 600 : 500,
                fontSize: "14px",
                transition: "all var(--transition-fast)",
                border: isActive ? "1px solid var(--color-border-focus)" : "1px solid transparent",
              }}
            >
              <span style={{ color: isActive ? "var(--color-primary-bright)" : "var(--color-text-muted)" }}>
                {item.icon}
              </span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer / API Links */}
      <div style={{
        padding: "16px",
        borderTop: "1px solid var(--color-border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        backgroundColor: "rgba(0, 0, 0, 0.2)",
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "12px",
          color: "var(--color-text-muted)",
        }}>
          <span>Backend</span>
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "5px",
            color: "var(--color-primary-bright)",
            fontWeight: 500,
          }}>
            <span className="gc-pulse-dot" /> Railway
          </span>
        </div>

        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            padding: "8px 12px",
            fontSize: "12px",
            fontWeight: 600,
            borderRadius: "var(--radius-sm)",
            backgroundColor: "var(--color-surface-elevated)",
            color: "var(--color-text-secondary)",
            border: "1px solid var(--color-border)",
            transition: "all var(--transition-fast)",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          Open Swagger Docs
        </a>
      </div>
    </aside>
  );
}
