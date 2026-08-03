import Link from "next/link";
import { primaryNavigation } from "../../lib/navigation";

export function GlobalNav() {
  return (
    <header className="site-header">
      <nav className="global-nav" aria-label="Primary navigation">
        <Link className="brand" href="/" aria-label="ClearGlassInc Artemis home">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span><strong>ClearGlassInc</strong><small>ARTEMIS / INTELLIGENCE</small></span>
        </Link>
        <details className="nav-menu">
          <summary aria-label="Open navigation"><span>Explore</span><i aria-hidden="true" /></summary>
          <div className="nav-links">
            {primaryNavigation.map((item) => <Link href={item.href} key={item.href}>{item.label}</Link>)}
          </div>
        </details>
      </nav>
    </header>
  );
}
