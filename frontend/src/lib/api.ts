export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// ----------------------------------------------------------------------------- types
export type Category =
  | "summarization"
  | "information_extraction"
  | "question_answering"
  | "instruction_override"
  | "output_manipulation"
  | "benign";

export interface ExpectedFact {
  label: string;
  keywords: string[];
}

export interface TestCase {
  id: string;
  title: string;
  category: Category | "custom";
  user_task: string;
  document: string;
  attack_type: string | null;
  injection_text: string | null;
  attack_markers: string[];
  expected_facts: ExpectedFact[];
  expected_behavior: string;
  evaluation_criteria: string;
  pass_threshold: number;
}

export type TestCaseInput = Omit<TestCase, "id"> & { id?: string };

export interface Strategy {
  id: string;
  name: string;
  short_label: string;
  kind: "single" | "two_stage";
  description: string;
  templates: Record<string, string>;
  version: number;
  is_default?: boolean;
  updated_at?: string;
}

export interface Provider {
  id: string;
  label: string;
  simulated: boolean;
  model: string;
  available: boolean;
  unavailable_reason: string;
}

export interface Metrics {
  total_runs: number;
  evaluated_runs: number;
  error_runs: number;
  attack_runs: number;
  attack_followed: number;
  attack_resisted: number;
  attack_uncertain: number;
  attack_compliance_rate: number | null;
  task_runs: number;
  task_completed: number;
  task_accuracy: number | null;
  refusals: number;
  false_refusal_rate: number | null;
  successful_cases: number;
  avg_latency_ms: number | null;
}

export interface Message {
  role: string;
  content: string;
}

export interface Evaluation {
  evaluator: string;
  attack: {
    status: string;
    markers_checked: string[];
    matched_markers: string[];
    reporting_language: string[];
    rule: string;
  };
  task: {
    status: string;
    coverage: number | null;
    threshold: number;
    matched_facts: string[];
    missing_facts: string[];
  };
  refusal: { refused: boolean; matched_phrases: string[]; rule: string };
}

export interface Run {
  id: number;
  experiment_id: string;
  test_case_id: string;
  category: string;
  strategy_id: string;
  strategy_version: number;
  repetition: number;
  prompt: Record<string, Message[]>;
  stage1_output: string | null;
  response: string | null;
  status: "ok" | "error";
  error_type: string | null;
  error: string | null;
  latency_ms: number | null;
  attack_status: "followed" | "resisted" | "uncertain" | "not_applicable" | null;
  task_status: "completed" | "incomplete" | "not_evaluated" | null;
  fact_coverage: number | null;
  refused: boolean | null;
  evaluation: Evaluation | null;
  llm_judge: Record<string, unknown> | null;
  created_at: string;
}

export type ExperimentStatus = "pending" | "running" | "completed" | "completed_with_errors" | "failed";

export interface ExperimentSummary {
  id: string;
  name: string;
  mode: "single" | "batch";
  provider: string;
  model: string;
  simulated: boolean;
  repetitions: number;
  temperature: number;
  status: ExperimentStatus;
  total_runs: number;
  completed_runs: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  strategy_ids: string[];
  test_case_count: number;
  metrics: Metrics;
}

export interface Experiment extends Omit<ExperimentSummary, "strategy_ids" | "test_case_count" | "metrics"> {
  use_llm_judge: boolean;
  strategy_snapshot: Strategy[];
  cases_snapshot: TestCase[];
  runs: Run[];
  metrics: {
    overall: Metrics;
    by_strategy: Record<string, Metrics>;
    by_category: Record<string, Metrics>;
    most_effective_strategy: string | null;
    most_effective_rule: string;
  };
}

export interface Analytics {
  available: { real_runs: number; simulated_runs: number };
  test_case_count: number;
  experiment_count: number;
  strategies: { id: string; name: string; short_label: string }[];
  providers: string[];
  overall: Metrics;
  by_strategy: Record<string, Metrics>;
  by_category: Record<string, Metrics>;
  by_category_and_strategy: Record<string, Record<string, Metrics>>;
  most_effective_strategy: string | null;
  most_effective_rule: string;
  timeline: {
    experiment_id: string;
    name: string;
    created_at: string;
    simulated: boolean;
    metrics: Metrics;
    by_strategy: Record<string, Metrics>;
  }[];
}

export interface ExperimentRequest {
  name?: string;
  provider: string;
  strategy_ids: string[];
  test_case_ids?: string[];
  custom_case?: {
    user_task: string;
    document: string;
    attack_markers: string[];
    injection_text: string | null;
    expected_facts: ExpectedFact[];
  };
  repetitions: number;
  temperature: number;
  use_llm_judge: boolean;
}

// ----------------------------------------------------------------------------- client
export class ApiError extends Error {}

function describeDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item?.loc) ? item.loc.slice(1).join(".") : "";
        return location ? `${location}: ${item?.msg}` : String(item?.msg ?? item);
      })
      .join("; ");
  }
  return "Request failed";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      `Cannot reach the ContextShield backend at ${API_URL}. Start it with "uvicorn app.main:app --port 8000" in the backend folder.`,
    );
  }
  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status})`;
    try {
      message = describeDetail((await response.json()).detail);
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({ body: JSON.stringify(body) });

function query(parameters: Record<string, string | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(parameters)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  providers: () => request<Provider[]>("/api/providers"),

  testCases: () => request<TestCase[]>("/api/test-cases"),
  createTestCase: (body: TestCaseInput) => request<TestCase>("/api/test-cases", { method: "POST", ...json(body) }),
  updateTestCase: (id: string, body: TestCaseInput) =>
    request<TestCase>(`/api/test-cases/${encodeURIComponent(id)}`, { method: "PUT", ...json(body) }),
  deleteTestCase: (id: string) => request<void>(`/api/test-cases/${encodeURIComponent(id)}`, { method: "DELETE" }),
  importTestCases: (format: "json" | "csv", content: string, mode: "merge" | "replace") =>
    request<{ created: number; updated: number; total: number }>("/api/test-cases/import", {
      method: "POST",
      ...json({ format, content, mode }),
    }),
  resetTestCases: () => request<{ total: number }>("/api/test-cases/reset", { method: "POST" }),
  testCasesExportUrl: (format: "json" | "csv") => `${API_URL}/api/test-cases/export?format=${format}`,

  strategies: () => request<Strategy[]>("/api/strategies"),
  updateStrategy: (id: string, templates: Record<string, string>) =>
    request<Strategy>(`/api/strategies/${id}`, { method: "PUT", ...json({ templates }) }),
  resetStrategy: (id: string) => request<Strategy>(`/api/strategies/${id}/reset`, { method: "POST" }),

  // Returns only {id, status, total_runs} when the backend runs experiments in the background,
  // or the full finished Experiment when it runs them synchronously (serverless deployment).
  createExperiment: (body: ExperimentRequest) =>
    request<{ id: string; status: string; total_runs: number } & Partial<Experiment>>("/api/experiments", {
      method: "POST",
      ...json(body),
    }),
  experiments: () => request<ExperimentSummary[]>("/api/experiments"),
  experiment: (id: string) => request<Experiment>(`/api/experiments/${encodeURIComponent(id)}`),
  deleteExperiment: (id: string) => request<void>(`/api/experiments/${encodeURIComponent(id)}`, { method: "DELETE" }),
  experimentExportUrl: (id: string, format: "csv" | "json" | "pdf") =>
    `${API_URL}/api/experiments/${encodeURIComponent(id)}/export?format=${format}`,

  analytics: (filters: {
    strategy?: string;
    category?: string;
    provider?: string;
    simulated?: boolean;
    date_from?: string;
    date_to?: string;
  } = {}) => request<Analytics>(`/api/analytics${query(filters)}`),
};
