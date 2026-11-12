"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, FlaskConical } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, percent } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { AttackOutcomeChart, StrategyOverviewChart } from "@/components/charts";
import { ExperimentStatusBadge } from "@/components/ExperimentResults";
import { Card, EmptyState, ErrorNotice, Loading, PageHeader, SimulatedBanner, SourceBadge, SourceToggle, StatCard } from "@/components/ui";

export default function OverviewPage() {
  const [sourceChoice, setSourceChoice] = useState<boolean | null>(null);
  const counts = useApi(() => api.analytics(), "counts");
  // Default to real results when any exist; otherwise show (clearly labelled) simulated data.
  const simulated = sourceChoice ?? (counts.data ? counts.data.available.real_runs === 0 : true);
  const analytics = useApi(() => api.analytics({ simulated }), `overview-${simulated}`);
  const experiments = useApi(() => api.experiments(), "recent");

  const runButton = (
    <Link href="/run" className="btn btn-primary">
      <FlaskConical className="h-4 w-4" /> Run New Experiment
    </Link>
  );

  const error = counts.error ?? analytics.error ?? experiments.error;
  const data = analytics.data;
  const best = data?.strategies.find((strategy) => strategy.id === data.most_effective_strategy);
  const hasRuns = (data?.overall.total_runs ?? 0) > 0;
  const noRunsAtAll = counts.data && counts.data.available.real_runs + counts.data.available.simulated_runs === 0;

  return (
    <>
      <PageHeader
        title="Overview"
        description="How often do models follow instructions hidden inside documents, and which prompt-engineering strategies reduce it without breaking the legitimate task?"
        actions={
          <>
            {counts.data && !noRunsAtAll && <SourceToggle value={simulated} onChange={setSourceChoice} available={counts.data.available} />}
            {runButton}
          </>
        }
      />

      {error && <ErrorNotice message={error} onRetry={() => { counts.reload(); analytics.reload(); experiments.reload(); }} />}
      {!error && (!data || !experiments.data) && <Loading label="Loading dashboard" />}

      {!error && data && experiments.data && (
        <>
          {noRunsAtAll ? (
            <EmptyState
              title="No experiments have been run yet"
              description={`The dataset contains ${data.test_case_count} synthetic test cases. Run an experiment to populate this dashboard. Nothing shown here is ever pre-filled with invented results.`}
              action={runButton}
            />
          ) : (
            <>
              {simulated && hasRuns && <SimulatedBanner />}
              {!hasRuns && (
                <div className="mb-5">
                  <EmptyState
                    title={simulated ? "No simulated experiments yet" : "No real-LLM experiments yet"}
                    description={simulated ? "Run an experiment with the mock simulator to see demo data here." : "Configure an OpenAI-compatible API key and run an experiment, or switch to the simulated results."}
                  />
                </div>
              )}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <StatCard label="Total experiments" value={String(data.experiment_count)} hint={`${data.overall.total_runs} model responses stored`} />
                <StatCard label="Total test cases" value={String(data.test_case_count)} hint="Synthetic cases in the dataset" />
                <StatCard
                  label="Avg. attack compliance rate"
                  value={percent(data.overall.attack_compliance_rate)}
                  direction="lower"
                  hint={`${data.overall.attack_followed} of ${data.overall.attack_runs} attack responses followed the injection.`}
                />
                <StatCard
                  label="Avg. legitimate task accuracy"
                  value={percent(data.overall.task_accuracy)}
                  direction="higher"
                  hint={`${data.overall.task_completed} of ${data.overall.task_runs} tasks completed.`}
                />
                <StatCard
                  label="False refusal rate"
                  value={percent(data.overall.false_refusal_rate)}
                  direction="lower"
                  hint={`${data.overall.refusals} of ${data.overall.evaluated_runs} responses refused a legitimate task.`}
                />
                <StatCard
                  label="Lowest attack compliance"
                  value={best ? `${best.short_label}. ${best.name}` : "n/a"}
                  hint={best ? `${percent(data.by_strategy[best.id].attack_compliance_rate)} in the ${simulated ? "simulated" : "tested"} runs. Ranking only, not proof of protection.` : "Needs at least one evaluated attack response."}
                />
              </div>

              <div className="mt-5 grid gap-5 lg:grid-cols-5">
                <Card className="lg:col-span-3" title="Strategy performance" subtitle="Attack compliance and false refusal: lower is better. Task accuracy: higher is better.">
                  <StrategyOverviewChart strategies={data.strategies} metrics={data.by_strategy} />
                </Card>
                <Card className="lg:col-span-2" title="Attack outcome distribution" subtitle="All evaluated responses to documents containing an injection.">
                  <AttackOutcomeChart metrics={data.overall} />
                </Card>
              </div>
            </>
          )}

          <Card
            className="mt-5"
            title="Recent experiments"
            actions={
              <Link href="/history" className="inline-flex items-center gap-1 text-xs font-medium text-navy-700 hover:underline">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            }
          >
            {experiments.data.length === 0 ? (
              <p className="text-sm text-slate-500">No experiments yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px]">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="th">Experiment</th>
                      <th className="th">Source</th>
                      <th className="th">Status</th>
                      <th className="th">Attack compliance</th>
                      <th className="th">Task accuracy</th>
                      <th className="th">Started</th>
                    </tr>
                  </thead>
                  <tbody>
                    {experiments.data.slice(0, 6).map((experiment) => (
                      <tr key={experiment.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                        <td className="td">
                          <Link href={`/experiment?id=${experiment.id}`} className="font-medium text-navy-800 hover:underline">{experiment.name}</Link>
                          <div className="font-mono text-[11px] text-slate-400">{experiment.id}</div>
                        </td>
                        <td className="td"><SourceBadge simulated={experiment.simulated} /></td>
                        <td className="td"><ExperimentStatusBadge status={experiment.status} /></td>
                        <td className="td">{percent(experiment.metrics.attack_compliance_rate)}</td>
                        <td className="td">{percent(experiment.metrics.task_accuracy)}</td>
                        <td className="td whitespace-nowrap">{formatDate(experiment.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </>
  );
}
