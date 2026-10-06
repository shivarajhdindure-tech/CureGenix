"use client";

import { useRef, useState } from "react";
import { fmtBytes } from "@/lib/analysis";

function Spinner() {
  return (
    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
  );
}

export default function UploadPanel({ file, validation, onSelect, onRemove, onStart, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const checking = validation?.status === "checking";
  const valid = validation?.status === "valid";
  const invalid = validation?.status === "invalid";

  function openPicker() {
    inputRef.current?.click();
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped) onSelect(dropped);
  }

  return (
    <div className="panel p-6 shadow-glow md:p-8" id="upload">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-white">
            Upload Protein Structure
          </h2>
          <p className="mt-1.5 text-sm text-slate-400">
            Supported format: PDB (.pdb)
          </p>
        </div>
        <span className="badge border-cyan-400/30 bg-cyan-400/10 text-cyan-300">PDB</span>
      </div>

      {!file ? (
        <div
          role="button"
          tabIndex={0}
          aria-label="Choose a PDB file. Click or press Enter to browse, or drag and drop."
          onClick={openPicker}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPicker();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`mt-6 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-12 text-center transition focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 ${
            dragging
              ? "border-cyan-300 bg-cyan-400/10"
              : "border-white/15 bg-ink-900/50 hover:border-cyan-400/50 hover:bg-cyan-400/[0.04]"
          }`}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" className="text-cyan-300/80" aria-hidden="true">
            <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="mt-4 text-sm font-medium text-slate-100">
            Drag and drop your PDB file here
          </p>
          <p className="mt-1 text-xs text-slate-400">or</p>
          <span className="btn-ghost mt-3">Browse files</span>
        </div>
      ) : (
        <div
          className={`mt-6 rounded-2xl border p-4 ${
            invalid
              ? "border-red-400/40 bg-red-500/[0.06]"
              : valid
                ? "border-emerald-400/30 bg-emerald-400/[0.05]"
                : "border-white/10 bg-ink-900/50"
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] font-data text-[11px] font-semibold text-cyan-300">
              PDB
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white" title={file.name}>
                {file.name}
              </p>
              <p className="font-data mt-0.5 text-xs text-slate-400">{fmtBytes(file.size)}</p>
            </div>
            <button
              type="button"
              onClick={onRemove}
              disabled={disabled}
              aria-label={`Remove ${file.name}`}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/[0.07] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 disabled:opacity-40"
            >
              Remove
            </button>
          </div>

          <p
            role="status"
            className={`mt-3 flex items-center gap-2 text-xs ${
              invalid ? "text-red-300" : valid ? "text-emerald-300" : "text-slate-400"
            }`}
          >
            {checking && <Spinner />}
            {valid && <span aria-hidden="true">✓</span>}
            {invalid && <span aria-hidden="true">✕</span>}
            {checking ? "Validating file…" : validation?.message}
          </p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept=".pdb"
        className="sr-only"
        tabIndex={-1}
        onChange={(e) => {
          const selected = e.target.files?.[0];
          if (selected) onSelect(selected);
          e.target.value = "";
        }}
      />

      <button
        type="button"
        onClick={onStart}
        disabled={!valid || disabled}
        className="btn-primary mt-6 w-full"
      >
        Start Molecular Analysis
      </button>
      <p className="mt-3 text-center text-xs text-slate-500">
        A full run typically takes several minutes.
      </p>
    </div>
  );
}
