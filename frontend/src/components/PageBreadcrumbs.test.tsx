import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { PageBreadcrumbs } from "./PageBreadcrumbs";
import { getCourseMenuLabel } from "@/lib/navigation";

describe("page breadcrumbs", () => {
  it.each(["superadmin", "lecturer"])("matches the %s menu and marks only the current item", (role) => {
    const label = getCourseMenuLabel(role);
    render(<MemoryRouter><PageBreadcrumbs items={[
      { label, to: "/courses" },
      { label: "Pemrograman dengan nama mata kuliah yang panjang", to: "/courses/c1" },
      { label: "Kelas A (2026/2027)" },
    ]} /></MemoryRouter>);
    const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(nav).getAllByRole("listitem")).toHaveLength(3);
    expect(within(nav).getByRole("link", { name: label })).toHaveAttribute("href", "/courses");
    expect(within(nav).getByRole("link", { name: /Pemrograman/ })).toHaveAttribute("href", "/courses/c1");
    expect(within(nav).getAllByRole("link")).toHaveLength(2);
    expect(nav.querySelectorAll('[aria-current="page"]')).toHaveLength(1);
    expect(nav.querySelector('[aria-current="page"]')).toHaveTextContent("Kelas A (2026/2027)");
  });
});
