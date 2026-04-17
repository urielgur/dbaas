import { ExternalLink } from "lucide-react";
import { useDbTypes } from "../../hooks/useDbTypes";

const TYPE_COLORS: Record<string, string> = {
  elasticsearch: "border-yellow-200 bg-yellow-50",
  mongodb: "border-green-200 bg-green-50",
  postgresql: "border-blue-200 bg-blue-50",
};

const BADGE_COLORS: Record<string, string> = {
  elasticsearch: "bg-yellow-100 text-yellow-800",
  mongodb: "bg-green-100 text-green-800",
  postgresql: "bg-blue-100 text-blue-800",
};

export function ParentChartsSection() {
  const { data: dbTypes } = useDbTypes();

  if (!dbTypes || dbTypes.length === 0) return null;

  const chartsWithUrls = dbTypes.filter((t) => t.helm_chart_url);
  if (chartsWithUrls.length === 0) return null;

  return (
    <section aria-label="Parent helm charts" className="mb-6">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Parent Helm Charts
      </h2>
      <div className="flex flex-wrap gap-3">
        {chartsWithUrls.map((t) => {
          const cardCls = TYPE_COLORS[t.canonical_name] ?? "border-gray-200 bg-gray-50";
          const badgeCls = BADGE_COLORS[t.canonical_name] ?? "bg-gray-100 text-gray-700";

          return (
            <a
              key={t.canonical_name}
              href={t.helm_chart_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`group flex items-center gap-3 px-4 py-3 rounded-lg border ${cardCls} hover:shadow-sm transition-shadow min-w-[200px]`}
              aria-label={`${t.display_label} parent helm chart (opens in new tab)`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badgeCls}`}>
                    {t.display_label}
                  </span>
                </div>
                {t.helm_chart_version && (
                  <p className="text-xs text-gray-500 mt-1 font-mono">{t.helm_chart_version}</p>
                )}
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-600 flex-shrink-0" aria-hidden="true" />
            </a>
          );
        })}
      </div>
    </section>
  );
}
