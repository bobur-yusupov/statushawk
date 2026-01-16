import TelegramConnect from "./components/TelegramConnect";

export default function SettingsPage() {
    return (
        <div className="max-w-2xl mx-auto p-6 space-y-6">
            <h1 className="text-3xl font-bold">Notification Channels</h1>
            <TelegramConnect />
        </div>
    )
}