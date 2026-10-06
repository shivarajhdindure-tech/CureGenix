export default function Footer() {
  return (
    <footer className="mt-20 border-t border-white/[0.06]">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-8 text-xs text-slate-500 md:flex-row md:items-center md:justify-between md:px-8">
        <p className="font-medium text-slate-400">
          CureGenix · Quantum-Assisted Molecular Analysis
        </p>
        <p>
          Research prototype. Results are computational and do not establish
          clinical efficacy.
        </p>
      </div>
    </footer>
  );
}
