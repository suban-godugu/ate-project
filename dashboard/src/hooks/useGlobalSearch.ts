"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchPlatform as searchLocal } from "@/lib/searchIndex";
import { searchPlatform as searchRemote } from "@/lib/api/dashboard";
import { isLiveApi } from "@/lib/api/config";
import { useFilterStore } from "@/stores/filterStore";

export function useGlobalSearch() {
  const query = useFilterStore((s) => s.searchQuery);
  const liveQuery = useQuery({
    queryKey: ["search", query],
    queryFn: () => searchRemote(query),
    enabled: isLiveApi() && query.trim().length > 0,
  });

  const mockResults = useMemo(() => searchLocal(query), [query]);
  const results = isLiveApi() ? (liveQuery.data ?? []) : mockResults;

  return { query, results, isLoading: isLiveApi() ? liveQuery.isLoading : false };
}
