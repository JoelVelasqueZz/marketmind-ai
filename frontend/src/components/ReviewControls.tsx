import { useState } from "react";
import type { ReviewStatus } from "../types";

interface ReviewControlsProps {
  currentStatus: ReviewStatus;
  currentJustification?: string | null;
  onSave: (status: ReviewStatus, justification: string) => Promise<void>;
}

const STATUS_OPTIONS: ReviewStatus[] = ["pending", "revisada", "escalada", "descartada"];

export const STATUS_LABEL: Record<ReviewStatus, string> = {
  pending: "Pendiente",
  revisada: "Revisada",
  escalada: "Escalada",
  descartada: "Descartada",
};

export default function ReviewControls({ currentStatus, currentJustification, onSave }: ReviewControlsProps) {
  const [status, setStatus] = useState<ReviewStatus>(currentStatus);
  const [justification, setJustification] = useState(currentJustification ?? "");
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(currentStatus === "pending");
  const [justSaved, setJustSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onSave(status, justification);
      setEditing(false);
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div className="bg-surface-container-low border border-outline-variant rounded-lg p-3">
        <div className="flex items-center justify-between gap-3 mb-1">
          <span className="text-label-sm font-bold text-on-surface uppercase">
            {STATUS_LABEL[status]}
          </span>
          <button
            className="text-label-sm font-bold text-primary hover:underline"
            onClick={() => setEditing(true)}
          >
            Editar
          </button>
        </div>
        {justification && <p className="text-body-md text-on-surface-variant">{justification}</p>}
        {justSaved && (
          <p className="text-label-sm text-success font-bold mt-2 flex items-center gap-1">
            <span className="material-symbols-outlined text-sm">check_circle</span>
            Guardado correctamente
          </p>
        )}
      </div>
    );
  }

  return (
    <div>
      <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-2">
        Observaciones del analista
      </p>
      <textarea
        className="w-full bg-surface-container-low border border-outline-variant rounded-lg p-3 text-body-md text-on-surface outline-none focus:border-primary min-h-[70px] mb-3"
        placeholder="Añadir notas técnicas…"
        value={justification}
        onChange={(e) => setJustification(e.target.value)}
      />
      <div className="flex items-center gap-3">
        <select
          className="bg-surface-variant border border-outline-variant rounded-lg px-3 py-2 text-label-md font-bold text-on-surface outline-none cursor-pointer"
          value={status}
          onChange={(e) => setStatus(e.target.value as ReviewStatus)}
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </select>
        <button
          className="px-4 py-2 bg-primary-container text-on-primary-container text-label-md font-bold rounded-lg disabled:opacity-40"
          disabled={saving || status === "pending" || justification.trim().length < 3}
          onClick={handleSave}
          title={
            justification.trim().length < 3
              ? "Escribe una justificación (HU3: toda revisión guarda su justificación)"
              : undefined
          }
        >
          {saving ? "Guardando…" : "Guardar"}
        </button>
      </div>
      {error && (
        <p className="text-label-sm text-error font-bold mt-2">
          No se pudo guardar la revisión: {error}
        </p>
      )}
    </div>
  );
}
