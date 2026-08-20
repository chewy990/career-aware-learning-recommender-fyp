import AuthStep from "./components/AuthStep";
import AuthenticatedApp from "./components/AuthenticatedApp";
import Shell from "./components/Shell";
import useLearningApp from "./hooks/useLearningApp";
import Landing, { AboutPage } from "./Landing";

export default function App() {
  const controller = useLearningApp();
  const {
    error,
    loading,
    meta,
    setStep,
    startLearning,
    startupStatus,
    step,
    submitAuth,
  } = controller;

  if (loading || !meta) {
    return (
      <Shell>
        <main className="startup-screen" aria-live="polite">
          {loading ? <span className="startup-spinner" aria-hidden="true" /> : null}
          <p className="startup-eyebrow">Career-aware learning recommender</p>
          <h1>{loading ? "Starting the service" : "Service unavailable"}</h1>
          <p>{loading ? startupStatus : error}</p>
          {!loading ? (
            <button className="primary" type="button" onClick={() => window.location.reload()}>
              Try again
            </button>
          ) : null}
        </main>
      </Shell>
    );
  }

  if (step === "landing") {
    return (
      <Shell fullBleed>
        <Landing
          onStart={startLearning}
          onAbout={() => setStep("about")}
        />
      </Shell>
    );
  }

  if (step === "about") {
    return (
      <Shell fullBleed>
        <AboutPage
          onStart={startLearning}
          onHome={() => setStep("landing")}
        />
      </Shell>
    );
  }

  if (step === "auth") {
    return (
      <Shell>
        <AuthStep
          notice={error}
          onSubmit={submitAuth}
          onBack={() => setStep("landing")}
        />
      </Shell>
    );
  }

  return (
    <Shell>
      <AuthenticatedApp controller={controller} />
    </Shell>
  );
}
