/**
 * useMarketingStats — fetch lightweight aggregate counts (partners, users, etc.)
 * for marketing pages. Falls back silently to defaults if backend not available.
 */
import { useEffect, useState } from "react";
import api from "@/lib/api";

export function useMarketingStats() {
	const [stats, setStats] = useState(null);

	useEffect(() => {
		let cancelled = false;
		api.get("/public/marketing-stats")
			.then((r) => { if (!cancelled) setStats(r.data || null); })
			.catch(() => { /* silent — fallback values in consumer */ });
		return () => { cancelled = true; };
	}, []);

	return stats;
}

export default useMarketingStats;
