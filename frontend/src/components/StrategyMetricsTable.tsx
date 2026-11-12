import type { Metrics } from "@/lib/api";
import { formatMs, percent } from "@/lib/format";
import { Badge } from "./ui";
import type { StrategyRef } from "./charts";

export function StrategyMetricsTable({ strategies, metrics, mostEffective }: {
  strategies: StrategyRef[];
  metrics: Record<string, Metrics>;
  mostEffective?: string | null;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="th">Strategy</th>
            <th className="th">
              Attack compliance
              <div className="font-normal normal-case tracking-normal text-slate-400">lower is better</div>
            </th>
            <th className="th">
              Task accuracy
              <div className="font-normal normal-case tracking-normal text-slate-400">higher is better</div>
            </th>
            <th className="th">
              False refusal
              <div className="font-normal normal-case tracking-normal text-slate-400">lower is better</div>
            </th>
            <th className="th">
              Successful cases
              <div className="font-normal normal-case tracking-normal text-slate-400">resisted + completed</div>
            </th>
            <th className="th">
              Avg. time
              <div className="font-normal normal-case tracking-normal text-slate-400">per response</div>
            </th>
            <th className="th">Errors</th>
          </tr>
        </thead>
        <tbody>
          {strategies.map((strategy) => {
            const m = metrics[strategy.id];
            return (
              <tr key={strategy.id} className="border-b border-slate-100 last:border-0">
                <td className="td">
                  <div className="flex flex-wrap items-center gap-2 font-medium text-navy-900">
                    {strategy.short_label}. {strategy.name}
                    {mostEffective === strategy.id && <Badge tone="green" title="Lowest attack compliance rate in this data">Lowest attack compliance</Badge>}
                  </div>
                </td>
                {m ? (
                  <>
                    <td className="td">
                      <span className="font-semibold">{percent(m.attack_compliance_rate)}</span>
                      <div className="text-xs text-slate-500">
                        {m.attack_followed} of {m.attack_runs} followed
                        {m.attack_uncertain > 0 && `, ${m.attack_uncertain} uncertain`}
                      </div>
                    </td>
                    <td className="td">
                      <span className="font-semibold">{percent(m.task_accuracy)}</span>
                      <div className="text-xs text-slate-500">{m.task_completed} of {m.task_runs} completed</div>
                    </td>
                    <td className="td">
                      <span className="font-semibold">{percent(m.false_refusal_rate)}</span>
                      <div className="text-xs text-slate-500">{m.refusals} of {m.evaluated_runs} refused</div>
                    </td>
                    <td className="td">{m.successful_cases} of {m.evaluated_runs}</td>
                    <td className="td">{formatMs(m.avg_latency_ms)}</td>
                    <td className="td">{m.error_runs}</td>
                  </>
                ) : (
                  <td className="td text-slate-400" colSpan={6}>No runs for this strategy.</td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
