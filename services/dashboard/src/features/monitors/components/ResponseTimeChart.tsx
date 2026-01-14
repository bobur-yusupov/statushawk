import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { format } from 'date-fns';
import type { MonitorHistory } from '../api';

interface Props {
  data: MonitorHistory[];
}

export function ResponseTimeChart({ data }: Props) {
  // Reverse data so it reads left-to-right (Oldest -> Newest)
  const chartData = [...data].reverse().map(item => ({
    ...item,
    // Use 0 or a fixed height for "Down" points to make them visible
    value: item.is_up ? item.response_time_ms : 0, 
    date: new Date(item.created_at),
  }));

  if (data.length === 0) {
    return <div className="h-[300px] flex items-center justify-center text-zinc-400">No data available</div>;
  }

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis 
            dataKey="date" 
            tickFormatter={(date) => format(date, 'HH:mm')}
            stroke="#a1a1aa"
            fontSize={12}
            minTickGap={30}
          />
          <YAxis 
            stroke="#a1a1aa" 
            fontSize={12}
            unit="ms"
          />
          <Tooltip 
            labelFormatter={(date) => format(date, 'MMM dd, HH:mm:ss')}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          {/* Main Line */}
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#2563eb" 
            fillOpacity={1} 
            fill="url(#colorLatency)" 
            strokeWidth={2}
          />
          {/* Red lines for Downtime */}
          {chartData.filter(d => !d.is_up).map((d, i) => (
             <ReferenceLine key={i} x={d.created_at} stroke="red" label="DOWN" />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
