/**
 * Load fixed-profile research data and model metrics.
 *
 * Requests use the authenticated session but remain independent of learner state.
 */
import { useEffect, useState } from "react";
import { API_BASE, apiFetch } from "../../lib/api";

/** Return research datasets, controls, and loading/error states. */
export default function useResearchData() {
  const [profiles, setProfiles] = useState([]);
  const [profileId, setProfileId] = useState("");
  const [model, setModel] = useState("hybrid");
  const [topK, setTopK] = useState(5);
  const [recommendations, setRecommendations] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [datasetSummary, setDatasetSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    async function loadProfiles() {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/api/profiles`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Could not load research profiles.");
        const data = await response.json();
        const nextProfiles = data.profiles || [];
        setProfiles(nextProfiles);
        setProfileId((current) => current || nextProfiles[0]?.profile_id || "");
      } catch (requestError) {
        if (requestError.name === "AbortError") return;
        setError(requestError.message || "Could not load research profiles.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadProfiles();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function loadMetrics() {
      try {
        setMetricsLoading(true);
        const response = await apiFetch("/api/research/metrics", {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Could not load model metrics.");
        const data = await response.json();
        setMetrics(data.metrics || []);
      } catch (requestError) {
        if (requestError.name === "AbortError") return;
        setError(requestError.message || "Could not load model metrics.");
      } finally {
        if (!controller.signal.aborted) setMetricsLoading(false);
      }
    }
    loadMetrics();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function loadDatasetSummary() {
      try {
        const response = await fetch(`${API_BASE}/api/research/dataset-summary`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Could not load dataset summary.");
        setDatasetSummary(await response.json());
      } catch (requestError) {
        if (requestError.name === "AbortError") return;
        setError(requestError.message || "Could not load dataset summary.");
      }
    }
    loadDatasetSummary();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function loadRecommendations() {
      if (!profileId) return;
      try {
        setLoading(true);
        const response = await apiFetch("/api/research/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ profile_id: profileId, model, top_k: topK }),
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Could not load research recommendations.");
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      } catch (requestError) {
        if (requestError.name === "AbortError") return;
        setError(requestError.message || "Could not load research recommendations.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadRecommendations();
    return () => controller.abort();
  }, [profileId, model, topK]);

  return {
    datasetSummary,
    error,
    loading,
    metrics,
    metricsLoading,
    model,
    profileId,
    profiles,
    recommendations,
    setModel,
    setProfileId,
    setTopK,
    topK,
  };
}
