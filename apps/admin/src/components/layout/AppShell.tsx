"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useAuth } from "@/context/AuthContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isLoading, token } = useAuth();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <main>{children}</main>;
  }

  if (isLoading || !token) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--color-bg-base)",
        color: "var(--color-text-secondary)",
        gap: "12px",
      }}>
        <div className="gc-pulse-dot" />
        <span>Authenticating Greencore Admin session...</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{
        flex: 1,
        marginLeft: "260px",
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
      }}>
        <Header />
        <main style={{
          flex: 1,
          padding: "32px",
          maxWidth: "1400px",
          width: "100%",
          margin: "0 auto",
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
