interface DisclaimerProps {
  text?: string;
}

const DEFAULT_TEXT =
  "Este contenido es informativo, no constituye asesoría financiera personalizada y no garantiza resultados.";

export default function Disclaimer({ text = DEFAULT_TEXT }: DisclaimerProps) {
  return (
    <div className="flex items-start gap-2 bg-surface-container-low border border-outline-variant rounded-lg px-4 py-3 text-label-md text-label-md text-on-surface-variant">
      <span className="material-symbols-outlined text-sm text-warning">info</span>
      <span>{text}</span>
    </div>
  );
}
