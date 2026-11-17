import { Info } from "lucide-react";

/** Shown only on the public deployment (NEXT_PUBLIC_DEMO_MODE=1). */
export function DemoBanner() {
  if (process.env.NEXT_PUBLIC_DEMO_MODE !== "1") return null;
  return (
    <div role="note" className="mb-5 flex items-start gap-3 rounded-xl border border-navy-100 bg-navy-50 px-4 py-3 text-sm text-navy-800">
      <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div>
        <span className="font-semibold">Public demo. </span>
        The real experiment results from our Milestone 2 runs with Gemma 4 (gemma-4-31b-it) are preloaded: switch the
        source to <span className="font-medium">Real LLM</span> on Overview, Strategy Comparison or Analytics, or open
        them in Experiment History. New experiments here use the mock simulator and are labelled{" "}
        <span className="font-medium">Simulated</span>; live LLM runs need an API key and run locally (see the README).
        Changes made on this demo are temporary.
      </div>
    </div>
  );
}
