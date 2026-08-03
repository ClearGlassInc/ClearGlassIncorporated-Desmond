import Link from "next/link";
import { primaryNavigation } from "../../lib/navigation";

export function FooterNav() {
  return (
    <footer className="site-footer">
      <div><strong>ClearGlassInc Artemis</strong><p>Human-governed intelligence for secure, coalition-aware operations.</p></div>
      <nav aria-label="Footer navigation">{primaryNavigation.map((item) => <Link href={item.href} key={item.href}>{item.label}</Link>)}</nav>
      <p className="footer-note">Target-state reference architecture · consequential actions always require explicit authority.</p>
    </footer>
  );
}
