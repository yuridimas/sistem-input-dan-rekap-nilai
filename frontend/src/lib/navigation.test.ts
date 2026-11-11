import { describe, expect, it } from "vitest";
import { getCourseMenuLabel, isSidebarItemActive } from "./navigation";

describe("course navigation context", () => {
  it("uses the role's actual menu label", () => {
    expect(getCourseMenuLabel("superadmin")).toBe("Semua Mata Kuliah");
    expect(getCourseMenuLabel("lecturer")).toBe("Mata Kuliah Saya");
  });
  it.each(["/courses", "/courses/", "/courses/c1", "/classes/k1"])("keeps Courses active at %s", (path) => {
    expect(isSidebarItemActive("/courses", path)).toBe(true);
  });
  it.each(["/courses-archive", "/classes-other", "/students/s1", "/dashboard"])("does not confuse %s with the course route", (path) => {
    expect(isSidebarItemActive("/courses", path)).toBe(false);
  });
  it("keeps dashboard exact and other menu routes segment aware", () => {
    expect(isSidebarItemActive("/dashboard", "/dashboard/x")).toBe(false);
    expect(isSidebarItemActive("/dashboard", "/dashboard")).toBe(true);
    expect(isSidebarItemActive("/students", "/students/s1")).toBe(true);
    expect(isSidebarItemActive("/students", "/students-old")).toBe(false);
  });
});
