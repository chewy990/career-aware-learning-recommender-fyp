import { coreSkillsForPathway } from "../lib/session";

const PATHWAY_DESCRIPTIONS = {
  data_analyst: "Turn raw data into clear reports and business decisions.",
  ml_engineer: "Build, evaluate, and deploy machine-learning systems.",
  software_developer: "Design, build, test, and maintain useful software.",
  data_scientist: "Explore data and build models that explain and predict.",
  data_engineer: "Build reliable data pipelines, databases, and platforms.",
};

export default function CourseStep({ pathways, hasCourses, choosePathway, onBack }) {
  return (
    <div className="stack">
      <div className="section-heading">
        <span>Step 1</span>
        <h2>Choose the career pathway you want to work toward.</h2>
        <p>Your current skills carry across pathways, so you only need to assess new ones.</p>
      </div>
      {hasCourses && <button className="ghost inline-action" onClick={onBack}>Back to Courses</button>}
      <div className="pathway-grid">
        {pathways.map((pathway) => (
          <button className="pathway-card" key={pathway.id} onClick={() => choosePathway(pathway.id)}>
            <span>{pathway.label}</span>
            <p>{PATHWAY_DESCRIPTIONS[pathway.id] || "Build a focused course around the skills this pathway needs."}</p>
            <small>Core skills: {coreSkillsForPathway(pathway).map((skill) => skill.label).join(" / ")}</small>
          </button>
        ))}
      </div>
    </div>
  );
}
