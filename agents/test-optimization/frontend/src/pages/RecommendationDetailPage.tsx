import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { RecommendationView } from "@/components/RecommendationView";
import { ErrorState, Spinner } from "@/components/ui";
import { api } from "@/lib/api";

export function RecommendationDetailPage() {
  const { id = "" } = useParams();

  const detail = useQuery({
    queryKey: ["recommendation", id],
    queryFn: () => api.getRecommendation(id),
    enabled: Boolean(id),
  });

  if (detail.isLoading) return <Spinner label="Loading recommendation…" />;
  if (detail.isError) {
    return <ErrorState message={(detail.error as Error).message} onRetry={() => detail.refetch()} />;
  }
  if (!detail.data) return null;

  return (
    <div className="space-y-4">
      <Link
        to="/recommendations"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-300 transition hover:text-ink-100"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to history
      </Link>
      <RecommendationView rec={detail.data} />
    </div>
  );
}
