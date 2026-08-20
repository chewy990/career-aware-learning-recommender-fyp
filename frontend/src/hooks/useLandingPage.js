import { useEffect, useRef, useState } from "react";
import Lenis from "lenis";
import { API_BASE } from "../lib/api";

function prefersReducedMotion() {
  return window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
}

/** Enable smooth scrolling unless the operating system requests reduced motion. */
export function useSmoothScrolling() {
  useEffect(() => {
    if (prefersReducedMotion()) return undefined;

    const lenis = new Lenis({
      duration: 1,
      smoothWheel: true,
    });
    let animationFrame;
    function updateScroll(time) {
      lenis.raf(time);
      animationFrame = requestAnimationFrame(updateScroll);
    }
    animationFrame = requestAnimationFrame(updateScroll);
    return () => {
      cancelAnimationFrame(animationFrame);
      lenis.destroy();
    };
  }, []);
}

/** Observe one landing element and reveal it once without continuous scroll work. */
export function useScrollReveal(options = {}) {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setIsVisible(true);
      return undefined;
    }
    const node = ref.current;
    if (!node) return undefined;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.18, ...options },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return [ref, isVisible];
}

/** Load optional landing-page dataset counts without blocking the core interface. */
export function useDatasetStats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      try {
        const response = await fetch(
          `${API_BASE}/api/research/dataset-summary`,
        );
        if (!response.ok) {
          throw new Error("Dataset summary is unavailable.");
        }
        const data = await response.json();
        if (!cancelled) setStats(data);
      } catch {
        // The landing page remains usable while the API starts.
      }
    }
    loadStats();
    return () => {
      cancelled = true;
    };
  }, []);

  return stats;
}
