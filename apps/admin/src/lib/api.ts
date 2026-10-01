/**
 * Greencore Admin Dashboard — API Client
 * Connects to Railway production backend: https://greencore-production.up.railway.app
 */

import type {
  LoginRequest,
  LoginResponse,
  RefreshRequest,
  RefreshResponse,
  InviteDriverRequest,
  InviteDriverResponse,
  Driver,
  DriverListResponse,
  DriverCreateRequest,
  DriverUpdateRequest,
  DriverDeactivateRequest,
  DriverDeactivateResponse,
  RouteSummary,
  RouteDetail,
  Drop,
  DropCreateRequest,
  DropUpdateRequest,
  DropMoveRequest,
  DropMoveResponse,
  RouteImportPreviewResponse,
  RouteImportCommitRequest,
  RouteImportCommitResponse,
  AllocationOverviewResponse,
  AllocationConfirmRequest,
  AllocationConfirmResponse,
} from "@greencore/shared-types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "https://greencore-production.up.railway.app";

const TOKEN_KEY = "greencore_access_token";
const REFRESH_TOKEN_KEY = "greencore_refresh_token";
const USER_KEY = "greencore_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredTokens(accessToken: string, refreshToken?: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function clearStoredTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${path}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && typeof window !== "undefined") {
      // Unauthorized — clear token
      clearStoredTokens();
    }

    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = { detail: response.statusText };
      }
      const message =
        errorBody?.detail ||
        (Array.isArray(errorBody?.detail)
          ? errorBody.detail.map((e: any) => e.msg || e.message).join(", ")
          : null) ||
        `Request failed with status ${response.status}`;
      throw new ApiError(message, response.status, errorBody);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err?.message || "Network request failed", 0, err);
  }
}

export const api = {
  // Meta Endpoints
  meta: {
    getHealth: () => request<{ status: string; environment: string }>("/health"),
    getInfo: () => request<any>("/"),
  },

  // Auth Endpoints (Section 14.1)
  auth: {
    login: (data: LoginRequest) =>
      request<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    refresh: (data: RefreshRequest) =>
      request<RefreshResponse>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    inviteDriver: (data: InviteDriverRequest) =>
      request<InviteDriverResponse>("/auth/invite", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Driver Endpoints (Section 14.2)
  drivers: {
    list: (params?: { page?: number; page_size?: number; status?: string; role?: string }) => {
      const search = new URLSearchParams();
      if (params?.page) search.set("page", params.page.toString());
      if (params?.page_size) search.set("page_size", params.page_size.toString());
      if (params?.status) search.set("status", params.status);
      if (params?.role) search.set("role", params.role);
      const query = search.toString() ? `?${search.toString()}` : "";
      return request<DriverListResponse>(`/drivers${query}`);
    },
    get: (id: string) => request<Driver>(`/drivers/${id}`),
    create: (data: DriverCreateRequest) =>
      request<Driver>("/drivers", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: DriverUpdateRequest) =>
      request<Driver>(`/drivers/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    deactivate: (id: string, data: DriverDeactivateRequest) =>
      request<DriverDeactivateResponse>(`/drivers/${id}/deactivate`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Route & Drop Endpoints (Section 14.3)
  routes: {
    list: (params?: { page?: number; page_size?: number; status?: string }) => {
      const search = new URLSearchParams();
      if (params?.page) search.set("page", params.page.toString());
      if (params?.page_size) search.set("page_size", params.page_size.toString());
      if (params?.status) search.set("status", params.status);
      const query = search.toString() ? `?${search.toString()}` : "";
      return request<{ data: RouteSummary[]; total: number }>(`/routes${query}`);
    },
    get: (id: string) => request<RouteDetail>(`/routes/${id}`),
    create: (data: { route_name: string; depot_id?: string | null; max_drops?: number | null }) =>
      request<RouteDetail>("/routes", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    createDrop: (routeId: string, data: DropCreateRequest) =>
      request<Drop>(`/routes/${routeId}/drops`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    updateDrop: (routeId: string, dropId: string, data: DropUpdateRequest) =>
      request<Drop>(`/routes/${routeId}/drops/${dropId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    moveDrop: (dropId: string, data: DropMoveRequest) =>
      request<DropMoveResponse>(`/routes/drops/${dropId}/move`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    importPreview: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request<RouteImportPreviewResponse>("/routes/import/preview", {
        method: "POST",
        body: formData,
      });
    },
    importCommit: (data: RouteImportCommitRequest) =>
      request<RouteImportCommitResponse>("/routes/import/commit", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Allocation Endpoints (Section 14.4)
  allocations: {
    getOverview: (date: string) =>
      request<AllocationOverviewResponse>(`/allocations?date=${encodeURIComponent(date)}`),
    confirm: (data: AllocationConfirmRequest) =>
      request<AllocationConfirmResponse>("/allocations/confirm", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};
