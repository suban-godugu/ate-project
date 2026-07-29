"use client";

import { useEffect, useState } from "react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ALERT_MODULES,
  ALERT_SEVERITIES,
  ALERT_STATUSES,
  type AlertCreatePayload,
  type AlertUpdatePayload,
} from "@/lib/api/alerts";
import { useAlertMutations } from "@/hooks/useAlertMutations";
import type { RecentAlertRow } from "@/types/alerts";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function optionalUuid(value: string): string | null {
  const v = value.trim();
  return v && UUID_RE.test(v) ? v : null;
}

export interface AlertFormValues {
  title: string;
  description: string;
  severity: string;
  sourceModule: string;
  status: string;
  lotId: string;
  waferId: string;
}

const emptyForm: AlertFormValues = {
  title: "",
  description: "",
  severity: "Medium",
  sourceModule: "Scan Chain",
  status: "Open",
  lotId: "",
  waferId: "",
};

function toForm(alert?: RecentAlertRow | null): AlertFormValues {
  if (!alert) return emptyForm;
  return {
    title: alert.description?.slice(0, 80) ?? "",
    description: alert.description ?? "",
    severity: alert.severity,
    sourceModule: alert.sourceModule,
    status: alert.status,
    lotId: alert.lotId ?? "",
    waferId: alert.waferId ?? "",
  };
}

interface AlertFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  alert?: RecentAlertRow | null;
}

export function AlertFormDialog({ open, onOpenChange, mode, alert }: AlertFormDialogProps) {
  const { createAlert, updateAlert } = useAlertMutations();
  const [form, setForm] = useState<AlertFormValues>(emptyForm);
  const [error, setError] = useState<string | null>(null);

  const pending = createAlert.isPending || updateAlert.isPending;

  useEffect(() => {
    if (open) {
      setForm(toForm(alert));
      setError(null);
    }
  }, [open, alert]);

  const handleSubmit = async () => {
    setError(null);
    if (!form.description.trim()) {
      setError("Description is required.");
      return;
    }

    try {
      if (mode === "create") {
        const body: AlertCreatePayload = {
          source_module: form.sourceModule,
          severity: form.severity,
          status: form.status,
          title: form.title.trim() || form.description.trim().slice(0, 120),
          description: form.description.trim(),
          lot_id: optionalUuid(form.lotId),
          wafer_id: optionalUuid(form.waferId),
        };
        await createAlert.mutateAsync(body);
      } else if (alert) {
        const body: AlertUpdatePayload = {
          severity: form.severity,
          status: form.status,
          title: form.title.trim() || form.description.trim().slice(0, 120),
          description: form.description.trim(),
        };
        await updateAlert.mutateAsync({ id: alert.id, body });
      }
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !pending && onOpenChange(v)}>
      <DialogContent className="max-w-lg" onClose={() => !pending && onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "Create Alert" : "Edit Alert"}</DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a new operational alert. It will appear in the alerts list immediately."
              : "Update alert details. Changes sync to the dashboard on save."}
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="alert-title">Title</Label>
            <Input
              id="alert-title"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Short summary"
              disabled={pending}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="alert-description">Description</Label>
            <textarea
              id="alert-description"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Describe the issue and recommended action"
              rows={4}
              disabled={pending}
              className="w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm text-white outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select
                value={form.severity}
                onValueChange={(v) => v && setForm((f) => ({ ...f, severity: v }))}
                disabled={pending}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALERT_SEVERITIES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Source module</Label>
              <Select
                value={form.sourceModule}
                onValueChange={(v) => v && setForm((f) => ({ ...f, sourceModule: v }))}
                disabled={pending || mode === "edit"}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALERT_MODULES.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => v && setForm((f) => ({ ...f, status: v }))}
                disabled={pending}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALERT_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {mode === "create" && (
              <div className="space-y-2">
                <Label htmlFor="alert-lot">Lot ID (optional)</Label>
                <Input
                  id="alert-lot"
                  value={form.lotId}
                  onChange={(e) => setForm((f) => ({ ...f, lotId: e.target.value }))}
                  placeholder="Lot UUID (optional)"
                  disabled={pending}
                />
              </div>
            )}
          </div>
          {mode === "create" && (
            <div className="space-y-2">
              <Label htmlFor="alert-wafer">Wafer ID (optional)</Label>
              <Input
                id="alert-wafer"
                value={form.waferId}
                onChange={(e) => setForm((f) => ({ ...f, waferId: e.target.value }))}
                placeholder="Wafer UUID (optional)"
                disabled={pending}
              />
            </div>
          )}
          {error && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={pending} className="bg-[#7C3AED] hover:bg-[#6D28D9]">
            {pending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "create" ? "Create Alert" : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
