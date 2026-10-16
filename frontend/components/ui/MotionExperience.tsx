"use client";

import { useEffect } from "react";

// Delegate to the document so asynchronously loaded group cards work too.
const surfaces = ".live-group-tabs > button, .home-side-card:not(.home-quick-links)";

export default function MotionExperience() {
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: no-preference) and (hover: hover) and (pointer: fine)");
    let active: HTMLElement | null = null;
    let frame = 0;
    let x = 0;
    let y = 0;
    const reset = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      if (active) {
        active.removeAttribute("data-depth-active");
        ["--depth-x", "--depth-y"].forEach(key => active?.style.removeProperty(key));
        active = null;
      }
    };
    const move = (event: PointerEvent) => {
      if (!preference.matches || event.pointerType !== "mouse") return;
      const target = event.target instanceof Element ? event.target.closest<HTMLElement>(surfaces) : null;
      if (!target || target.matches(":disabled")) { reset(); return; }
      if (active !== target) { reset(); active = target; }
      x = event.clientX;
      y = event.clientY;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        if (!active?.isConnected) { reset(); return; }
        const rect = active.getBoundingClientRect();
        const horizontal = Math.max(-.5, Math.min(.5, (x - rect.left) / Math.max(1, rect.width) - .5));
        const vertical = Math.max(-.5, Math.min(.5, (y - rect.top) / Math.max(1, rect.height) - .5));
        active.style.setProperty("--depth-x", `${-vertical * 5}deg`);
        active.style.setProperty("--depth-y", `${horizontal * 5}deg`);
        active.setAttribute("data-depth-active", "true");
      });
    };
    document.addEventListener("pointermove", move, { passive: true });
    document.documentElement.addEventListener("pointerleave", reset);
    window.addEventListener("blur", reset);
    window.addEventListener("scroll", reset, { passive: true, capture: true });
    preference.addEventListener("change", reset);
    return () => {
      reset();
      document.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", reset);
      window.removeEventListener("blur", reset);
      window.removeEventListener("scroll", reset, true);
      preference.removeEventListener("change", reset);
    };
  }, []);
  return null;
}
