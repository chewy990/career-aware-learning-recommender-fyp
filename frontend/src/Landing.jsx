import {
  LEARNING_PROVIDERS,
  LEARNING_STAGES,
  PATHWAY_LABELS,
  PRODUCT_FEATURES,
} from "./content/landingContent";
import {
  Brand,
  ProductSchematic,
  Reveal,
  TopNav,
} from "./components/landing/LandingUi";
import {
  useDatasetStats,
  useSmoothScrolling,
} from "./hooks/useLandingPage";

export default function Landing({ onStart, onAbout }) {
  useSmoothScrolling();
  const stats = useDatasetStats();

  return (
    <div className="landing">
      <TopNav onStart={onStart} onAbout={onAbout} page="home" />

      <header className="landing-hero">
        <ProductSchematic />
        <div className="landing-hero-copy">
          <span className="hero-kicker">Career-aware course planning</span>
          <h1>Learn what your career needs. Skip what it does not.</h1>
          <p>
            Choose a pathway, check your current skills, and get a practical course
            assembled in the right order from trusted learning platforms.
          </p>
          <button className="primary hero-cta" onClick={onStart}>Build my learning path</button>
        </div>
        <div className="hero-facts" aria-label="Product summary">
          <span><strong>{stats?.pathways || 5}</strong> pathways</span>
          <span><strong>4</strong> learning stages</span>
          <span><strong>1</strong> clear next step</span>
        </div>
      </header>

      <section className="provider-band" aria-label="Learning resource providers">
        <p>Recommendations link to trusted learning platforms</p>
        <div className="provider-row">
          {LEARNING_PROVIDERS.slice(0, 7).map((source) => <span key={source}>{source}</span>)}
        </div>
      </section>

      <section className="landing-band light-band product-intro">
        <Reveal className="band-heading">
          <span className="eyebrow">A focused course, not another catalogue</span>
          <h2>One pathway built around what you already know.</h2>
          <p>
            Most platforms give every learner the same long list. This recommender
            starts with your career goal and removes the material you do not need yet.
          </p>
        </Reveal>
        <div className="feature-grid">
          {PRODUCT_FEATURES.map((feature) => (
            <Reveal as="article" className="feature-card" key={feature.title}>
              <span className="feature-number">{feature.number}</span>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="landing-band dark-band stages-band">
        <Reveal className="band-heading">
          <span className="eyebrow">Your course structure</span>
          <h2>Get practical sooner.</h2>
          <p>Four stages keep the path useful without turning it into a rigid full career track.</p>
        </Reveal>
        <div className="stage-roadmap">
          {LEARNING_STAGES.map((stage, index) => (
            <Reveal as="article" className="stage-roadmap-item" key={stage.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{stage.title}</h3>
              <p>{stage.description}</p>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="landing-band light-band showcase-band">
        <Reveal className="band-heading">
          <span className="eyebrow">The product</span>
          <h2>See the recommendation. See the reasoning.</h2>
        </Reveal>
        <div className="showcase-grid">
          <Reveal as="figure" className="showcase-frame">
            <img src="/screenshot-dashboard.png" alt="Generated pathway course with progress and recommended next step" />
            <figcaption>
              <strong>Your course</strong>
              <span>Switch pathways, continue the next resource, and track progress without losing context.</span>
            </figcaption>
          </Reveal>
          <Reveal as="figure" className="showcase-frame">
            <img src="/screenshot-research.png" alt="Research view explaining recommendation choices and model evidence" />
            <figcaption>
              <strong>Research view</strong>
              <span>Inspect why each resource was selected and keep technical evidence available when needed.</span>
            </figcaption>
          </Reveal>
        </div>
      </section>

      <section className="landing-band light-band pathway-band">
        <Reveal className="pathway-copy">
          <span className="eyebrow">Choose a direction</span>
          <h2>Five pathways. One shared skill profile.</h2>
          <p>Your saved levels carry across courses, so each new pathway starts with less setup.</p>
        </Reveal>
        <Reveal className="pathway-list">
          {PATHWAY_LABELS.map((pathway, index) => (
            <div key={pathway}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{pathway}</strong>
            </div>
          ))}
        </Reveal>
      </section>

      <section className="landing-band dark-band closing-band">
        <div className="closing-grid" aria-hidden="true" />
        <Reveal className="closing-copy">
          <Brand />
          <h2>Your next course should start with your next useful skill.</h2>
          <p>Pick a career pathway and turn your current skills into a clear place to begin.</p>
          <button className="primary" onClick={onStart}>Build my learning path</button>
        </Reveal>
      </section>
    </div>
  );
}

export function AboutPage({ onStart, onHome }) {
  return (
    <div className="about-page">
      <TopNav onStart={onStart} onHome={onHome} page="about" />

      <main className="about-page-main">
        <section className="about-page-hero">
          <div className="about-page-copy">
            <h1>Too many platforms tell learners to start with everything.</h1>
            <p>
              Course catalogues are good at offering choice. They are less helpful when a
              learner still has to translate a career goal into the right first skill,
              resource, and project.
            </p>
          </div>
          <aside className="about-stance">
            <span>One focused question</span>
            <p>What is the most useful thing for this learner to study next?</p>
          </aside>
        </section>

        <section className="about-narrative">
          <div className="about-story">
            <p>
              The concern is not that learners have too little material. It is that the
              burden of sequencing that material still falls on them. A job title can imply
              dozens of skills, and two people aiming for the same role may need very
              different starting points.
            </p>
            <p>
              Long career tracks can also create a false finish line: study everything
              first, then begin practical work. That delay makes progress harder to feel
              and gives new knowledge less context.
            </p>
          </div>
          <div className="about-principles">
            <article>
              <span>01</span>
              <div>
                <strong>Reduce the decision load</strong>
                <p>Show a clear next step instead of asking learners to compare an entire catalogue.</p>
              </div>
            </article>
            <article>
              <span>02</span>
              <div>
                <strong>Preserve what the learner already knows</strong>
                <p>Carry saved skill levels across pathways so changing direction does not mean starting over.</p>
              </div>
            </article>
            <article>
              <span>03</span>
              <div>
                <strong>Make recommendations inspectable</strong>
                <p>Keep the reasoning available so relevance can be understood, questioned, and improved.</p>
              </div>
            </article>
          </div>
        </section>

        <section className="about-note">
          <h2>Note:</h2>
          <div className="about-note-content">
            <p>
              Career-Aware Learning sits between a learner's goal and the platforms that
              teach the material. It does not host courses, issue certificates, or replace
              instructors. Its role is narrower: help someone decide what is worth learning
              next, then send them to the original provider.
            </p>
            <button className="primary" onClick={onStart}>Try the recommender</button>
          </div>
        </section>
      </main>
    </div>
  );
}
