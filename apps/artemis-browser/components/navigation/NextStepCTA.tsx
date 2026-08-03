import Link from "next/link";
import { getNavigationItem } from "../../lib/navigation";

export function NextStepCTA({ href }: { href: string }) {
  const item = getNavigationItem(href);
  if (!item) return null;
  return <aside className="next-step"><span>Recommended next step</span><div><h2>{item.label}</h2><p>{item.description}</p></div><Link href={href}>Continue <b aria-hidden="true">→</b></Link></aside>;
}
