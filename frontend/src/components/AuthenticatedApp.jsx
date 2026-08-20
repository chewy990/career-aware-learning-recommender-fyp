import AccountMenu from "./AccountMenu";
import ConfirmDialog from "./ConfirmDialog";
import CourseStep from "./CourseStep";
import Dashboard from "./Dashboard";
import PasswordStep from "./PasswordStep";
import ResearchView from "./ResearchView";
import SkillStep from "./SkillStep";

export default function AuthenticatedApp({ controller }) {
  const {
    activeCoreSkillIds,
    activePathway,
    auth,
    changePassword,
    choosePathway,
    closeConfirm,
    completeItem,
    confirmRequest,
    coreSkills,
    deletePathway,
    error,
    generateCourse,
    knownCoreSkills,
    lastUpdate,
    logout,
    meta,
    path,
    pathLoading,
    resetProgress,
    resetSkills,
    session,
    setSession,
    setSkillCheckIds,
    setStep,
    setupPathway,
    skillCheckSkills,
    step,
    switchActivePathway,
    updateSkill,
  } = controller;

  const defaultAppStep =
    session.selectedPathways.length > 0
      ? "dashboard"
      : "pathways";

  return (
    <>
      {error && <div className="error-banner">{error}</div>}

      <main className="app-grid">
        <aside className="control-panel">
          <div className="panel-brand">Career-Aware Learning</div>

          <div className="button-stack">
            <button
              className={
                step === "dashboard"
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() => setStep(defaultAppStep)}
            >
              My courses
            </button>
            <button
              className={
                step === "pathways" || step === "skills"
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() => setStep("pathways")}
            >
              Add pathway
            </button>
            <AccountMenu
              username={auth.username}
              courseCount={session.selectedPathways.length}
              completedCount={session.completedItemIds.length}
              onSecurity={() => setStep("security")}
              onResearch={() => setStep("research")}
              onAbout={() => setStep("about")}
              onHome={() => setStep("landing")}
              onResetProgress={resetProgress}
              onResetSkills={resetSkills}
              onLogout={logout}
            />
          </div>
        </aside>

        <section className="main-panel">
          {step === "pathways" && (
            <CourseStep
              pathways={meta?.pathways || []}
              hasCourses={session.selectedPathways.length > 0}
              choosePathway={choosePathway}
              onBack={() => setStep("dashboard")}
            />
          )}
          {step === "skills" && (
            <SkillStep
              pathway={setupPathway}
              unknownSkills={skillCheckSkills}
              knownSkills={knownCoreSkills}
              session={session}
              setSession={setSession}
              updateSkill={updateSkill}
              onReviewSaved={() =>
                setSkillCheckIds(
                  coreSkills.map((skill) => skill.id),
                )
              }
              onBack={() => setStep("pathways")}
              onNext={generateCourse}
            />
          )}
          {step === "dashboard" && (
            <Dashboard
              pathways={meta?.pathways || []}
              session={session}
              path={path}
              pathLoading={pathLoading}
              activeCoreSkillIds={activeCoreSkillIds}
              onSwitchPathway={switchActivePathway}
              onDeletePathway={deletePathway}
              onComplete={completeItem}
              lastUpdate={lastUpdate}
              onStartPathway={choosePathway}
            />
          )}
          {step === "research" && (
            <ResearchView
              path={path}
              session={session}
              selectedPathway={activePathway}
              coreSkillIds={activeCoreSkillIds}
              onBack={() => setStep(defaultAppStep)}
            />
          )}
          {step === "security" && (
            <PasswordStep
              onSubmit={changePassword}
              onBack={() => setStep(defaultAppStep)}
            />
          )}
        </section>
      </main>
      <ConfirmDialog request={confirmRequest} onClose={closeConfirm} />
    </>
  );
}
