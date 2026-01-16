import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Send, CheckCircle2, Trash2 } from "lucide-react";

export default function TelegramConnect() {
    const [loading, setLoading] = useState(true);
    const [telegramChannel, setTelegramChannel] = useState<any>(null);
    const [connectLink, setConnectLink] = useState("");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);

            const channelsRes = await api.get("/notifications/channels/");
            const existing = channelsRes.data.find((c: any) => c.provider === "telegram");
            setTelegramChannel(existing);

            if (!existing) {
                const linkRes = await api.get("/notifications/telegram-link/")
                setConnectLink(linkRes.data.link);
            }
        } catch (error) {
            console.error("Failed to load telegram settings", error);
        } finally {
            setLoading(false);
        }
    }

    const handleDelete = async () => {
        if (!telegramChannel) return;
        try {
            await api.delete(`/notifications/channels/${telegramChannel.id}/`);
            setTelegramChannel(null);
            fetchData();
        } catch (error) {
            console.error("Failed to remove channel", error);
        }
    }

    if (loading) {
        return (
            <Card>
                <CardContent className="pt-6 flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin">Loading Telegram status...</Loader2>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                {/* Telegram Icon */}
                <Send className="h-5 w-5 text-sky-500" />
                <CardTitle>Telegram Notifications</CardTitle>
            </div>
            {telegramChannel && (
                <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-100">
                <CheckCircle2 className="h-3 w-3 mr-1" /> Active
                </Badge>
            )}
            </div>
            <CardDescription>
            Get instant alerts on your phone when a monitor goes down.
            </CardDescription>
        </CardHeader>

        <CardContent>
            {telegramChannel ? (
            <div className="flex items-center justify-between bg-muted/50 p-3 rounded-md">
                <div className="text-sm">
                <p className="font-medium">Connected as {telegramChannel.name}</p>
                <p className="text-xs text-muted-foreground">
                    Connected on {new Date(telegramChannel.created_at).toLocaleDateString()}
                </p>
                </div>
                {/* Optional Disconnect Button */}
                <Button variant="ghost" size="sm" onClick={handleDelete} className="text-red-500 hover:text-red-600 hover:bg-red-50">
                <Trash2 className="h-4 w-4" />
                </Button>
            </div>
            ) : (
            <div className="space-y-3">
                {/* The Magic Button */}
                <Button asChild className="w-full bg-sky-500 hover:bg-sky-600 text-white">
                <a href={connectLink} target="_blank" rel="noopener noreferrer">
                    <Send className="mr-2 h-4 w-4" /> Connect Telegram
                </a>
                </Button>
                <p className="text-xs text-center text-muted-foreground">
                Clicking this will open Telegram. Tap <strong>Start</strong> to finish setup.
                </p>
            </div>
            )}
        </CardContent>
        </Card>
    );
}
