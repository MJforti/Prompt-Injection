export const CATEGORY_LABELS: Record<string, string> = {
  summarization: "Summarization attack",
  information_extraction: "Information extraction attack",
  question_answering: "Question-answering attack",
  instruction_override: "Instruction override",
  output_manipulation: "Output manipulation",
  benign: "Benign (no attack)",
  custom: "Custom input",
};

export const CATEGORY_SHORT: Record<string, string> = {
  summarization: "Summarization",
  information_extraction: "Extraction",
  question_answering: "Q&A",
  instruction_override: "Override",
  output_manipulation: "Output manip.",
  benign: "Benign",
  custom: "Custom",
};

export const CATEGORIES = [
  "summarization",
  "information_extraction",
  "question_answering",
  "instruction_override",
  "output_manipulation",
  "benign",
] as const;

export const METRIC_COLORS = {
  attack: "#c2410c",
  task: "#1d4ed8",
  refusal: "#6d28d9",
};

export const STRATEGY_COLORS = ["#0f1f3d", "#2563eb", "#0d9488", "#d97706", "#7c3aed", "#be123c"];

export function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? "n/a" : `${value}%`;
}

export function humanize(value: string | null | undefined): string {
  if (!value) return "none";
  return value.replace(/_/g, " ");
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "n/a";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMs(value: number | null | undefined): string {
  if (value === null || value === undefined) return "n/a";
  return value >= 1000 ? `${(value / 1000).toFixed(2)} s` : `${value.toFixed(1)} ms`;
}
