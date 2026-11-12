"use client";

import Link from "next/link";
import { useState } from "react";
import { Download, Eye, FileText, FlaskConical, Trash2 } from "lucide-react";
import { api, type ExperimentSummary } from "@/lib/api";
import { formatDate, percent } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { ExperimentStatusBadge } from "@/components/ExperimentResults";
import { Card, EmptyState, ErrorNotice, Loading, PageHeader, SourceBadge } from "@/components/ui";

export default function HistoryPage() {
  const experiments = useApi(() => api.experiments(), "history");
  const [source, setSource] = useState<"all" | "real" | "simulated">("all");
  const [actionError, setActionError] = useState<string | null>(null);

  const remove = async (experiment: ExperimentSummary) => {
    if (!window.confirm(`Permanently delete experiment ${experiment.id} and its ${experiment.completed_runs} stored runs? This cannot be undone.`)) return;
    setActionError(null);
    try {
      await api.deleteExperiment(experiment.id);
      experiments.reload();
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Could not delete the experiment");
    }
  };

  const shown = (experiments.data ?? []).filter(
    (experiment) => source === "all" || (source === "simulated") === experiment.simulated,
  );

  return (
    <>
      <PageHeader
        title="Experiment History"
        description="Every experiment is stored with its configuration, exact prompts, raw responses and evaluation, so results can be reviewed and exported later."
        actions={
          <>
            <select className="input w-auto" value={source} onChange={(event) => setSource(event.target.value as typeof source)} aria-label="Filter by result source">
              <option value="all">All sources</option>
              <option value="real">Real LLM only</option>
              <option value="simulated">Simulated only</option>
            </select>
            <Link href="/run" className="btn btn-primary"><FlaskConical className="h-4 w-4" /> Run New Experiment</Link>
          </>
        }
      />
      {experiments.error && <ErrorNotice message={experiments.error} onRetry={experiments.reload} />}
      {actionError && <div className="mb-4"><ErrorNotice message={actionError} /></div>}
      {!experiments.error && !experiments.data && <Loading label="Loading history" />}

      {experiments.data && shown.length === 0 && (
        <EmptyState
          title="No experiments to show"
          description={experiments.data.length === 0 ? "Experiments you run will be listed here with their results." : "No experiments match this source filter."}
        />
      )}

      {experiments.data && shown.length > 0 && (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px]">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="th">Experiment</th>
                  <th className="th">Source / model</th>
                  <th className="th">Status</th>
                  <th className="th">Scope</th>
                  <th className="th">Attack compl.</th>
                  <th className="th">Task acc.</th>
                  <th className="th">False refusal</th>
                  <th className="th">Started</th>
                  <th className="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((experiment) => (
                  <tr key={experiment.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                    <td className="td">
                      <Link href={`/experiment?id=${experiment.id}`} className="font-medium text-navy-800 hover:underline">{experiment.name}</Link>
                      <div className="font-mono text-[11px] text-slate-400">{experiment.id}</div>
                    </td>
                    <td className="td">
                      <SourceBadge simulated={experiment.simulated} />
                      <div className="mt-0.5 max-w-44 truncate text-xs text-slate-500" title={experiment.model}>{experiment.model}</div>
                    </td>
                    <td className="td">
                      <ExperimentStatusBadge status={experiment.status} />
                      {experiment.metrics.error_runs > 0 && <div className="mt-0.5 text-xs text-red-700">{experiment.metrics.error_runs} failed run(s)</div>}
                    </td>
                    <td className="td whitespace-nowrap text-xs">
                      {experiment.test_case_count} case(s) × {experiment.strategy_ids.length} strateg{experiment.strategy_ids.length === 1 ? "y" : "ies"} × {experiment.repetitions}
                      <div className="text-slate-500">{experiment.completed_runs} of {experiment.total_runs} runs</div>
                    </td>
                    <td className="td">{percent(experiment.metrics.attack_compliance_rate)}</td>
                    <td className="td">{percent(experiment.metrics.task_accuracy)}</td>
                    <td className="td">{percent(experiment.metrics.false_refusal_rate)}</td>
                    <td className="td whitespace-nowrap text-xs">{formatDate(experiment.created_at)}</td>
                    <td className="td">
                      <div className="flex justify-end gap-1">
                        <Link className="btn btn-secondary btn-sm" href={`/experiment?id=${experiment.id}`}><Eye className="h-3.5 w-3.5" /> View</Link>
                        <a className="btn btn-secondary btn-sm" href={api.experimentExportUrl(experiment.id, "csv")} aria-label={`Download CSV for ${experiment.id}`}><Download className="h-3.5 w-3.5" /> CSV</a>
                        <a className="btn btn-secondary btn-sm" href={api.experimentExportUrl(experiment.id, "pdf")} aria-label={`Download PDF report for ${experiment.id}`}><FileText className="h-3.5 w-3.5" /> PDF</a>
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => void remove(experiment)} aria-label={`Delete ${experiment.id}`}><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
