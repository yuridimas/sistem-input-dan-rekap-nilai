import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

/** Hierarki halaman: ancestor dapat dibuka, item terakhir menandai halaman aktif. */
export function PageBreadcrumbs({ items }: { items: readonly BreadcrumbItem[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-5 text-sm text-muted-foreground">
      <ol className="flex min-w-0 flex-wrap items-center gap-2">
        {items.map((item, index) => (
          <li className="flex min-w-0 items-center gap-2" key={item.to ?? `${index}-${item.label}`}>
            {index > 0 && <ChevronRight aria-hidden="true" className="size-3.5 shrink-0" />}
            {index === items.length - 1
              ? <span aria-current="page" className="min-w-0 text-foreground [overflow-wrap:anywhere]">{item.label}</span>
              : item.to
                ? <Link className="min-w-0 underline-offset-4 hover:underline [overflow-wrap:anywhere]" to={item.to}>{item.label}</Link>
                : <span className="min-w-0 [overflow-wrap:anywhere]">{item.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
