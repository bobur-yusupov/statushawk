import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle, XCircle, Clock } from "lucide-react";
import { getMonitor, getMonitorStats, getMonitorHistory } from "./api";
import { ResponseTimeChart } from "./components/ResponseTimeChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function MonitorDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const monitorId = parseInt(id || "0");

  // Fetch Monitor Info
  const { data: monitor } = useQuery({
    queryKey: ['monitor', monitorId],
    queryFn: () => getMonitor(monitorId),
  });

  // Fetch Stats (Uptime)
  const { data: stats } = useQuery({
    queryKey: ['monitor-stats', monitorId],
    queryFn: () => getMonitorStats(monitorId, '24h'),
    refetchInterval: 10000,
  });

  // Fetch History (Graph)
  const { data: history } = useQuery({
    queryKey: ['monitor-history', monitorId],
    queryFn: () => getMonitorHistory(monitorId),
    refetchInterval: 10000,
  });

  if (!monitor) return <div className="p-8">Loading...</div>;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/monitors')}>
            <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
                {monitor.name}
                <Badge variant={monitor.status === 'UP' ? 'default' : 'destructive'}>
                    {monitor.status}
                </Badge>
            </h2>
            <p className="text-zinc-500">{monitor.url}</p>
        </div>
      </div>

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response (24h)</CardTitle>
                <Clock className="w-4 h-4 text-zinc-500" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{stats?.avg_response_time || 0}ms</div>
            </CardContent>
        </Card>
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Uptime (24h)</CardTitle>
                <CheckCircle className="w-4 h-4 text-green-500" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-green-600">{stats?.uptime_percentage || 100}%</div>
            </CardContent>
        </Card>
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Downtime</CardTitle>
                <XCircle className="w-4 h-4 text-red-500" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-red-600">{stats?.down_count || 0} checks</div>
            </CardContent>
        </Card>
      </div>

      {/* CHART */}
      <Card className="p-6">
        <h3 className="font-semibold mb-6">Response Time History</h3>
        {history ? <ResponseTimeChart data={history} /> : <div>Loading Chart...</div>}
      </Card>
    </div>
  );
}