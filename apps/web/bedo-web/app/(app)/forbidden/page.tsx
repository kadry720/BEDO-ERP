export default function Page() {
  return (
    <section className="rounded-md border border-gray-200 bg-white p-8 shadow-panel">
      <div className="text-xs font-semibold uppercase text-muted">403</div>
      <h1 className="mt-2 text-3xl font-bold text-ink">Forbidden</h1>
      <p className="mt-3 text-sm text-muted">Your current BEDO role does not allow access to this route.</p>
    </section>
  );
}
