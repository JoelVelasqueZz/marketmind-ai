import { useState } from "react";
import type { ReviewStatus } from "../types";

interface ReviewControlsProps {
  currentStatus: ReviewStatus;
  currentJustification?: string | null;
  onSave: (status: ReviewStatus, justification: string) => Promise<void>;
}

const STATUS_OPTIONS: ReviewStatus[] = ["pending", "revisada", "escalada", "descartada"];

export default function ReviewControls({ currentStatus, currentJustification, onSave }: ReviewControlsProps) {
  const [status, setStatus] = useState<ReviewStatus>(currentStatus);
  const [justification, setJustification] = useState(currentJustification ?? "");
  const [saving, setSaving] = useState(false);

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
              {s}
            </option>
          ))}
        </select>
        <button
          className="px-4 py-2 bg-primary-container text-on-primary-container text-label-md font-bold rounded-lg disabled:opacity-40"
          disabled={saving || status === "pending"}
          onClick={async () => {
            setSaving(true);
            try {
              await onSave(status, justification);
            } finally {
              setSaving(false);
            }
          }}
        >
          {saving ? "Guardando…" : "Guardar"}
        </button>
      </div>
    </div>
  );
}
