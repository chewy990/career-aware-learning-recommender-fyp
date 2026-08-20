import { useScrollReveal } from "../../hooks/useLandingPage";

export function Reveal({
  as: Tag = "div",
  className = "",
  children,
}) {
  const [ref, isVisible] = useScrollReveal();
  return (
    <Tag
      ref={ref}
      className={`reveal ${isVisible ? "is-visible" : ""} ${className}`}
    >
      {children}
    </Tag>
  );
}

export function Brand() {
  return (
    <span className="brand-lockup">
      <span className="brand-mark" aria-hidden="true">
        *
      </span>
      <span>Career-Aware Learning</span>
    </span>
  );
}

export function ProductSchematic() {
  return (
    <div className="hero-schematic" aria-hidden="true">
      <div className="schematic-grid" />
      <div className="schematic-node node-goal">
        <span>Career goal</span>
        <strong>Data Analyst</strong>
      </div>
      <div className="schematic-node node-skill">
        <span>Current skill</span>
        <strong>SQL / Basic</strong>
      </div>
      <div className="schematic-node node-gap">
        <span>Priority gap</span>
        <strong>Data visualisation</strong>
      </div>
      <div className="schematic-core">
        <span className="core-spark">*</span>
        <small>Recommended next</small>
        <strong>SQL for data analysis</strong>
        <span>Beginner / 2 hours</span>
      </div>
      <div className="schematic-stage stage-one">01 / Learn</div>
      <div className="schematic-stage stage-two">02 / Build</div>
      <div className="schematic-stage stage-three">03 / Deepen</div>
    </div>
  );
}

export function TopNav({
  onStart,
  onAbout,
  onHome,
  page = "home",
}) {
  return (
    <nav className="landing-nav">
      <button
        className="brand-button"
        type="button"
        onClick={onHome}
      >
        <Brand />
      </button>
      <div className="landing-nav-actions">
        {page === "home" ? (
          <button className="nav-text-link" onClick={onAbout}>
            About
          </button>
        ) : (
          <button className="nav-text-link" onClick={onHome}>
            Home
          </button>
        )}
        <button
          className="primary landing-nav-cta"
          onClick={onStart}
        >
          Start learning
        </button>
      </div>
    </nav>
  );
}
