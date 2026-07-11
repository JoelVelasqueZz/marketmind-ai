import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

interface TopbarProps {
  placeholder?: string;
}

export default function Topbar({ placeholder = "Buscar noticias, tickers o eventos..." }: TopbarProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [value, setValue] = useState(searchParams.get("q") ?? "");

  useEffect(() => {
    setValue(searchParams.get("q") ?? "");
  }, [searchParams]);

  function runSearch() {
    const trimmed = value.trim();
    navigate(trimmed ? `/radar?q=${encodeURIComponent(trimmed)}` : "/radar");
  }

  return (
    <header className="h-16 w-[calc(100%-280px)] fixed top-0 z-40 flex items-center justify-between px-container-padding border-b border-outline-variant backdrop-blur-md bg-surface/80">
      <div className="flex items-center gap-stack-md flex-1">
        <div className="relative w-full max-w-md group">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
            search
          </span>
          <input
            className="w-full bg-surface-container border border-outline-variant rounded-lg py-2 pl-10 pr-4 text-body-md focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
            placeholder={`${placeholder} (Enter)`}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch();
            }}
          />
        </div>
      </div>
      <div className="flex items-center gap-stack-md">
        <button className="p-2 text-on-surface-variant hover:bg-surface-container-high transition-colors duration-200 rounded-full">
          <span className="material-symbols-outlined">notifications</span>
        </button>
      </div>
    </header>
  );
}
