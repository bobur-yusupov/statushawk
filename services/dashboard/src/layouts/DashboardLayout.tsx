import { Outlet, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Activity, Settings, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export default function DashboardLayout() {
    const location = useLocation();

    const navItems = [
        {
            href: "/", 
            label: "Overview",
            icon: LayoutDashboard,
        },
        {
            href: "/monitors", 
            label: "Monitors",
            icon: Activity,
        },
        {
            href: "/settings", 
            label: "Settings",
            icon: Settings,
        }
    ];

    return (
        <div className="min-h-screen bg-zinc-50 flex">
            <aside className="hidden md:flex w-64 flex-col bg-white border-r border-zinc-200">
                <div className="p-6 botder-b border-zinc-100">
                    <h1 className="text-xl font-bold text-zinc-900 flex items-center gap-2">Statushawk</h1>
                </div>
                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                                    isActive 
                                        ? "bg-zinc-900 text-white" 
                                        : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                                }`}
                            >
                                <item.icon className="w-4 h-4" />
                                {item.label}
                            </Link>
                        )
                    })}
                </nav>
            </aside>

            <div className="flex-1 flex flex-col">
                <header className="md:hidden h-16 border-b bg-white flex items-center px-4">
                    <Sheet>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <Menu className="w-5 h-5" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="w-64 p-0">
                            <div className="p-6 font-bold">Menu</div>
                        </SheetContent>
                    </Sheet>
                    <span className="font-bold ml-4">StatusHawk</span>
                </header>
                <main className="flex-1 overflow-auto bg-zinc-50/50">
                    <div className="h-full p-8 max-w-8xl mx-auto w-full">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    )
}
