import { useState } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { createMonitor, monitorKeys } from "./api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";

export function AddMonitorDialog() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [interval, setInterval] = useState("30"); // Default 30s
  
  const queryClient = useQueryClient();

  // Mutation to handle API call
  const mutation = useMutation({
    mutationFn: createMonitor,
    onSuccess: () => {
      // 1. Close modal
      setOpen(false);
      // 2. Reset form
      setName(""); setUrl("");
      // 3. Refresh the list automatically
      queryClient.invalidateQueries({ queryKey: monitorKeys.all });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({ 
      name, 
      url, 
      interval: parseInt(interval),
      monitor_type: "HTTP"
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-zinc-700 text-white hover:bg-zinc-900">
          <Plus className="w-4 h-4 mr-2" /> Add Monitor
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-white sm:max-w-[425px] z-50">
        <DialogHeader>
          <DialogTitle>Add New Monitor</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input 
              id="name" 
              placeholder="e.g. Google Production" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="url">URL to Check</Label>
            <Input 
              id="url" 
              placeholder="https://..." 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              type="url"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="interval">Interval (seconds)</Label>
            <Input 
              id="interval" 
              type="number" 
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              min="10"
              required
            />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create Monitor"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
