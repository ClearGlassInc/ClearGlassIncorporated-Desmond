import { FooterNav } from "../navigation/FooterNav";
import { GlobalNav } from "../navigation/GlobalNav";

export function SiteShell({ children }: { children: React.ReactNode }) {
  return <><a className="skip-link" href="#main-content">Skip to content</a><GlobalNav />{children}<FooterNav /></>;
}
