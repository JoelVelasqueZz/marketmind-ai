import { useEffect, useState } from "react";
import { api } from "../api";
import type { Health } from "../types";

const MODE_INFO: Record<Health["llm_mode"], { label: string; dot: string; tooltip: string }> = {
  mock: {
    label: "Modo mock",
    dot: "bg-on-surface-variant",
    tooltip: "Respuestas deterministas por reglas fijas, sin llamadas a un LLM real.",
  },
  gemini: {
    label: "Gemini en vivo",
    dot: "bg-emerald-400",
    tooltip: "Análisis generado en tiempo real por la API de Gemini (Google).",
  },
  claude: {
    label: "Claude en vivo",
    dot: "bg-amber-400",
    tooltip: "Análisis generado en tiempo real por la API de Claude (Anthropic).",
  },
  deepseek: {
    label: "DeepSeek en vivo",
    dot: "bg-sky-400",
    tooltip: "Análisis generado en tiempo real por la API de DeepSeek.",
  },
};

export default function LlmModeBadge() {
  const [mode, setMode] = useState<Health["llm_mode"] | null>(null);

  useEffect(() => {
    api
      .getHealth()
      .then((h) => setMode(h.llm_mode))
      .catch(() => setMode(null));
  }, []);

  if (!mode) return null;
  const info = MODE_INFO[mode];

  return (
    <span
      title={info.tooltip}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-label-sm font-bold bg-surface-container border border-outline-variant text-on-surface-variant cursor-help"
    >
      <span className={`w-2 h-2 rounded-full ${info.dot}`} />
      {info.label}
    </span>
  );
}
