import { api } from "@/lib/api";

export interface Monitor {
  id: number;
  name: string;
  url: string;
  interval: number;
  monitor_type: string;
  status: "UP" | "DOWN" | "UNKNOWN"; 
  is_active: boolean;
  created_at: string;
  last_checked_at?: string | null; 
}

export interface MonitorHistory {
    id: number;
    response_time_ms: number;
    status_code: number;
    is_up: boolean;
    created_at: string;
}

export interface MonitorStats {
    period: string;
    uptime_percentage: number;
    avg_response_time: number;
    total_checks: number;
    down_count: number;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const monitorKeys = {
  all: ['monitors'] as const,
};

export const getMonitors = async () => {
  const { data } = await api.get<PaginatedResponse<Monitor>>('/monitors/');
  return data.results; 
};

export const createMonitor = async (payload: { name: string; url: string; interval: number; monitor_type: string }) => {
    const { data } = await api.post<Monitor>('/monitors/', payload);
    return data;
};

export const deleteMonitor = async (id: number) => {
    await api.delete(`/monitors/${id}/`);
};
  
export const toggleMonitor = async (id: number, isActive: boolean) => {
    const { data } = await api.patch<Monitor>(`/monitors/${id}/`, { is_active: isActive });
    return data;
};

export const getMonitor = async (id: number) => {
    const { data } = await api.get<Monitor>(`/monitors/${id}`);
    return data;
}

export const getMonitorStats = async (id: number, period = '24h') => {
    const { data } = await api.get<MonitorStats>(`/monitors/${id}/stats/?period=${period}`);
    return data;
}

export const getMonitorHistory = async (id: number)=> {
    const { data } = await api.get<PaginatedResponse<MonitorHistory>>(`/monitors/${id}/history/`);
    return data.results;
}
