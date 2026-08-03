import { Breadcrumbs } from "../navigation/Breadcrumbs";
import { NextStepCTA } from "../navigation/NextStepCTA";
import { RelatedLinks } from "../navigation/RelatedLinks";
import { routeFlow } from "../../lib/navigation";

export function PageFlow({ route, title, eyebrow, summary, children }: { route: string; title: string; eyebrow: string; summary: string; children: React.ReactNode }) {
  const flow = routeFlow[route];
  return <main id="main-content" className="flow-page"><Breadcrumbs label={title} /><header className="flow-hero"><p className="eyebrow"><span />{eyebrow}</p><h1>{title}</h1><p className="lede">{summary}</p></header>{children}{flow && <><RelatedLinks hrefs={flow.related} /><NextStepCTA href={flow.next} /></>}</main>;
}
