export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200/90 bg-white/70 py-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 sm:px-6 lg:px-8 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-semibold text-slate-700">
          CureGenix &middot; Quantum-Assisted Molecular Discovery Platform
        </p>
        <p className="text-[11px] text-slate-400">
          Scientific research software. Predictions are computational hypotheses and do not replace physical laboratory validation.
        </p>
      </div>
    </footer>
  );
}
