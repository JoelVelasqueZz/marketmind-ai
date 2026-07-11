import type { Instrument } from "../types";

export interface FilterState {
  type: string;
  asset: string;
  maxAgeDays: string;
}

interface FiltersProps {
  instruments: Instrument[];
  value: FilterState;
  onChange: (next: FilterState) => void;
}

const TYPE_OPTIONS = [
  { value: "", label: "All Assets" },
  { value: "equity", label: "Equities" },
  { value: "crypto", label: "Crypto" },
  { value: "credit", label: "Credit" },
  { value: "other", label: "Other" },
];

const AGE_OPTIONS = [
  { value: "", label: "Any time" },
  { value: "1", label: "Last 24h" },
  { value: "7", label: "Last 7d" },
  { value: "30", label: "Last 30d" },
];

export default function Filters({ instruments, value, onChange }: FiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-stack-sm mb-stack-lg bg-surface-container-low p-4 rounded-xl border border-outline-variant">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-variant rounded-lg border border-outline-variant">
        <span className="text-label-sm text-on-surface-variant">Asset Type</span>
        <select
          className="bg-transparent text-label-md font-bold text-on-surface outline-none border-none p-0 cursor-pointer"
          value={value.type}
          onChange={(e) => onChange({ ...value, type: e.target.value })}
        >
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-surface-container text-on-surface">
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-variant rounded-lg border border-outline-variant">
        <span className="text-label-sm text-on-surface-variant">Asset</span>
        <select
          className="bg-transparent text-label-md font-bold text-on-surface outline-none border-none p-0 cursor-pointer"
          value={value.asset}
          onChange={(e) => onChange({ ...value, asset: e.target.value })}
        >
          <option value="" className="bg-surface-container text-on-surface">
            All
          </option>
          {instruments.map((i) => (
            <option key={i.symbol} value={i.symbol} className="bg-surface-container text-on-surface">
              {i.symbol}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-variant rounded-lg border border-outline-variant">
        <span className="text-label-sm text-on-surface-variant">Date Range</span>
        <select
          className="bg-transparent text-label-md font-bold text-on-surface outline-none border-none p-0 cursor-pointer"
          value={value.maxAgeDays}
          onChange={(e) => onChange({ ...value, maxAgeDays: e.target.value })}
        >
          {AGE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-surface-container text-on-surface">
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
