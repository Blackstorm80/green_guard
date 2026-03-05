import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Fusionne les classes CSS proprement.
 * Permet d'avoir des conditions dans tes classes (ex: bouton rouge SI erreur).
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}