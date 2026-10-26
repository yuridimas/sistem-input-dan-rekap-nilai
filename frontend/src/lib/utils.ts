/**
 * Utilitas class CSS bersama bagi komponen aplikasi dan primitive UI.
 * Penggabungan Tailwind dipusatkan agar override class pemanggil konsisten.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Gabungkan class kondisional lalu selesaikan konflik utility Tailwind.
 * @param inputs Nilai class yang diterima clsx. @returns String class untuk atribut
 * className.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}