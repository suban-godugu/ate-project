"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { registerQueryClient } from "@/lib/api/queryCache";
import { muteHiddenChartWarning } from "@/lib/muteHiddenChartWarning";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  muteHiddenChartWarning();

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            refetchOnMount: false,
            refetchOnReconnect: false,
            retry: 1,
            staleTime: 5 * 60_000,
            gcTime: 15 * 60_000,
          },
        },
      })
  );

  useEffect(() => {
    registerQueryClient(queryClient);
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
