import { SKILL_LEVELS, skillLevelLabel } from "../lib/session";

const DIFFICULTIES = [
  { value: 1, label: "Beginner" },
  { value: 2, label: "Intermediate" },
  { value: 3, label: "Advanced" },
];

function SkillSliderRow({ skill, session, updateSkill }) {
  return (
    <label className="skill-row">
      <span>
        <strong>{skill.label}</strong>
      </span>
      <div className="skill-slider">
        <input type="range" min="0" max="3" value={session.skills[skill.id] || 0} aria-label={`${skill.label} level`} onChange={(event) => updateSkill(skill.id, event.target.value)} />
        <div className="skill-scale" aria-hidden="true">
          {SKILL_LEVELS.map((level) => <span key={level.value}>{level.label}</span>)}
        </div>
      </div>
      <b>{skillLevelLabel(session.skills[skill.id] || 0)}</b>
    </label>
  );
}

export default function SkillStep({ pathway, unknownSkills, knownSkills, session, setSession, updateSkill, onReviewSaved, onBack, onNext }) {
  return (
    <div className="stack">
      <div className="section-heading">
        <span>Step 2</span>
        <h2>{pathway?.label || "Selected pathway"} skill check</h2>
        <p>Tell us where you are now. Saved skill levels carry across pathways.</p>
      </div>
      {knownSkills.length > 0 && (
        <div className="known-skills">
          <div className="known-skills-header">
            <h3>Saved skill levels</h3>
            <button className="text-action" type="button" onClick={onReviewSaved}>Edit saved levels</button>
          </div>
          <div className="known-skill-list">
            {knownSkills.map((skill) => (
              <div className="known-skill-item" key={skill.id}>
                <span>{skill.label}</span>
                <strong>{skillLevelLabel(session.skills[skill.id])}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
      {unknownSkills.length > 0 ? (
        <div className="skill-list">
          {unknownSkills.map((skill) => (
            <SkillSliderRow key={skill.id} skill={skill} session={session} updateSkill={updateSkill} />
          ))}
        </div>
      ) : (
        <p className="ready-note">Your saved levels are ready. Generate the course now or edit them above.</p>
      )}
      <label className="field">
        <span>Preferred course difficulty</span>
        <select value={session.preferredDifficulty} onChange={(event) => setSession({ ...session, preferredDifficulty: Number(event.target.value) })}>
          {DIFFICULTIES.map((difficulty) => <option key={difficulty.value} value={difficulty.value}>{difficulty.label}</option>)}
        </select>
        <small>Used to suggest easier or harder resources. It does not change skill progress.</small>
      </label>
      <div className="action-row">
        <button className="ghost" onClick={onBack}>Back to pathways</button>
        <button className="primary" onClick={onNext}>Generate course</button>
      </div>
    </div>
  );
}
