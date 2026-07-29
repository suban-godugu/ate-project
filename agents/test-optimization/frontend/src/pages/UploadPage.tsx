import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileJson, UploadCloud } from "lucide-react";
import { RecommendationView } from "@/components/RecommendationView";
import { Card, ErrorState, Spinner } from "@/components/ui";
import { api } from "@/lib/api";

export function UploadPage() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>("");
  const [dragging, setDragging] = useState(false);

  const upload = useMutation({
    mutationFn: (file: File) => api.upload(file, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  function handleFile(file: File | undefined) {
    if (!file) return;
    setFileName(file.name);
    upload.mutate(file);
  }

  return (
    <div className="space-y-4">
      <Card
        title="Upload Optimization Context"
        subtitle="Provide an OptimizationContext JSON to generate an enterprise test strategy"
      >
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            handleFile(event.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-10 text-center transition ${
            dragging
              ? "border-brand-500/60 bg-brand-600/10"
              : "border-white/12 bg-base-800/40 hover:border-brand-500/40"
          }`}
        >
          <UploadCloud className="h-7 w-7 text-brand-400" />
          <div>
            <p className="text-sm font-medium text-ink-100">
              Drop a JSON file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-ink-400">
              Accepts a bare OptimizationContext or an object with a <code>context</code> key
            </p>
          </div>
          {fileName && (
            <span className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-ink-200">
              <FileJson className="h-3 w-3" />
              {fileName}
            </span>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(event) => handleFile(event.target.files?.[0])}
          />
        </div>
      </Card>

      {upload.isPending && <Spinner label="Analyzing uploaded context…" />}

      {upload.isError && <ErrorState message={(upload.error as Error).message} />}

      {upload.data && <RecommendationView rec={upload.data} />}
    </div>
  );
}
