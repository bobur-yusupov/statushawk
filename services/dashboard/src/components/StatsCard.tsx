import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LucideIcon } from "lucide-react";

interface StatsCardProp {
    title: string;
    value: string | number;
    description?: string;
    icon: LucideIcon;
    trend?: "up" | "down" | "neutral";
}

export function StatsCard({ title, value, description, icon: Icon, trend } : StatsCardProp) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                    {title}
                </CardTitle>
                <Icon className="h-4 w-4 text-zinc-500" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {description && (
                    <p className="text-xs text-zinc-500 mt-1">
                        {trend === "down" && <span className="text-red-500 mr-1">↓</span>}
                        {trend === "up" && <span className="text-green-500 mr-1">↑</span>}
                        {description}
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
