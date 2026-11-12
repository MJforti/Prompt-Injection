"use client";

import { useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { api, type Strategy } from "@/lib/api";
import { METRIC_COLORS, formatDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { StrategyMetricChart } from "@/components/charts";
import { StrategyMetricsTable } from "@/components/StrategyMetricsTable";
import { Badge, Card, EmptyState, ErrorNotice, Loading, PageHeader, SimulatedBanner, SourceToggle } from "@/components/ui";

const TEMPLATE_LABELS: Record<string, string> = {
  system: "System prompt",
  user: "User prompt",
  stage1_system: "Stage 1 system prompt (fact extraction)",
  stage1_user: "Stage 1 user prompt",
  stage2_system: "Stage 2 system prompt (task completion)",
  stage2_user: "Stage 2 user prompt",
};

function StrategyEditor({ strategy, onChanged }: { strategy: Strategy; onChanged: () => void }) {
  const [templates, setTemplates] = useState(strategy.templates);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dirty = JSON.stringify(templates) !== JSON.stringify(strategy.templates);

  const run = async (action: () => Promise<Strategy>) => {
    setBusy(true);
    setError(null);
    try {
      const updated = await action();
      setTemplates(updated.templates);
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save the strategy");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title={`${strategy.short_label}. ${strategy.name}`}
      subtitle={strategy.description}
      actions={
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge tone="navy">Version {strategy.version}</Badge>
          {strategy.is_default ? <Badge tone="slate">Default text</Badge> : <Badge tone="amber">Edited</Badge>}
          {strategy.kind === "two_stage" && <Badge tone="slate">Two LLM calls</Badge>}
        </div>
      }
    >
      <div className="grid gap-3 md:grid-cols-2">
        {Object.keys(strategy.templates).map((key) => (
          <div key={key}>
            <label className="label" htmlFor={`${strategy.id}-${key}`}>{TEMPLATE_LABELS[key] ?? key}</label>
            <textarea
              id={`${strategy.id}-${key}`}
              className="input min-h-36 font-mono text-xs leading-relaxed"
              value={templates[key] ?? ""}
              onChange={(event) => setTemplates((current) => ({ ...current, [key]: event.target.value }))}
            />
          </div>
        ))}
      </div>
      {error && <div className="mt-3"><ErrorNotice message={error} /></div>}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500">
          Placeholders: <code>{"{task}"}</code>, <code>{"{document}"}</code>
          {strategy.kind === "two_stage" && <>, <code>{"{extracted}"}</code> (stage 1 output)</>}. Last changed {formatDate(strategy.updated_at)}.
        </p>
        <div className="flex gap-2">
          <button type="button" className="btn btn-secondary btn-sm" disabled={busy || (strategy.is_default && !dirty)}
            onClick={() => { if (window.confirm(`Reset "${strategy.name}" to its default prompt text?`)) void run(() => api.resetStrategy(strategy.id)); }}>
            <RotateCcw className="h-3.5 w-3.5" /> Reset to default
          </button>
          <button type="button" className="btn btn-primary btn-sm" disabled={busy || !dirty} onClick={() => void run(() => api.updateStrategy(strategy.id, templates))}>
            <Save className="h-3.5 w-3.5" /> Save as version {strategy.version + 1}
          </button>
        </div>
      </div>
    </Card>
  );
}

export default function ComparisonPage() {
  const [sourceChoice, setSourceChoice] = useState<boolean | null>(null);
  const counts = useApi(() => api.analytics(), "counts");
  const simulated = sourceChoice ?? (counts.data ? counts.data.available.real_runs === 0 : true);
  const analytics = useApi(() => api.analytics({ simulated }), `comparison-${simulated}`);
  const strategies = useApi(() => api.strategies(), "strategies");
  const data = analytics.data;
  const hasRuns = (data?.overall.total_runs ?? 0) > 0;
  const error = counts.error ?? analytics.error ?? strategies.error;

  return (
    <>
      <PageHeader
        title="Strategy Comparison"
        description="Compare the four prompt-engineering strategies across all stored experiments, and inspect or edit the exact prompt templates they use."
        actions={counts.data && <SourceToggle value={simulated} onChange={setSourceChoice} available={counts.data.available} />}
      />
      {error && <ErrorNotice message={error} onRetry={() => { counts.reload(); analytics.reload(); strategies.reload(); }} />}
      {!error && (!data || !strategies.data) && <Loading label="Loading strategies" />}

      {!error && data && strategies.data && (
        <div className="space-y-5">
          {simulated && hasRuns && <SimulatedBanner />}
          {hasRuns ? (
            <Card
              title={`Aggregate results (${simulated ? "simulated" : "real LLM"} runs)`}
              subtitle={`${data.overall.total_runs} responses from ${data.experiment_count} experiment(s). Experiments may have used different prompt versions; open an experiment to see the exact prompts it ran.`}
            >
              <StrategyMetricsTable strategies={data.strategies} metrics={data.by_strategy} mostEffective={data.most_effective_strategy} />
              <div className="mt-5 grid gap-5 md:grid-cols-3">
                <div>
                  <div className="mb-1 text-xs font-medium text-slate-600">Attack compliance rate (lower is better)</div>
                  <StrategyMetricChart strategies={data.strategies} metrics={data.by_strategy} metric="attack_compliance_rate" color={METRIC_COLORS.attack} height={210} />
                </div>
                <div>
                  <div className="mb-1 text-xs font-medium text-slate-600">Legitimate task accuracy (higher is better)</div>
                  <StrategyMetricChart strategies={data.strategies} metrics={data.by_strategy} metric="task_accuracy" color={METRIC_COLORS.task} height={210} />
                </div>
                <div>
                  <div className="mb-1 text-xs font-medium text-slate-600">False refusal rate (lower is better)</div>
                  <StrategyMetricChart strategies={data.strategies} metrics={data.by_strategy} metric="false_refusal_rate" color={METRIC_COLORS.refusal} height={210} />
                </div>
              </div>
            </Card>
          ) : (
            <EmptyState
              title={`No ${simulated ? "simulated" : "real-LLM"} results to compare yet`}
              description="Run an experiment with two or more strategies. The comparison table and charts are calculated only from stored runs."
            />
          )}

          <Card title="How to read the metrics">
            <dl className="grid gap-4 text-sm md:grid-cols-3">
              <div>
                <dt className="font-semibold text-navy-900">Attack compliance rate <span className="font-normal text-slate-500">(lower is better)</span></dt>
                <dd className="mt-1 text-slate-600">Attack-following responses ÷ evaluated attack responses × 100. “Uncertain” verdicts are listed separately and are not counted as followed.</dd>
              </div>
              <div>
                <dt className="font-semibold text-navy-900">Legitimate task accuracy <span className="font-normal text-slate-500">(higher is better)</span></dt>
                <dd className="mt-1 text-slate-600">Responses containing enough of the expected facts ÷ task-evaluated responses × 100. A defense that blocks attacks but breaks the task is not useful.</dd>
              </div>
              <div>
                <dt className="font-semibold text-navy-900">False refusal rate <span className="font-normal text-slate-500">(lower is better)</span></dt>
                <dd className="mt-1 text-slate-600">Responses that refused a legitimate task ÷ evaluated responses × 100. Guards against “defenses” that simply refuse every document.</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs text-slate-500">The metrics are deliberately not combined into one score. {data.most_effective_rule}</p>
          </Card>

          <div id="templates" className="scroll-mt-6">
            <h2 className="mb-1 text-lg font-semibold text-navy-900">Prompt templates</h2>
            <p className="mb-4 max-w-3xl text-sm text-slate-500">
              These are the exact templates sent to the model. Saving an edit creates a new version; every experiment stores a snapshot of the templates and the fully rendered prompt of each run, so earlier results always show what was actually sent.
            </p>
            <div className="space-y-5">
              {strategies.data.map((strategy) => (
                <StrategyEditor key={`${strategy.id}-${strategy.version}`} strategy={strategy} onChanged={strategies.reload} />
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
