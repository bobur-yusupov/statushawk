import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { deleteMonitor, getMonitors, monitorKeys, toggleMonitor } from "./api";
import { AddMonitorDialog } from "./AddMonitorDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Globe, Pause, Play, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function MonitorsPage() {
    const queryClient = useQueryClient();

    const { data: monitors, isLoading } = useQuery({
        queryKey: monitorKeys.all,
        queryFn: getMonitors,
        refetchInterval: 5000
    });

    const toggleMutation = useMutation({
        mutationFn: ({ id, active }: { id: number; active: boolean }) => toggleMonitor(id, active),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: monitorKeys.all }),
    });

    const deleteMutation = useMutation({
        mutationFn: deleteMonitor,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: monitorKeys.all }),
    });

    if (isLoading) return <div className="p-8">Loading monitors...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Monitors</h2>
                    <p className="text-zinc-500">Manage your endpoints and configurations.</p>
                </div>
                <AddMonitorDialog />
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {monitors?.map((monitor) => (
                    <Card key={monitor.id} className="transition-all hover:shadow-md">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle>
                                <Link to={`/monitors/${monitor.id}`} className="hover:underline cursor-pointer flex items-center gap-2">
                                    {monitor.monitor_type === 'HTTP' ? <Globe className="w-4 h-4 text-blue-500" /> : <Activity className="w-4 h-4" />}
                                    {monitor.name}
                                </Link>
                            </CardTitle>

                            <Badge variant="outline" className={
                                monitor.status === "UP"
                                    ? "bg-green-50 text-red-700 border-red-200"
                                    : monitor.status === "DOWN"
                                        ? "bg-red-50 text-red-700 border-red-200"
                                        : "bg-zinc-100"
                            }>
                                {monitor.status}
                            </Badge>
                        </CardHeader>

                        <CardContent className="pt-4">
                            <div className="text-xl font-bold truncate" title={monitor.url}>
                                {monitor.url}
                            </div>

                            <div className="flex flex-col gap-1 mt-2 text-xs text-zinc-500">
                                <div className="flex justify-between">
                                    <span>Interval:</span>
                                    <span className="font-mono">{monitor.interval}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Added:</span>
                                    <span>{formatDistanceToNow(new Date(monitor.created_at), { addSuffix: true })}</span>
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 mt-6 border-t pt-4">
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    className={monitor.is_active ? "text-amber-600 hover:text-amber-700" : "text-emerald-600 hover:text-green-50"}
                                >
                                    {monitor.is_active ? (
                                        <><Pause className="w-4 h-4 mr-2" /> Pause</>
                                    ) : (
                                        <><Play className="w-4 h-4 mr-2" /> Resume</>
                                    )}
                                </Button>
                                <Button 
                                    size="sm" 
                                    variant="ghost"
                                    className="text-zinc-400 hover:text-red-600 hover:bg-red-50"
                                    onClick={() => {
                                        if(confirm("Are you sure you want to delete this monitor?")) deleteMutation.mutate(monitor.id);
                                    }}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}