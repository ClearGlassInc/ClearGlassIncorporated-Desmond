import Link from "next/link";
import { getNavigationItem } from "../../lib/navigation";

export function RelatedLinks({ hrefs }: { hrefs: string[] }) {
  return (
    <section className="related-links" aria-labelledby="related-title">
      <p className="section-kicker">Continue exploring</p><h2 id="related-title">Connected system views</h2>
      <div>{hrefs.map((href) => { const item = getNavigationItem(href); return item && <Link href={href} key={href}><strong>{item.label}</strong><span>{item.description}</span><b aria-hidden="true">↗</b></Link>; })}</div>
    </section>
  );
}
