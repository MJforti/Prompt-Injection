"use client";

import { useState } from "react";
import { AlertTriangle, Download, FileJson, FileText } from "lucide-react";
import { api, type Experiment, type Message, type Run, type Strategy } from "@/lib/api";
import { CATEGORY_LABELS, METRIC_COLORS, formatDate, formatMs, humanize, percent } from "@/lib/format";
import { StrategyMetricChart } from "./charts";
import { StrategyMetricsTable } from "./StrategyMetricsTable";
import { Badge, Card, DocumentView, SimulatedBanner, SourceBadge } from "./ui";

const STATUS_LABEL: Record<string, string> = {
  pending: "Queued",
  running: "Running",
  completed: "Completed",
  completed_with_errors: "Completed with errors",
  failed: "Failed",
};

export function ExperimentStatusBadge({ status }: { status: string }) {
  const tone = status === "completed" ? "green" : status === "failed" ? "red" : status === "completed_with_errors" ? "amber" : "navy";
  return <Badge tone={tone}>{STATUS_LABEL[status] ?? status}</Badge>;
}

export function RunBadges({ run }: { run: Run }) {
  if (run.status === "error") return <Badge tone="red">Provider error</Badge>;
  return (
    <>
      {run.attack_status === "resisted" && <Badge tone="green">Attack resisted</Badge>}
      {run.attack_status === "followed" && <Badge tone="red">Attack followed</Badge>}
      {run.attack_status === "uncertain" && <Badge tone="amber">Evaluation uncertain</Badge>}
      {run.attack_status === "not_applicable" && <Badge tone="slate">No attack in document</Badge>}
      {run.task_status === "completed" && <Badge tone="green">Task completed</Badge>}
      {run.task_status === "incomplete" && <Badge tone="red">Task incomplete</Badge>}
      {run.task_status === "not_evaluated" && <Badge tone="slate">Task not evaluated</Badge>}
      {run.refused && <Badge tone="amber">False refusal</Badge>}
    </>
  );
}

function Messages({ messages }: { messages: Message[] }) {
  return (
    <div className="space-y-2">
      {messages.map((message, index) => (
        <div key={index}>
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">{message.role}</div>
          <div className="codeblock">{message.content}</div>
        </div>
      ))}
    </div>
  );
}

function Disclosure({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <details className="group rounded-lg border border-slate-200">
      <summary className="cursor-pointer select-none px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">{label}</summary>
      <div className="border-t border-slate-200 p-3">{children}</div>
    </details>
  );
}

function RunCard({ run, strategy }: { run: Run | undefined; strategy: Strategy }) {
  return (
    <div className="card flex min-w-0 flex-col p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-sm font-semibold text-navy-900">
            {strategy.short_label}. {strategy.name}
          </div>
          <div className="text-xs text-slate-500">Prompt version {strategy.version}</div>
        </div>
        {run?.latency_ms != null && <span className="whitespace-nowrap text-xs text-slate-500">{formatMs(run.latency_ms)}</span>}
      </div>
      {!run ? (
        <p className="mt-4 text-sm text-slate-400">Waiting for this run…</p>
      ) : (
        <>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <RunBadges run={run} />
          </div>
          {run.status === "error" ? (
            <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
              <div className="font-semibold">{humanize(run.error_type)}</div>
              {run.error}
              <div className="mt-1 text-red-700">No response was recorded. Failed calls are never replaced with simulated output.</div>
            </div>
          ) : (
            <>
              <div className="mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Raw response</div>
              <div className="codeblock mt-1 max-h-64 overflow-y-auto">{run.response}</div>
            </>
          )}
          <div className="mt-3 space-y-2">
            <Disclosure label="Exact prompt sent">
              {run.prompt.main && <Messages messages={run.prompt.main} />}
              {run.prompt.stage1 && (
                <>
                  <div className="mb-2 text-xs font-semibold text-navy-900">Stage 1: fact extraction</div>
                  <Messages messages={run.prompt.stage1} />
                </>
              )}
              {run.prompt.stage2 && (
                <>
                  <div className="mb-2 mt-4 text-xs font-semibold text-navy-900">Stage 2: task completion</div>
                  <Messages messages={run.prompt.stage2} />
                </>
              )}
            </Disclosure>
            {run.stage1_output != null && (
              <Disclosure label="Stage 1 output (extracted facts)">
                <div className="codeblock">{run.stage1_output}</div>
              </Disclosure>
            )}
            {run.evaluation && (
              <Disclosure label="Evaluation details">
                <dl className="space-y-2.5 text-xs text-slate-700">
                  <div>
                    <dt className="font-semibold text-navy-900">Attack: {humanize(run.evaluation.attack.status)}</dt>
                    <dd>{run.evaluation.attack.rule}</dd>
                    {run.evaluation.attack.markers_checked.length > 0 && (
                      <dd className="mt-0.5 text-slate-500">
                        Markers checked: {run.evaluation.attack.markers_checked.map((marker) => `"${marker}"`).join(", ")}. Matched:{" "}
                        {run.evaluation.attack.matched_markers.length ? run.evaluation.attack.matched_markers.map((marker) => `"${marker}"`).join(", ") : "none"}.
                        {run.evaluation.attack.reporting_language.length > 0 &&
                          ` Reporting language: ${run.evaluation.attack.reporting_language.join(", ")}.`}
                      </dd>
                    )}
                  </div>
                  <div>
                    <dt className="font-semibold text-navy-900">
                      Task: {humanize(run.evaluation.task.status)}
                      {run.evaluation.task.coverage !== null &&
                        ` (${Math.round(run.evaluation.task.coverage * 100)}% of expected facts, threshold ${Math.round(run.evaluation.task.threshold * 100)}%)`}
                    </dt>
                    {run.evaluation.task.matched_facts.map((fact) => (
                      <dd key={fact} className="text-emerald-700">Found: {fact}</dd>
                    ))}
                    {run.evaluation.task.missing_facts.map((fact) => (
                      <dd key={fact} className="text-red-700">Missing: {fact}</dd>
                    ))}
                    {run.evaluation.task.coverage === null && <dd className="text-slate-500">No expected facts were defined for this input.</dd>}
                  </div>
                  <div>
                    <dt className="font-semibold text-navy-900">False refusal: {run.evaluation.refusal.refused ? "yes" : "no"}</dt>
                    <dd>
                      {run.evaluation.refusal.rule}
                      {run.evaluation.refusal.matched_phrases.length > 0 && ` Matched: "${run.evaluation.refusal.matched_phrases.join('", "')}".`}
                    </dd>
                  </div>
                  <div className="text-slate-400">Evaluator: {run.evaluation.evaluator}</div>
                </dl>
              </Disclosure>
            )}
            {run.llm_judge && (
              <Disclosure label="LLM judge (separate, optional second opinion)">
                <div className="codeblock">{JSON.stringify(run.llm_judge, null, 2)}</div>
                <p className="mt-2 text-xs text-slate-500">The LLM judge is itself a model and can be wrong. It is not used in any headline metric.</p>
              </Disclosure>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function ExperimentResults({ experiment }: { experiment: Experiment }) {
  const cases = experiment.cases_snapshot;
  const strategies = experiment.strategy_snapshot;
  const [caseId, setCaseId] = useState(cases[0]?.id ?? "");
  const [repetition, setRepetition] = useState(1);
  const activeCase = cases.find((testCase) => testCase.id === caseId) ?? cases[0];
  const finished = !["pending", "running"].includes(experiment.status);
  const progress = experiment.total_runs ? Math.round((experiment.completed_runs / experiment.total_runs) * 100) : 0;
  const runFor = (strategyId: string) =>
    experiment.runs.find((run) => run.test_case_id === activeCase?.id && run.strategy_id === strategyId && run.repetition === repetition);
  const columns = strategies.length >= 4 ? "xl:grid-cols-4 md:grid-cols-2" : strategies.length === 3 ? "lg:grid-cols-3" : strategies.length === 2 ? "md:grid-cols-2" : "";

  return (
    <div className="space-y-5">
      {experiment.simulated && <SimulatedBanner />}

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-navy-900">{experiment.name}</h2>
              <ExperimentStatusBadge status={experiment.status} />
              <SourceBadge simulated={experiment.simulated} />
            </div>
            <div className="mt-1 font-mono text-xs text-slate-500">{experiment.id}</div>
            <dl className="mt-3 grid grid-cols-2 gap-x-8 gap-y-1 text-sm sm:grid-cols-4">
              <div><dt className="text-xs text-slate-500">Provider</dt><dd>{humanize(experiment.provider)}</dd></div>
              <div><dt className="text-xs text-slate-500">Model</dt><dd className="break-all">{experiment.model}</dd></div>
              <div><dt className="text-xs text-slate-500">Repetitions / temperature</dt><dd>{experiment.repetitions} / {experiment.temperature}</dd></div>
              <div><dt className="text-xs text-slate-500">Started</dt><dd>{formatDate(experiment.created_at)}</dd></div>
            </dl>
          </div>
          {finished && experiment.runs.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <a className="btn btn-secondary btn-sm" href={api.experimentExportUrl(experiment.id, "csv")}><Download className="h-3.5 w-3.5" /> CSV</a>
              <a className="btn btn-secondary btn-sm" href={api.experimentExportUrl(experiment.id, "json")}><FileJson className="h-3.5 w-3.5" /> JSON</a>
              <a className="btn btn-primary btn-sm" href={api.experimentExportUrl(experiment.id, "pdf")}><FileText className="h-3.5 w-3.5" /> PDF report</a>
            </div>
          )}
        </div>
        {!finished && (
          <div className="mt-4">
            <div className="mb-1 flex justify-between text-xs text-slate-500">
              <span>Running… {experiment.completed_runs} of {experiment.total_runs} runs</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-full rounded-full bg-navy-700 transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
        {experiment.error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <span className="font-semibold">Experiment stopped: </span>{experiment.error}. Remaining runs were not executed and no simulated results were substituted.
            </div>
          </div>
        )}
      </Card>

      {experiment.runs.length > 0 && (
        <>
          <Card title="Strategy comparison" subtitle="Calculated from the stored runs of this experiment. The three metrics are reported separately and are not merged into one score.">
            <StrategyMetricsTable strategies={strategies} metrics={experiment.metrics.by_strategy} mostEffective={experiment.metrics.most_effective_strategy} />
            {experiment.metrics.overall.attack_uncertain > 0 && (
              <p className="mt-3 text-xs text-amber-700">
                {experiment.metrics.overall.attack_uncertain} response(s) are marked “evaluation uncertain” and are not counted as followed. Review their raw output below.
              </p>
            )}
            <div className="mt-5 grid gap-5 md:grid-cols-3">
              <div>
                <div className="mb-1 text-xs font-medium text-slate-600">Attack compliance rate (lower is better)</div>
                <StrategyMetricChart strategies={strategies} metrics={experiment.metrics.by_strategy} metric="attack_compliance_rate" color={METRIC_COLORS.attack} height={200} />
              </div>
              <div>
                <div className="mb-1 text-xs font-medium text-slate-600">Legitimate task accuracy (higher is better)</div>
                <StrategyMetricChart strategies={strategies} metrics={experiment.metrics.by_strategy} metric="task_accuracy" color={METRIC_COLORS.task} height={200} />
              </div>
              <div>
                <div className="mb-1 text-xs font-medium text-slate-600">False refusal rate (lower is better)</div>
                <StrategyMetricChart strategies={strategies} metrics={experiment.metrics.by_strategy} metric="false_refusal_rate" color={METRIC_COLORS.refusal} height={200} />
              </div>
            </div>
          </Card>
        </>
      )}

      {activeCase && (
        <Card
          title="Responses side by side"
          subtitle="Every strategy received the same task, document, model and temperature."
          actions={
            <div className="flex flex-wrap items-center gap-2">
              {cases.length > 1 && (
                <select className="input w-auto max-w-xs" value={activeCase.id} onChange={(event) => setCaseId(event.target.value)} aria-label="Test case">
                  {cases.map((testCase) => (
                    <option key={testCase.id} value={testCase.id}>{testCase.id}: {testCase.title}</option>
                  ))}
                </select>
              )}
              {experiment.repetitions > 1 && (
                <select className="input w-auto" value={repetition} onChange={(event) => setRepetition(Number(event.target.value))} aria-label="Repetition">
                  {Array.from({ length: experiment.repetitions }, (_, index) => (
                    <option key={index} value={index + 1}>Repetition {index + 1}</option>
                  ))}
                </select>
              )}
            </div>
          }
        >
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <div className="label">Original user task</div>
              <div className="codeblock">{activeCase.user_task}</div>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <Badge tone="navy">{CATEGORY_LABELS[activeCase.category] ?? activeCase.category}</Badge>
                {activeCase.attack_type && <Badge tone="slate">Attack type: {humanize(activeCase.attack_type)}</Badge>}
              </div>
              {activeCase.expected_behavior && <p className="mt-2 text-xs text-slate-500">Expected behaviour: {activeCase.expected_behavior}</p>}
            </div>
            <div>
              <div className="label">Document used {activeCase.injection_text && <span className="normal-case text-red-700">(embedded instruction highlighted)</span>}</div>
              <DocumentView text={activeCase.document} injection={activeCase.injection_text} />
            </div>
          </div>
          <div className={`mt-5 grid gap-4 ${columns}`}>
            {strategies.map((strategy) => (
              <RunCard key={strategy.id} run={runFor(strategy.id)} strategy={strategy} />
            ))}
          </div>
        </Card>
      )}

      {finished && experiment.metrics.most_effective_strategy && (
        <p className="text-xs text-slate-500">
          “Lowest attack compliance” ranking rule: {experiment.metrics.most_effective_rule} Reading: {percent(experiment.metrics.by_strategy[experiment.metrics.most_effective_strategy]?.attack_compliance_rate)} for the
          highlighted strategy in this experiment only. This is not evidence that any strategy prevents prompt injection.
        </p>
      )}
    </div>
  );
}
