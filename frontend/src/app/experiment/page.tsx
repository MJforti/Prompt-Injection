"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api, type Experiment } from "@/lib/api";
import { ExperimentResults } from "@/components/ExperimentResults";
import { EmptyState, ErrorNotice, Loading, PageHeader } from "@/components/ui";

function ExperimentDetail() {
  const id = useSearchParams().get("id");
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const load = () => {
      api
        .experiment(id)
        .then((latest) => {
          if (cancelled) return;
          setExperiment(latest);
          setError(null);
          if (["pending", "running"].includes(latest.status)) timer = setTimeout(load, 800);
        })
        .catch((reason: unknown) => {
          if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not load the experiment");
        });
    };
    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  if (!id) return <EmptyState title="No experiment selected" description="Open an experiment from the Experiment History page." />;
  if (error) return <ErrorNotice message={error} />;
  if (!experiment || experiment.id !== id) return <Loading label="Loading experiment" />;
  return <ExperimentResults key={experiment.id} experiment={experiment} />;
}

export default function ExperimentPage() {
  return (
    <>
      <PageHeader
        title="Experiment Results"
        description="Exact prompts, raw responses and evaluation evidence for one stored experiment."
        actions={<Link href="/history" className="btn btn-secondary"><ArrowLeft className="h-4 w-4" /> Back to history</Link>}
      />
      <Suspense fallback={<Loading />}>
        <ExperimentDetail />
      </Suspense>
    </>
  );
}
