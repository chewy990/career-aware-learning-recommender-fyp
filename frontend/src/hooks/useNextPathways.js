/**
 * Fetch where a learner's current skills could take them next.
 *
 * This depends on skills gained across every course and on which courses the
 * learner already holds, so it must never be read from a stored path snapshot.
 * It is recomputed whenever that live state changes.
 */
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function useNextPathways({ session, activePathway }) {
  const [nextPathways, setNextPathways] = useState([]);
  const skillsKey = JSON.stringify(session.skills || {});
  const selectedKey = (session.selectedPathways || []).join(",");
  const completedKey = (session.completedCourses || []).join(",");

  useEffect(() => {
    let cancelled = false;
    if (!activePathway) {
      setNextPathways([]);
      return undefined;
    }
    (async () => {
      try {
        const response = await apiFetch("/api/next-pathways", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_pathway: activePathway,
            selected_pathways: session.selectedPathways || [],
            completed_courses: session.completedCourses || [],
            current_skills: session.skills || {},
          }),
        });
        if (!response.ok) {
          if (!cancelled) setNextPathways([]);
          return;
        }
        const data = await response.json();
        if (!cancelled) setNextPathways(data.next_pathways || []);
      } catch {
        if (!cancelled) setNextPathways([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activePathway, skillsKey, selectedKey, completedKey]);

  return nextPathways;
}
