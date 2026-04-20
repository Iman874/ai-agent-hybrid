import { useState, useEffect } from "react";
import { checkHealth } from "@/api/health";
import type { HealthResponse } from "@/types/api";

export function useHealth(intervalMs = 30_000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetch = async () => {
      try {
        const data = await checkHealth();
        if (mounted) setHealth(data);
      } catch {
        if (mounted) setHealth(null);
      }
    };
    fetch();
    const id = setInterval(fetch, intervalMs);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return health;
}
