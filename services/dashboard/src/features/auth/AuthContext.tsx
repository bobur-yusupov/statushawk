import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { api } from "@/lib/api";

interface AuthContextType {
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState<string | null>(() => {
        const storedToken = localStorage.getItem("token");
        if (storedToken) {
            api.defaults.headers.common["Authorization"] = `Token ${storedToken}`;
        }
        return storedToken;
    });

    useEffect(() => {
        const handleStorageChange = () => {
            const currentToken = localStorage.getItem("token");
            if (currentToken !== token) {
                setToken(currentToken);
            }
        };

        window.addEventListener("storage", handleStorageChange);
        return () => window.removeEventListener("storage", handleStorageChange);
    }, [token]);

    useEffect(() => {
        if (token) {
            localStorage.setItem("token", token);
            api.defaults.headers.common["Authorization"] = `Token ${token}`;
        } else {
            localStorage.removeItem("token");
            delete api.defaults.headers.common["Authorization"];
        }
    }, [token]);

    const login = (newToken: string) => setToken(newToken);
    const logout = () => setToken(null);

    return (
        <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within an AuthProvider");
    return context;
}
