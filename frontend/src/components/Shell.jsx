export default function Shell({ children, fullBleed = false }) {
  return <div className={fullBleed ? "page-shell full-bleed" : "page-shell"}>{children}</div>;
}
