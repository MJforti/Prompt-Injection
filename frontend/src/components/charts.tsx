"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Metrics } from "@/lib/api";
import { METRIC_COLORS, STRATEGY_COLORS } from "@/lib/format";

const AXIS = { fontSize: 11, fill: "#64748b" };
const TOOLTIP_STYLE = { fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" };
const percentTick = (value: number) => `${value}%`;
const percentTooltip = (value: unknown) => (value === null || value === undefined ? "n/a" : `${value}%`);

export interface StrategyRef {
  id: string;
  name: string;
  short_label: string;
}

type MetricKey = "attack_compliance_rate" | "task_accuracy" | "false_refusal_rate";

/** One metric as a bar per strategy. Strategies without data are omitted, never drawn as 0. */
export function StrategyMetricChart({ strategies, metrics, metric, color, height = 240 }: {
  strategies: StrategyRef[];
  metrics: Record<string, Metrics>;
  metric: MetricKey;
  color: string;
  height?: number;
}) {
  const data = strategies
    .filter((strategy) => metrics[strategy.id] && metrics[strategy.id][metric] !== null)
    .map((strategy) => ({ name: `${strategy.short_label}. ${strategy.name}`, value: metrics[strategy.id][metric] }));
  if (data.length === 0) return <NoChartData />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="name" tick={AXIS} interval={0} tickFormatter={(name: string) => name.split(".")[0]} />
        <YAxis domain={[0, 100]} tick={AXIS} tickFormatter={percentTick} />
        <Tooltip formatter={percentTooltip} contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#f1f5f9" }} />
        <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={56} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Attack compliance and task accuracy side by side per strategy. */
export function StrategyOverviewChart({ strategies, metrics }: { strategies: StrategyRef[]; metrics: Record<string, Metrics> }) {
  const data = strategies
    .filter((strategy) => metrics[strategy.id])
    .map((strategy) => ({
      name: `${strategy.short_label}. ${strategy.name}`,
      "Attack compliance": metrics[strategy.id].attack_compliance_rate,
      "Task accuracy": metrics[strategy.id].task_accuracy,
      "False refusal": metrics[strategy.id].false_refusal_rate,
    }));
  if (data.length === 0) return <NoChartData />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="name" tick={AXIS} interval={0} tickFormatter={(name: string) => name.split(".")[0]} />
        <YAxis domain={[0, 100]} tick={AXIS} tickFormatter={percentTick} />
        <Tooltip formatter={percentTooltip} contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#f1f5f9" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Attack compliance" fill={METRIC_COLORS.attack} radius={[3, 3, 0, 0]} isAnimationActive={false} />
        <Bar dataKey="Task accuracy" fill={METRIC_COLORS.task} radius={[3, 3, 0, 0]} isAnimationActive={false} />
        <Bar dataKey="False refusal" fill={METRIC_COLORS.refusal} radius={[3, 3, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AttackOutcomeChart({ metrics }: { metrics: Metrics }) {
  const data = [
    { name: "Attack resisted", value: metrics.attack_resisted, color: "#059669" },
    { name: "Attack followed", value: metrics.attack_followed, color: "#dc2626" },
    { name: "Evaluation uncertain", value: metrics.attack_uncertain, color: "#d97706" },
  ].filter((entry) => entry.value > 0);
  if (data.length === 0) return <NoChartData />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={92} paddingAngle={2} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(value: unknown) => `${value} responses`} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

/** One metric per category, one bar per strategy. */
export function CategoryStrategyChart({ categories, strategies, data, metric }: {
  categories: { id: string; label: string }[];
  strategies: StrategyRef[];
  data: Record<string, Record<string, Metrics>>;
  metric: MetricKey;
}) {
  const rows = categories
    .filter((category) => data[category.id])
    .map((category) => {
      const row: Record<string, string | number | null> = { name: category.label };
      for (const strategy of strategies) {
        row[strategy.name] = data[category.id][strategy.id]?.[metric] ?? null;
      }
      return row;
    })
    .filter((row) => strategies.some((strategy) => row[strategy.name] !== null));
  if (rows.length === 0) return <NoChartData />;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="name" tick={AXIS} interval={0} />
        <YAxis domain={[0, 100]} tick={AXIS} tickFormatter={percentTick} />
        <Tooltip formatter={percentTooltip} contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#f1f5f9" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {strategies.map((strategy, index) => (
          <Bar key={strategy.id} dataKey={strategy.name} fill={STRATEGY_COLORS[index % STRATEGY_COLORS.length]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TimelineChart({ points }: { points: { label: string; attack: number | null; task: number | null; refusal: number | null }[] }) {
  if (points.length === 0) return <NoChartData />;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={points} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={AXIS} />
        <YAxis domain={[0, 100]} tick={AXIS} tickFormatter={percentTick} />
        <Tooltip formatter={percentTooltip} contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="attack" name="Attack compliance" stroke={METRIC_COLORS.attack} strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
        <Line type="monotone" dataKey="task" name="Task accuracy" stroke={METRIC_COLORS.task} strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
        <Line type="monotone" dataKey="refusal" name="False refusal" stroke={METRIC_COLORS.refusal} strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function NoChartData() {
  return (
    <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-slate-200 text-sm text-slate-400">
      Not enough data to draw this chart yet.
    </div>
  );
}
