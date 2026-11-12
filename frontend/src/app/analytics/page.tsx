"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { CATEGORIES, CATEGORY_LABELS, CATEGORY_SHORT, METRIC_COLORS, humanize } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { CategoryStrategyChart, StrategyMetricChart, TimelineChart } from "@/components/charts";
import { Card, EmptyState, ErrorNotice, Loading, PageHeader, SimulatedBanner, SourceToggle } from "@/components/ui";

export default function AnalyticsPage() {
  const [sourceChoice, setSourceChoice] = useState<boolean | null>(null);
  const [strategy, setStrategy] = useState("");
  const [category, setCategory] = useState("");
  const [provider, setProvider] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const counts = useApi(() => api.analytics(), "counts");
  const simulated = sourceChoice ?? (counts.data ? counts.data.available.real_runs === 0 : true);
  const filters = { simulated, strategy, category, provider, date_from: dateFrom, date_to: dateTo };
  const analytics = useApi(() => api.analytics(filters), JSON.stringify(filters));
  const data = analytics.data;
  const error = counts.error ?? analytics.error;
  const hasRuns = (data?.overall.evaluated_runs ?? 0) > 0;
  const filtered = Boolean(strategy || category || provider || dateFrom || dateTo);
  const shownStrategies = data ? data.strategies.filter((candidate) => !strategy || candidate.id === strategy) : [];
  const attackCategories = CATEGORIES.filter((id) => id !== "benign").map((id) => ({ id, label: CATEGORY_SHORT[id] }));
  const allCategories = [...CATEGORIES, "custom"].map((id) => ({ id, label: CATEGORY_SHORT[id] }));

  const clear = () => { setStrategy(""); setCategory(""); setProvider(""); setDateFrom(""); setDateTo(""); };

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Charts are computed live from stored experiment runs. Real and simulated results are never mixed in one chart."
        actions={counts.data && <SourceToggle value={simulated} onChange={setSourceChoice} available={counts.data.available} />}
      />

      <div className="card mb-5 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-6">
        <div>
          <label className="label" htmlFor="filter-strategy">Strategy</label>
          <select id="filter-strategy" className="input" value={strategy} onChange={(event) => setStrategy(event.target.value)}>
            <option value="">All strategies</option>
            {data?.strategies.map((option) => <option key={option.id} value={option.id}>{option.short_label}. {option.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="filter-category">Attack category</label>
          <select id="filter-category" className="input" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {allCategories.map((option) => <option key={option.id} value={option.id}>{CATEGORY_LABELS[option.id]}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="filter-provider">Model provider</label>
          <select id="filter-provider" className="input" value={provider} onChange={(event) => setProvider(event.target.value)}>
            <option value="">All providers</option>
            {data?.providers.map((option) => <option key={option} value={option}>{humanize(option)}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="filter-from">From date</label>
          <input id="filter-from" type="date" className="input" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="filter-to">To date</label>
          <input id="filter-to" type="date" className="input" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        </div>
        <div className="flex items-end">
          <button type="button" className="btn btn-secondary w-full" onClick={clear} disabled={!filtered}>Clear filters</button>
        </div>
      </div>

      {error && <ErrorNotice message={error} onRetry={() => { counts.reload(); analytics.reload(); }} />}
      {!error && !data && <Loading label="Loading analytics" />}

      {!error && data && !hasRuns && (
        <EmptyState
          title="Insufficient data"
          description={filtered
            ? "No evaluated runs match these filters. Clear a filter or change the result source."
            : `There are no ${simulated ? "simulated" : "real-LLM"} experiment results yet. Run an experiment to generate analytics; no placeholder percentages are shown.`}
        />
      )}

      {!error && data && hasRuns && (
        <div className="space-y-5">
          {simulated && <SimulatedBanner />}
          <p className="text-xs text-slate-500">
            Based on {data.overall.evaluated_runs} evaluated responses from {data.experiment_count} experiment(s) (dates in UTC).
            {data.overall.error_runs > 0 && ` ${data.overall.error_runs} run(s) failed with provider errors and are excluded.`}
          </p>
          <div className="grid gap-5 lg:grid-cols-3">
            <Card title="Attack compliance by strategy" subtitle="Lower is better.">
              <StrategyMetricChart strategies={shownStrategies} metrics={data.by_strategy} metric="attack_compliance_rate" color={METRIC_COLORS.attack} />
            </Card>
            <Card title="Legitimate task accuracy by strategy" subtitle="Higher is better.">
              <StrategyMetricChart strategies={shownStrategies} metrics={data.by_strategy} metric="task_accuracy" color={METRIC_COLORS.task} />
            </Card>
            <Card title="False refusal rate by strategy" subtitle="Lower is better.">
              <StrategyMetricChart strategies={shownStrategies} metrics={data.by_strategy} metric="false_refusal_rate" color={METRIC_COLORS.refusal} />
            </Card>
          </div>

          <Card title="Attack compliance by attack category" subtitle="Attack compliance rate per category and strategy. Lower is better. Benign documents contain no attack and are not shown.">
            <CategoryStrategyChart categories={attackCategories} strategies={shownStrategies} data={data.by_category_and_strategy} metric="attack_compliance_rate" />
          </Card>

          <Card title="Task accuracy by category" subtitle="Legitimate task accuracy per category and strategy, including benign documents. Higher is better.">
            <CategoryStrategyChart categories={allCategories} strategies={shownStrategies} data={data.by_category_and_strategy} metric="task_accuracy" />
          </Card>

          <Card title="Experiment history over time" subtitle="One point per experiment, in chronological order. Experiments can differ in test cases and strategies, so compare with care.">
            <TimelineChart
              points={data.timeline.map((point, index) => ({
                label: `#${index + 1} ${point.created_at.slice(5, 10)}`,
                attack: point.metrics.attack_compliance_rate,
                task: point.metrics.task_accuracy,
                refusal: point.metrics.false_refusal_rate,
              }))}
            />
          </Card>
        </div>
      )}
    </>
  );
}
