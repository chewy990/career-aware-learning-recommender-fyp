import { useEffect, useRef, useState } from "react";
import {
  ChevronDown,
  Eraser,
  FlaskConical,
  House,
  Info,
  KeyRound,
  LogOut,
  RotateCcw,
  Settings2,
} from "lucide-react";

export default function AccountMenu({
  username,
  courseCount,
  completedCount,
  onSecurity,
  onResearch,
  onAbout,
  onHome,
  onResetProgress,
  onResetSkills,
  onLogout,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;

    const closeFromOutside = (event) => {
      if (!menuRef.current?.contains(event.target)) setIsOpen(false);
    };
    const closeFromKeyboard = (event) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("pointerdown", closeFromOutside);
    document.addEventListener("keydown", closeFromKeyboard);
    return () => {
      document.removeEventListener("pointerdown", closeFromOutside);
      document.removeEventListener("keydown", closeFromKeyboard);
    };
  }, [isOpen]);

  const choose = (action) => {
    setIsOpen(false);
    action();
  };

  const initial = username?.trim().charAt(0).toUpperCase() || "U";
  const courseLabel = `${courseCount} ${
    courseCount === 1 ? "course" : "courses"
  }`;

  return (
    <div className="account-menu" ref={menuRef}>
      <button
        className="account-menu-trigger"
        type="button"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
      >
        <span className="account-menu-trigger-label">
          <Settings2 aria-hidden="true" />
          Account &amp; app
        </span>
        <ChevronDown className="account-menu-chevron" aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          className="account-menu-popover"
          role="menu"
          aria-label="Account and app"
        >
          <div className="account-menu-profile">
            <span className="account-menu-avatar" aria-hidden="true">
              {initial}
            </span>
            <span className="account-menu-profile-copy">
              <strong>{username}</strong>
              <span>
                {courseLabel} · {completedCount} completed
              </span>
            </span>
          </div>

          <div className="account-menu-group">
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onSecurity)}
            >
              <KeyRound aria-hidden="true" />
              Change password
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onResearch)}
            >
              <FlaskConical aria-hidden="true" />
              Research view
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onAbout)}
            >
              <Info aria-hidden="true" />
              About
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onHome)}
            >
              <House aria-hidden="true" />
              Home page
            </button>
          </div>

          <div className="account-menu-group account-menu-danger">
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onResetProgress)}
            >
              <RotateCcw aria-hidden="true" />
              Reset learning progress
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onResetSkills)}
            >
              <Eraser aria-hidden="true" />
              Reset skill levels
            </button>
          </div>

          <div className="account-menu-group account-menu-signout">
            <button
              type="button"
              role="menuitem"
              onClick={() => choose(onLogout)}
            >
              <LogOut aria-hidden="true" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
