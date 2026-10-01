"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import type {
  RouteImportPreviewResponse,
  RouteImportCommitResponse,
} from "@greencore/shared-types";

const TARGET_FIELDS = [
  { key: "customer_name", label: "Customer Name *", required: true },
  { key: "postcode", label: "Postcode *", required: true },
  { key: "account_number", label: "Account Number", required: false },
  { key: "address", label: "Street Address", required: false },
  { key: "route_name", label: "Route Name Column", required: false },
  { key: "sequence", label: "Sequence / Drop Order", required: false },
  { key: "delivery_instructions", label: "Delivery Instructions", required: false },
];

export default function RouteImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Wizard Steps: 1 = upload, 2 = column mapping, 3 = results
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [preview, setPreview] = useState<RouteImportPreviewResponse | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [defaultRouteName, setDefaultRouteName] = useState("");
  const [commitResult, setCommitResult] = useState<RouteImportCommitResponse | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadPreview = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const res = await api.routes.importPreview(file);
      setPreview(res);

      // Auto-match common column header names
      const initialMap: Record<string, string> = {};
      TARGET_FIELDS.forEach((tf) => {
        const match = res.detected_columns.find(
          (col) =>
            col.toLowerCase().replace(/[\s_-]/g, "") ===
            tf.key.toLowerCase().replace(/[\s_-]/g, "")
        );
        if (match) {
          initialMap[tf.key] = match;
        }
      });
      setColumnMapping(initialMap);
      setStep(2);
    } catch (err: any) {
      setError(err?.message || "Failed to parse CSV file");
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;
    setLoading(true);
    setError(null);

    try {
      const res = await api.routes.importCommit({
        import_id: preview.import_id,
        column_mapping: columnMapping,
        default_route_name: defaultRouteName || undefined,
      });
      setCommitResult(res);
      setStep(3);
    } catch (err: any) {
      setError(err?.message || "Failed to commit route import");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "1000px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: "800", color: "var(--color-text-primary)", letterSpacing: "-0.02em" }}>
          Route Card CSV / Excel Import
        </h1>
        <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
          Upload legacy route cards, map columns, and ingest drops with partial-success tolerance (Section 14.3 & 17.6)
        </p>
      </div>

      {/* Progress Indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {[
          { num: 1, label: "1. Upload File" },
          { num: 2, label: "2. Column Mapping" },
          { num: 3, label: "3. Commit & Verification" },
        ].map((s) => {
          const isCurrent = step === s.num;
          const isDone = step > s.num;
          return (
            <div
              key={s.num}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                borderRadius: "var(--radius-full)",
                backgroundColor: isCurrent
                  ? "var(--color-surface-elevated)"
                  : isDone
                  ? "var(--color-status-success-bg)"
                  : "var(--color-surface)",
                border: `1px solid ${
                  isCurrent
                    ? "var(--color-border-focus)"
                    : isDone
                    ? "var(--color-status-success-border)"
                    : "var(--color-border)"
                }`,
                fontSize: "13px",
                fontWeight: isCurrent || isDone ? 700 : 500,
                color: isDone
                  ? "var(--color-status-success)"
                  : isCurrent
                  ? "#FFFFFF"
                  : "var(--color-text-muted)",
              }}
            >
              {s.label}
            </div>
          );
        })}
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md)",
            backgroundColor: "var(--color-status-danger-bg)",
            border: "1px solid var(--color-status-danger-border)",
            color: "var(--color-status-danger)",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* STEP 1: Upload File */}
      {step === 1 && (
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "32px" }}>
          <div
            style={{
              border: "2px dashed var(--color-border)",
              borderRadius: "var(--radius-lg)",
              padding: "48px 24px",
              textAlign: "center",
              backgroundColor: "rgba(255, 255, 255, 0.01)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "12px",
                backgroundColor: "var(--color-surface-elevated)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--color-primary-bright)",
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </div>
            <div>
              <p style={{ fontSize: "16px", fontWeight: "600", color: "var(--color-text-primary)" }}>
                Drag and drop your route CSV here, or browse
              </p>
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
                Supports standard comma-separated delivery lists with account, address, and customer fields
              </p>
            </div>

            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              style={{ marginTop: "12px" }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={handleUploadPreview}
              disabled={!file || loading}
              className="gc-btn-primary"
            >
              {loading ? "Analyzing CSV..." : "Continue to Column Mapping →"}
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Column Mapping */}
      {step === 2 && preview && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <h3 style={{ fontSize: "18px", fontWeight: "700", color: "var(--color-text-primary)" }}>
                  Map CSV Columns to System Fields
                </h3>
                <p style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
                  Detected {preview.row_count} rows across {preview.detected_columns.length} columns
                </p>
              </div>
              <span className="gc-badge gc-badge-info">
                Import ID: {preview.import_id.slice(0, 8)}...
              </span>
            </div>

            <div>
              <label className="gc-label">Default Route Name (used if CSV has no route column)</label>
              <input
                type="text"
                className="gc-input"
                placeholder="e.g. IMPORTED NORTH LONDON"
                value={defaultRouteName}
                onChange={(e) => setDefaultRouteName(e.target.value)}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "10px" }}>
              {TARGET_FIELDS.map((field) => (
                <div key={field.key}>
                  <label className="gc-label">{field.label}</label>
                  <select
                    className="gc-input"
                    value={columnMapping[field.key] || ""}
                    onChange={(e) =>
                      setColumnMapping({
                        ...columnMapping,
                        [field.key]: e.target.value,
                      })
                    }
                  >
                    <option value="">— Select Column from CSV —</option>
                    {preview.detected_columns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "16px" }}>
              <button onClick={() => setStep(1)} className="gc-btn-secondary">
                ← Back
              </button>
              <button
                onClick={handleCommit}
                disabled={loading || !columnMapping.customer_name || !columnMapping.postcode}
                className="gc-btn-primary"
              >
                {loading ? "Importing Rows..." : `Commit Import (${preview.row_count} Rows)`}
              </button>
            </div>
          </div>

          {/* Sample Rows Preview */}
          <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "700", color: "var(--color-text-primary)" }}>
              Sample Data Preview (First 3 Rows)
            </h4>
            <div className="gc-table-container">
              <table className="gc-table" style={{ fontSize: "12px" }}>
                <thead>
                  <tr>
                    {preview.detected_columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.map((row, idx) => (
                    <tr key={idx}>
                      {preview.detected_columns.map((col) => (
                        <td key={col}>{row[col] || "—"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Results & Acceptance Verification (Section 17.6) */}
      {step === 3 && commitResult && (
        <div className="gc-card" style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "32px" }}>
          <div>
            <h2 style={{ fontSize: "22px", fontWeight: "800", color: "var(--color-text-primary)" }}>
              Import Results Summary
            </h2>
            <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
              Section 17.6 Compliance: Partial-success processing completed without dropping valid drops.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div
              style={{
                padding: "20px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-status-success-bg)",
                border: "1px solid var(--color-status-success-border)",
              }}
            >
              <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--color-status-success)" }}>
                Successfully Imported
              </div>
              <div style={{ fontSize: "36px", fontWeight: "800", color: "var(--color-status-success)" }}>
                {commitResult.imported}
              </div>
              <div style={{ fontSize: "12px", color: "var(--color-text-primary)", marginTop: "4px" }}>
                Drops integrated into route portfolio
              </div>
            </div>

            <div
              style={{
                padding: "20px",
                borderRadius: "var(--radius-md)",
                backgroundColor: commitResult.failed > 0 ? "var(--color-status-danger-bg)" : "var(--color-surface)",
                border: `1px solid ${commitResult.failed > 0 ? "var(--color-status-danger-border)" : "var(--color-border)"}`,
              }}
            >
              <div style={{ fontSize: "13px", fontWeight: "600", color: commitResult.failed > 0 ? "var(--color-status-danger)" : "var(--color-text-muted)" }}>
                Failed Rows (Skipped)
              </div>
              <div style={{ fontSize: "36px", fontWeight: "800", color: commitResult.failed > 0 ? "var(--color-status-danger)" : "var(--color-text-muted)" }}>
                {commitResult.failed}
              </div>
              <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
                {commitResult.failed === 0 ? "No row validation errors" : "Itemized error details below"}
              </div>
            </div>
          </div>

          {commitResult.errors && commitResult.errors.length > 0 && (
            <div>
              <h4 style={{ fontSize: "15px", fontWeight: "700", color: "var(--color-status-danger)", marginBottom: "8px" }}>
                Row Failure Details
              </h4>
              <div className="gc-table-container">
                <table className="gc-table">
                  <thead>
                    <tr>
                      <th style={{ width: "100px" }}>Row #</th>
                      <th>Error Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {commitResult.errors.map((err, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 700 }}>Row {err.row}</td>
                        <td style={{ color: "var(--color-status-danger)" }}>{err.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "12px" }}>
            <button
              onClick={() => {
                setFile(null);
                setPreview(null);
                setCommitResult(null);
                setStep(1);
              }}
              className="gc-btn-secondary"
            >
              Import Another File
            </button>
            <a href="/routes" className="gc-btn-primary">
              View Route Portfolio →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
