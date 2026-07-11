import { Link } from "react-router-dom";

const CARDS = [
  { to: "/radar", title: "News Radar", desc: "HU1 · Noticias por activo, sector o tema", icon: "analytics" },
  { to: "/analysis", title: "AI Analysis", desc: "HU2 · Señal explicable de impacto", icon: "psychology" },
  { to: "/briefings", title: "Briefings", desc: "HU3 · Revisión humana y tareas", icon: "description" },
];

export default function Dashboard() {
  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <h2 className="font-display-md text-display-md text-on-surface font-bold mb-2">
        Financial Market Intelligence
      </h2>
      <p className="text-body-lg text-on-surface-variant mb-stack-lg">
        Monitorea noticias, analiza impacto y genera briefings con IA para revisión humana — Track 5.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {CARDS.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className="flex flex-col gap-3 bg-surface-container border border-outline-variant rounded-xl p-5 hover:border-primary transition-colors"
          >
            <span className="material-symbols-outlined text-primary text-3xl">{c.icon}</span>
            <h3 className="font-headline-md text-headline-md text-on-surface">{c.title}</h3>
            <p className="text-body-md text-on-surface-variant">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
