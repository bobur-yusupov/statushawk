import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navidate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await api.post("/accounts/login", {
                email,
                password
            });

            const token = response.data.data?.token || response.data.token || response.data.key;

            login(token);
            navidate("/");
        } catch (err) {
            setError("Invalid credentials, Please try again.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-100 p-4">
            <Card className="w-full max-w-sm shadow-xl">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold">StatusHawk</CardTitle>
                    <CardDescription>Enter your credentials to access the dashboard</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="admin@admin.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                        {error && (
                            <div className="flex items-center">
                                <AlertCircle className="h-4 w-4" />
                                {error}
                            </div>
                        )}

                        <Button 
                            type="submit" 
                            className="w-full bg-zinc-700 text-white hover:bg-zinc-900" 
                            disabled={loading}>
                            {loading ? "Signing in..." : "Sign In"}
                        </Button>
                            <div className="text-center text-sm text-zinc-500 mt-4">
                            Don't have an account?{" "}
                            <Link to="/register" className="text-blue-600 hover:underline">
                                Sign up
                            </Link>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}