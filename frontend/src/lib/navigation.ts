/** Label bersama untuk menu Courses dan breadcrumb menurut role sesi. */
export function getCourseMenuLabel(role: string): string {
  return role === "superadmin" ? "Semua Mata Kuliah" : "Mata Kuliah Saya";
}

/** Kelompok route course/class memakai menu yang sama tanpa prefix match yang ambigu. */
export function isSidebarItemActive(target: string, pathname: string): boolean {
  if (target === "/dashboard") return pathname === target;
  if (target === "/courses" && pathname.startsWith("/classes/")) return true;
  return pathname === target || pathname.startsWith(`${target}/`);
}
