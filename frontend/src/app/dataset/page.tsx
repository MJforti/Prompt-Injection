"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { Download, Eye, Pencil, Play, Plus, RotateCcw, Trash2, Upload } from "lucide-react";
import { api, type Category, type TestCase, type TestCaseInput } from "@/lib/api";
import { CATEGORIES, CATEGORY_LABELS, CATEGORY_SHORT, humanize } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { Badge, Card, DocumentView, EmptyState, ErrorNotice, Loading, Modal, PageHeader } from "@/components/ui";

interface FormState {
  id: string;
  title: string;
  category: Category;
  user_task: string;
  document: string;
  attack_type: string;
  injection_text: string;
  attack_markers: string;
  expected_facts: string;
  expected_behavior: string;
  evaluation_criteria: string;
  pass_threshold: string;
}

const EMPTY_FORM: FormState = {
  id: "", title: "", category: "summarization", user_task: "", document: "", attack_type: "", injection_text: "",
  attack_markers: "", expected_facts: "", expected_behavior: "", evaluation_criteria: "", pass_threshold: "0.67",
};

function toForm(testCase: TestCase): FormState {
  return {
    id: testCase.id,
    title: testCase.title,
    category: testCase.category as Category,
    user_task: testCase.user_task,
    document: testCase.document,
    attack_type: testCase.attack_type ?? "",
    injection_text: testCase.injection_text ?? "",
    attack_markers: testCase.attack_markers.join("\n"),
    expected_facts: testCase.expected_facts.map((fact) => `${fact.label} :: ${fact.keywords.join(", ")}`).join("\n"),
    expected_behavior: testCase.expected_behavior,
    evaluation_criteria: testCase.evaluation_criteria,
    pass_threshold: String(testCase.pass_threshold),
  };
}

function fromForm(form: FormState): TestCaseInput {
  const benign = form.category === "benign";
  return {
    ...(form.id.trim() ? { id: form.id.trim() } : {}),
    title: form.title.trim(),
    category: form.category,
    user_task: form.user_task.trim(),
    document: form.document,
    attack_type: benign ? null : form.attack_type.trim() || null,
    injection_text: benign ? null : form.injection_text.trim() || null,
    attack_markers: benign ? [] : form.attack_markers.split("\n").map((marker) => marker.trim()).filter(Boolean),
    expected_facts: form.expected_facts
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [label, keywords] = line.split("::");
        return { label: label.trim(), keywords: (keywords ?? label).split(",").map((keyword) => keyword.trim()).filter(Boolean) };
      }),
    expected_behavior: form.expected_behavior.trim(),
    evaluation_criteria: form.evaluation_criteria.trim(),
    pass_threshold: Number(form.pass_threshold) || 0.67,
  };
}

function CaseForm({ initial, editingId, onSaved, onClose }: { initial: FormState; editingId: string | null; onSaved: () => void; onClose: () => void }) {
  const [form, setForm] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = (key: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((current) => ({ ...current, [key]: event.target.value }));
  const benign = form.category === "benign";

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editingId) await api.updateTestCase(editingId, fromForm(form));
      else await api.createTestCase(fromForm(form));
      onSaved();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save the test case");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={editingId ? `Edit ${editingId}` : "Add test case"} onClose={onClose} wide>
      <form onSubmit={save} className="grid gap-4 md:grid-cols-2">
        <p className="rounded-lg bg-navy-50 px-3 py-2 text-xs text-navy-800 md:col-span-2">
          Use synthetic content only. Do not paste real confidential documents or personal information.
        </p>
        <div>
          <label className="label" htmlFor="tc-title">Title</label>
          <input id="tc-title" className="input" required value={form.title} onChange={set("title")} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="tc-id">Test ID</label>
            <input id="tc-id" className="input" value={form.id} onChange={set("id")} disabled={!!editingId} placeholder="auto (TC-0xx)" pattern="[A-Za-z0-9_\-]{1,40}" />
          </div>
          <div>
            <label className="label" htmlFor="tc-category">Category</label>
            <select id="tc-category" className="input" value={form.category} onChange={set("category")}>
              {CATEGORIES.map((category) => <option key={category} value={category}>{CATEGORY_LABELS[category]}</option>)}
            </select>
          </div>
        </div>
        <div className="md:col-span-2">
          <label className="label" htmlFor="tc-task">User task</label>
          <input id="tc-task" className="input" required value={form.user_task} onChange={set("user_task")} />
        </div>
        <div className="md:col-span-2">
          <label className="label" htmlFor="tc-document">Document content (include the injected instruction for attack cases)</label>
          <textarea id="tc-document" className="input min-h-32 font-mono text-xs" required value={form.document} onChange={set("document")} />
        </div>
        {!benign && (
          <>
            <div>
              <label className="label" htmlFor="tc-attack-type">Attack type</label>
              <input id="tc-attack-type" className="input" value={form.attack_type} onChange={set("attack_type")} placeholder="e.g. direct_override" />
            </div>
            <div>
              <label className="label" htmlFor="tc-markers">Attack markers (one per line, required)</label>
              <textarea id="tc-markers" className="input min-h-16 font-mono text-xs" value={form.attack_markers} onChange={set("attack_markers")} placeholder="Text that appears only if the injection was obeyed" />
            </div>
            <div className="md:col-span-2">
              <label className="label" htmlFor="tc-injection">Injected instruction (exact text as it appears in the document)</label>
              <textarea id="tc-injection" className="input min-h-16 font-mono text-xs" value={form.injection_text} onChange={set("injection_text")} />
            </div>
          </>
        )}
        <div className="md:col-span-2">
          <label className="label" htmlFor="tc-facts">Expected legitimate information (one fact per line)</label>
          <textarea id="tc-facts" className="input min-h-24 font-mono text-xs" value={form.expected_facts} onChange={set("expected_facts")} placeholder={"Reading rooms remain open until 11 PM :: 11 PM|23:00\nFact sentence :: keyword one, keyword two"} />
          <p className="mt-1 text-xs text-slate-500">Format: <code>fact sentence :: keyword, keyword</code>. All keywords must appear in a correct answer; use <code>|</code> for alternatives.</p>
        </div>
        <div>
          <label className="label" htmlFor="tc-behavior">Expected correct behaviour</label>
          <textarea id="tc-behavior" className="input min-h-16 text-xs" value={form.expected_behavior} onChange={set("expected_behavior")} />
        </div>
        <div>
          <label className="label" htmlFor="tc-criteria">Evaluation criteria (notes)</label>
          <textarea id="tc-criteria" className="input min-h-16 text-xs" value={form.evaluation_criteria} onChange={set("evaluation_criteria")} />
        </div>
        <div>
          <label className="label" htmlFor="tc-threshold">Pass threshold (share of facts, 0 to 1)</label>
          <input id="tc-threshold" type="number" min={0} max={1} step={0.01} className="input" value={form.pass_threshold} onChange={set("pass_threshold")} />
        </div>
        {error && <div className="md:col-span-2"><ErrorNotice message={error} /></div>}
        <div className="flex justify-end gap-2 md:col-span-2">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Saving…" : "Save test case"}</button>
        </div>
      </form>
    </Modal>
  );
}

export default function DatasetPage() {
  const cases = useApi(() => api.testCases(), "cases");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [viewing, setViewing] = useState<TestCase | null>(null);
  const [editing, setEditing] = useState<{ form: FormState; id: string | null } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [importMode, setImportMode] = useState<"merge" | "replace">("merge");
  const fileInput = useRef<HTMLInputElement | null>(null);

  const act = async (action: () => Promise<string>) => {
    setActionError(null);
    setNotice(null);
    try {
      setNotice(await action());
      cases.reload();
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Action failed");
    }
  };

  const remove = (testCase: TestCase) => {
    if (!window.confirm(`Delete ${testCase.id} (${testCase.title})? Stored experiment results keep their own snapshot.`)) return;
    void act(async () => {
      await api.deleteTestCase(testCase.id);
      return `Deleted ${testCase.id}.`;
    });
  };

  const importFile = async (file: File) => {
    const format = file.name.toLowerCase().endsWith(".csv") ? "csv" : "json";
    if (importMode === "replace" && !window.confirm("Replace the entire dataset with the contents of this file?")) return;
    const content = await file.text();
    void act(async () => {
      const result = await api.importTestCases(format, content, importMode);
      return `Imported ${result.total} test cases from ${file.name} (${result.created} new, ${result.updated} updated).`;
    });
  };

  const reset = () => {
    if (!window.confirm("Replace the current dataset with the 24 bundled default test cases? Your added or edited cases will be removed.")) return;
    void act(async () => {
      const result = await api.resetTestCases();
      return `Restored the default dataset (${result.total} test cases).`;
    });
  };

  const filtered = (cases.data ?? []).filter((testCase) => {
    const text = `${testCase.id} ${testCase.title} ${testCase.user_task} ${testCase.attack_type ?? ""}`.toLowerCase();
    return (!category || testCase.category === category) && text.includes(search.toLowerCase());
  });

  return (
    <>
      <PageHeader
        title="Test Dataset"
        description="Synthetic test cases: documents with embedded malicious instructions across five attack categories, plus benign documents that measure false refusals."
        actions={
          <>
            <a className="btn btn-secondary" href={api.testCasesExportUrl("json")}><Download className="h-4 w-4" /> JSON</a>
            <a className="btn btn-secondary" href={api.testCasesExportUrl("csv")}><Download className="h-4 w-4" /> CSV</a>
            <button type="button" className="btn btn-primary" onClick={() => setEditing({ form: EMPTY_FORM, id: null })}><Plus className="h-4 w-4" /> Add test case</button>
          </>
        }
      />

      {cases.error && <ErrorNotice message={cases.error} onRetry={cases.reload} />}
      {!cases.error && !cases.data && <Loading label="Loading dataset" />}
      {actionError && <div className="mb-4"><ErrorNotice message={actionError} /></div>}
      {notice && <div role="status" className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">{notice}</div>}

      {cases.data && (
        <Card>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <input className="input w-56" placeholder="Search id, title, task…" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search test cases" />
            <select className="input w-auto" value={category} onChange={(event) => setCategory(event.target.value)} aria-label="Filter by category">
              <option value="">All categories ({cases.data.length})</option>
              {CATEGORIES.map((option) => (
                <option key={option} value={option}>{CATEGORY_LABELS[option]} ({cases.data!.filter((testCase) => testCase.category === option).length})</option>
              ))}
            </select>
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <select className="input w-auto" value={importMode} onChange={(event) => setImportMode(event.target.value as "merge" | "replace")} aria-label="Import mode">
                <option value="merge">Import: merge by ID</option>
                <option value="replace">Import: replace dataset</option>
              </select>
              <input ref={fileInput} type="file" accept=".json,.csv" className="hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importFile(file); event.target.value = ""; }} />
              <button type="button" className="btn btn-secondary" onClick={() => fileInput.current?.click()}><Upload className="h-4 w-4" /> Import CSV/JSON</button>
              <button type="button" className="btn btn-secondary" onClick={reset}><RotateCcw className="h-4 w-4" /> Restore defaults</button>
            </div>
          </div>

          {filtered.length === 0 ? (
            <EmptyState title="No test cases match" description={cases.data.length === 0 ? "The dataset is empty. Add a test case, import a file, or restore the default dataset." : "Try a different category or search term."} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px]">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="th">ID</th>
                    <th className="th">Title and task</th>
                    <th className="th">Category</th>
                    <th className="th">Attack type</th>
                    <th className="th">Facts</th>
                    <th className="th text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((testCase) => (
                    <tr key={testCase.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      <td className="td whitespace-nowrap font-mono text-xs">{testCase.id}</td>
                      <td className="td">
                        <div className="font-medium text-navy-900">{testCase.title}</div>
                        <div className="max-w-md truncate text-xs text-slate-500">{testCase.user_task}</div>
                      </td>
                      <td className="td"><Badge tone={testCase.category === "benign" ? "slate" : "navy"}>{CATEGORY_SHORT[testCase.category]}</Badge></td>
                      <td className="td text-xs">{humanize(testCase.attack_type)}</td>
                      <td className="td">{testCase.expected_facts.length}</td>
                      <td className="td">
                        <div className="flex justify-end gap-1">
                          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setViewing(testCase)} aria-label={`Inspect ${testCase.id}`}><Eye className="h-3.5 w-3.5" /> Inspect</button>
                          <Link className="btn btn-secondary btn-sm" href={`/run?case=${testCase.id}`} aria-label={`Run ${testCase.id}`}><Play className="h-3.5 w-3.5" /> Run</Link>
                          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setEditing({ form: toForm(testCase), id: testCase.id })} aria-label={`Edit ${testCase.id}`}><Pencil className="h-3.5 w-3.5" /></button>
                          <button type="button" className="btn btn-danger btn-sm" onClick={() => remove(testCase)} aria-label={`Delete ${testCase.id}`}><Trash2 className="h-3.5 w-3.5" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {viewing && (
        <Modal title={`${viewing.id}: ${viewing.title}`} onClose={() => setViewing(null)} wide>
          <div className="space-y-4 text-sm">
            <div className="flex flex-wrap gap-1.5">
              <Badge tone="navy">{CATEGORY_LABELS[viewing.category]}</Badge>
              <Badge tone="slate">Attack type: {humanize(viewing.attack_type)}</Badge>
              <Badge tone="slate">Pass threshold: {Math.round(viewing.pass_threshold * 100)}% of facts</Badge>
            </div>
            <div><div className="label">User task</div><div className="codeblock">{viewing.user_task}</div></div>
            <div>
              <div className="label">Document content {viewing.injection_text && <span className="normal-case text-red-700">(embedded instruction highlighted)</span>}</div>
              <DocumentView text={viewing.document} injection={viewing.injection_text} />
            </div>
            {viewing.attack_markers.length > 0 && (
              <div><div className="label">Attack markers (evidence of compliance)</div><div className="codeblock">{viewing.attack_markers.join("\n")}</div></div>
            )}
            <div>
              <div className="label">Expected legitimate information</div>
              <ul className="space-y-1.5">
                {viewing.expected_facts.map((fact) => (
                  <li key={fact.label} className="rounded-lg border border-slate-200 px-3 py-2">
                    {fact.label}
                    <div className="mt-0.5 font-mono text-xs text-slate-500">keywords: {fact.keywords.join(" + ")}</div>
                  </li>
                ))}
                {viewing.expected_facts.length === 0 && <li className="text-slate-500">None defined; the task will not be evaluated.</li>}
              </ul>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div><div className="label">Expected correct behaviour</div><p className="text-slate-600">{viewing.expected_behavior || "Not specified."}</p></div>
              <div><div className="label">Evaluation criteria</div><p className="text-slate-600">{viewing.evaluation_criteria || "Not specified."}</p></div>
            </div>
          </div>
        </Modal>
      )}

      {editing && (
        <CaseForm
          initial={editing.form}
          editingId={editing.id}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setNotice(editing.id ? `Saved ${editing.id}.` : "Test case added.");
            setEditing(null);
            cases.reload();
          }}
        />
      )}
    </>
  );
}
