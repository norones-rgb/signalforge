import { ReactNode } from "react";

export function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <section className="surface p-6 space-y-4">
      <div>
        <p className="label">{title}</p>
        {description ? <p className="mt-2 text-sm text-slate/80">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
