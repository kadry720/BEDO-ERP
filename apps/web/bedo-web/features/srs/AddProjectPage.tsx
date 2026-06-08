"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, PencilLine, Plus, Rocket, Trash2, X } from "lucide-react";
import { Button } from "@/components/Button";
import { projectRoute, routeSegment } from "@/lib/route-ids";
import type { SafeUser, TrainerItem } from "@/features/srs/types";

type TrainerDraft = {
  trainer_name: string;
  quantity: number;
  report_to_users: string[];
};

type ProjectFields = {
  project_name: string;
  project_code: string;
  end_user: string;
  po_deadline_date: string;
};

export function AddProjectPage({ reportToUsers }: { reportToUsers: SafeUser[] }) {
  const router = useRouter();
  const trainerSectionRef = useRef<HTMLElement>(null);
  const [projectId, setProjectId] = useState("");
  const [fields, setFields] = useState<ProjectFields>({ project_name: "", project_code: "", end_user: "", po_deadline_date: "" });
  const [detailsSubmitted, setDetailsSubmitted] = useState(false);
  const [savingDetails, setSavingDetails] = useState(false);
  const [trainers, setTrainers] = useState<TrainerItem[]>([]);
  const [trainerModal, setTrainerModal] = useState<TrainerItem | "new" | null>(null);
  const [quantityDraft, setQuantityDraft] = useState<TrainerDraft | null>(null);
  const [error, setError] = useState("");

  const defaultReportTo = useMemo(() => {
    const gm = reportToUsers.find((user) => user.business_role === "General Manager");
    return gm ? [gm.user] : [];
  }, [reportToUsers]);

  async function ensureProject() {
    if (projectId) {
      const response = await fetch(`/api/projects/${routeSegment(projectId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      if (!response.ok) {
        setError("Project details could not be saved.");
        return "";
      }
      return projectId;
    }
    const response = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fields),
    });
    if (!response.ok) {
      setError("Project could not be created.");
      return "";
    }
    const data = await response.json();
    setProjectId(data.project);
    return data.project as string;
  }

  async function submitProjectDetails() {
    setError("");
    setSavingDetails(true);
    try {
      const nextProjectId = await ensureProject();
      if (!nextProjectId) return;
      setDetailsSubmitted(true);
      await refreshTrainers(nextProjectId);
      window.requestAnimationFrame(() => trainerSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch {
      setError("Project details could not be saved. Check the local server and try again.");
    } finally {
      setSavingDetails(false);
    }
  }

  async function refreshTrainers(nextProjectId = projectId) {
    if (!nextProjectId) return [];
    const response = await fetch(`/api/projects/${routeSegment(nextProjectId)}/trainer-items`);
    if (!response.ok) return [];
    const data = await response.json();
    const nextTrainers = (data.trainer_items || []) as TrainerItem[];
    setTrainers(nextTrainers);
    return nextTrainers;
  }

  async function saveTrainer(payload: TrainerDraft & { separation_mode?: string }, editing?: TrainerItem) {
    setError("");
    const nextProjectId = await ensureProject();
    if (!nextProjectId) return;
    const response = await fetch(editing ? `/api/trainer-items/${routeSegment(editing.name)}` : `/api/projects/${routeSegment(nextProjectId)}/trainer-items`, {
      method: editing ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setError("Trainer item could not be saved.");
      return;
    }
    setTrainerModal(null);
    setQuantityDraft(null);
    await refreshTrainers(nextProjectId);
  }

  async function deleteTrainer(item: TrainerItem) {
    const response = await fetch(`/api/trainer-items/${routeSegment(item.name)}`, { method: "DELETE" });
    if (response.ok) await refreshTrainers();
  }

  async function releaseToSrs() {
    setError("");
    const nextProjectId = await ensureProject();
    if (!nextProjectId) return;
    const currentTrainers = await refreshTrainers(nextProjectId);
    if (!currentTrainers.length) {
      setError("Add at least one trainer item before release.");
      return;
    }
    const response = await fetch(`/api/projects/${routeSegment(nextProjectId)}/release-srs`, { method: "POST" });
    if (!response.ok) {
      setError("Project could not be released to SRS.");
      return;
    }
    router.push(projectRoute("gm", nextProjectId, "/trainers"));
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">GM Support Office</div>
        <h2 className="mt-2 text-3xl font-black text-slate-950">Add New Project</h2>
        <p className="mt-2 text-sm font-medium text-slate-600">Enter project details, add trainer items, then release the PO to SRS.</p>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-black text-slate-950">Project Details</h3>
            <p className="mt-1 text-sm font-medium text-slate-500">Submit project details first, then add trainer items.</p>
          </div>
          {detailsSubmitted && (
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              Details saved
            </span>
          )}
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <ProjectField label="Project Name" value={fields.project_name} onChange={(value) => setFields((current) => ({ ...current, project_name: value }))} />
          <ProjectField label="Project Code" value={fields.project_code} onChange={(value) => setFields((current) => ({ ...current, project_code: value }))} />
          <ProjectField label="End User" value={fields.end_user} onChange={(value) => setFields((current) => ({ ...current, end_user: value }))} />
          <ProjectField label="PO Deadline Date" type="date" value={fields.po_deadline_date} onChange={(value) => setFields((current) => ({ ...current, po_deadline_date: value }))} />
        </div>
        <div className="mt-5 flex justify-end border-t border-slate-200 pt-4">
          <Button type="button" disabled={savingDetails} onClick={submitProjectDetails}>
            <CheckCircle2 className="h-4 w-4" />
            {savingDetails ? "Saving..." : detailsSubmitted ? "Save Project Details" : "Submit Project Details"}
          </Button>
        </div>
      </div>

      {detailsSubmitted && (
        <section ref={trainerSectionRef} className="rounded-lg border border-slate-200 bg-white shadow-panel">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-5 py-4">
            <div>
              <h3 className="text-lg font-black text-slate-950">Trainer Items</h3>
              <p className="text-sm font-medium text-slate-500">{trainers.length} trainer item(s)</p>
            </div>
            <Button type="button" onClick={() => setTrainerModal("new")}>
              <Plus className="h-4 w-4" />
              Add Trainer
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-[760px] w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Trainer Name</th>
                  <th className="px-4 py-3">Quantity</th>
                  <th className="px-4 py-3">Report To</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {trainers.map((item) => (
                  <tr key={item.name}>
                    <td className="px-4 py-3 font-black text-slate-950">{item.trainer_item_name}</td>
                    <td className="px-4 py-3 text-slate-600">{item.quantity}</td>
                    <td className="px-4 py-3 text-slate-600">{item.current_responsible_name || "GM Support Office"}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <Button className="min-h-9 px-3" variant="secondary" type="button" onClick={() => setTrainerModal(item)}>
                          <PencilLine className="h-4 w-4" />
                          Edit
                        </Button>
                        <Button className="min-h-9 px-3" variant="danger" type="button" onClick={() => deleteTrainer(item)}>
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!trainers.length && <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No trainer items yet.</div>}
          </div>
          <div className="flex justify-end border-t border-slate-200 px-5 py-4">
            <Button type="button" disabled={!trainers.length} onClick={releaseToSrs}>
              <Rocket className="h-4 w-4" />
              Release PO to SRS
            </Button>
          </div>
        </section>
      )}

      {trainerModal && (
        <TrainerModal
          title={trainerModal === "new" ? "Add Trainer" : "Edit Trainer"}
          item={trainerModal === "new" ? undefined : trainerModal}
          reportToUsers={reportToUsers}
          defaultReportTo={defaultReportTo}
          onClose={() => setTrainerModal(null)}
          onSubmit={(payload) => {
            if (trainerModal === "new" && payload.quantity > 1) {
              setQuantityDraft(payload);
              return;
            }
            void saveTrainer({ ...payload, separation_mode: trainerModal === "new" ? "SINGLE" : trainerModal.separation_mode }, trainerModal === "new" ? undefined : trainerModal);
          }}
        />
      )}

      {quantityDraft && (
        <QuantityModeModal
          quantity={quantityDraft.quantity}
          onClose={() => setQuantityDraft(null)}
          onSelect={(mode) => saveTrainer({ ...quantityDraft, separation_mode: mode })}
        />
      )}
    </section>
  );
}

function ProjectField({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="text-sm font-black text-slate-800">{label}</span>
      <input
        className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        type={type}
        name={labelToFieldName(label)}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onInput={(event) => onChange(event.currentTarget.value)}
        onKeyUp={(event) => onChange(event.currentTarget.value)}
        onBlur={(event) => onChange(event.currentTarget.value)}
      />
    </label>
  );
}

function labelToFieldName(label: string) {
  return label.toLowerCase().replace(/\s+/g, "_") as keyof ProjectFields;
}

function TrainerModal({
  title,
  item,
  reportToUsers,
  defaultReportTo,
  onClose,
  onSubmit,
}: {
  title: string;
  item?: TrainerItem;
  reportToUsers: SafeUser[];
  defaultReportTo: string[];
  onClose: () => void;
  onSubmit: (payload: TrainerDraft) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <form
        className="w-full max-w-2xl rounded-lg bg-white shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          onSubmit({
            trainer_name: String(form.get("trainer_name") || "").trim(),
            quantity: Number(form.get("quantity") || 1),
            report_to_users: form.getAll("report_to_users").map(String),
          });
        }}
      >
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">Trainer Item</div>
            <h3 className="mt-1 text-xl font-black text-slate-950">{title}</h3>
          </div>
          <button className="rounded-md p-2 text-slate-500 hover:bg-slate-100" type="button" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="grid gap-4 px-6 py-5 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-black text-slate-800">Trainer Name</span>
            <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="trainer_name" defaultValue={item?.trainer_name || ""} />
          </label>
          <label className="block">
            <span className="text-sm font-black text-slate-800">Quantity</span>
            <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" min={1} step={1} name="quantity" type="number" defaultValue={item?.quantity || 1} />
          </label>
          <div className="md:col-span-2">
            <div className="text-sm font-black text-slate-800">Report To</div>
            <div className="mt-2 grid max-h-52 gap-2 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 sm:grid-cols-2">
              {reportToUsers.map((user) => (
                <label key={user.user} className="cursor-pointer">
                  <input className="peer sr-only" name="report_to_users" type="checkbox" value={user.user} defaultChecked={!item && defaultReportTo.includes(user.user)} />
                  <span className="block rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700 peer-checked:border-amber-500 peer-checked:bg-amber-50">
                    {user.full_name}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit">Save Trainer</Button>
        </div>
      </form>
    </div>
  );
}

function QuantityModeModal({ quantity, onClose, onSelect }: { quantity: number; onClose: () => void; onSelect: (mode: "COMBINED" | "SEPARATED") => void }) {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-2xl">
        <div className="border-b border-slate-200 px-6 py-5">
          <div className="text-xs font-black uppercase tracking-wide text-slate-500">Quantity Handling</div>
          <h3 className="mt-1 text-xl font-black text-slate-950">{quantity} trainer units</h3>
        </div>
        <div className="grid gap-3 px-6 py-5">
          <button className="rounded-md border border-slate-200 p-4 text-left hover:border-slate-400" type="button" onClick={() => onSelect("COMBINED")}>
            <div className="font-black text-slate-950">Combined</div>
            <div className="mt-1 text-sm text-slate-600">Create one trainer item with quantity {quantity}.</div>
          </button>
          <button className="rounded-md border border-slate-200 p-4 text-left hover:border-slate-400" type="button" onClick={() => onSelect("SEPARATED")}>
            <div className="font-black text-slate-950">Separated</div>
            <div className="mt-1 text-sm text-slate-600">Create {quantity} individual trainer items.</div>
          </button>
        </div>
        <div className="flex justify-end border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}
