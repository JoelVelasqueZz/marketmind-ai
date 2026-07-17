import type { ReviewCause } from "../types";

// Taxonomía NTSB de causa raíz (debe coincidir con backend/schemas.py::ReviewCause).
export const CAUSE_LABELS: Record<ReviewCause, string> = {
  evidencia_insuficiente: "Evidencia insuficiente",
  sobre_reaccion_al_precio: "Sobre-reacción al precio",
  dato_no_soportado_por_fuente: "Dato no soportado por la fuente",
  contexto_faltante: "Contexto faltante",
  criterio_del_comite: "Criterio del Comité",
};

export const CAUSE_OPTIONS = Object.entries(CAUSE_LABELS) as [ReviewCause, string][];
