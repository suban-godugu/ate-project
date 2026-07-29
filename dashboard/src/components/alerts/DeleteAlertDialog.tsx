"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAlertMutations } from "@/hooks/useAlertMutations";
import type { RecentAlertRow } from "@/types/alerts";

interface DeleteAlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  alert: RecentAlertRow | null;
}

export function DeleteAlertDialog({ open, onOpenChange, alert }: DeleteAlertDialogProps) {
  const { deleteAlert } = useAlertMutations();
  const pending = deleteAlert.isPending;
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!alert) return;
    setError(null);
    try {
      await deleteAlert.mutateAsync(alert.id);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !pending && onOpenChange(v)}>
      <DialogContent className="max-w-md" onClose={() => !pending && onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Delete Alert</DialogTitle>
          <DialogDescription>
            This permanently removes the alert from the system. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          {alert && (
            <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 text-sm text-slate-300">
              <p className="font-mono text-xs text-slate-500">{alert.id}</p>
              <p className="mt-2 font-medium text-white">{alert.description}</p>
            </div>
          )}
          {error && (
            <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={pending}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={pending}>
            {pending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Delete Alert
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
