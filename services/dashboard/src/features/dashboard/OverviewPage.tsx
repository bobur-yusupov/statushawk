import { Activity, ArrowDown, ArrowUp, Globe, ServerCrash } from "lucide-react";
import { StatsCard } from "@/components/StatsCard";
import { Button } from "@/components/ui/button";
import { useDashboardStats } from "./useDashboardStats";

export default function OverviewPage() {
  const { data: stats, isLoading, error } = useDashboardStats();

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
          <p className="text-zinc-500 mt-2">
            Here is what's happening with your infrastructure today.
          </p>
        </div>
        <div className="flex gap-2">
            <Button>Add Monitor</Button>
        </div>
      </div>

      {/* STATS GRID */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard 
          title="Total Monitors" 
          value={stats?.total || 0} 
          icon={Globe} 
          description="+2 from last month"
          trend="up"
        />
        <StatsCard 
          title="Operational" 
          value={stats?.up || 0} 
          icon={ArrowUp} 
          description="Systems normal"
          trend="neutral"
        />
        <StatsCard 
          title="Downtime" 
          value={stats?.down || 0}
          icon={ServerCrash} 
          description="2 active incidents" 
          trend="down"
        />
        <StatsCard 
          title="Avg Latency" 
          value={`${stats?.avg_latency || 0}ms`}
          icon={Activity} 
          description="Global average"
          trend="neutral"
        />
      </div>

      {/* RECENT ACTIVITY SECTION */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        
        {/* Main Chart Area (Placeholder) */}
        <div className="col-span-4 rounded-xl border bg-card text-card-foreground shadow p-6">
            <h3 className="font-semibold mb-4">Response Time History</h3>
            <div className="h-[200px] flex items-center justify-center border-dashed border-2 border-zinc-200 rounded-lg text-zinc-400">
                Chart Component Coming Soon...
            </div>
        </div>

        {/* Recent Failures List */}
        <div className="col-span-3 rounded-xl border bg-card text-card-foreground shadow p-6">
            <h3 className="font-semibold mb-4 text-red-600 flex items-center gap-2">
                <ServerCrash className="w-4 h-4" /> Recent Incidents
            </h3>
            <div className="space-y-4">
                {[1, 2].map((i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100">
                        <div className="space-y-1">
                            <p className="text-sm font-medium leading-none text-red-900">API Gateway</p>
                            <p className="text-xs text-red-600">500 Internal Server Error</p>
                        </div>
                        <div className="text-xs text-red-600 font-mono">2m ago</div>
                    </div>
                ))}
            </div>
        </div>
      </div>
    </div>
  );
}
