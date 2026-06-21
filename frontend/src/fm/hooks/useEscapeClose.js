import { useEffect } from "react";

/**
 * Close any modal/drawer when the user presses the Escape key.
 * Usage : useEscapeClose(open, () => setOpen(false))
 */
export function useEscapeClose(isOpen, onClose) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);
}
