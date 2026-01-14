import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Incident {
    id: number;
    monitor_name: string;
    url: string;
    code: number;
    reaason: string;
    created_at: string;
}

export interface DashboardStats {
    total: number;
    active: number;
    up: number;
    down: number;
    avg_latency: number;
    recent_failures: Incident[];
}

export const useDashboardStats = () => {
    return useQuery({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            const { data } = await api.get<DashboardStats>('/monitors/dashboard_stats');
            return data;
        },
        refetchInterval: 5000, // Auto-refresh every 5s
    })
}
