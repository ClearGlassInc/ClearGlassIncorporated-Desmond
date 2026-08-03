import { SectionAnchor } from "../ui/SectionAnchor";

export function SystemSection({ id, title, intro, items }: { id: string; title: string; intro: string; items: { title: string; text: string; meta?: string }[] }) {
  return <section id={id} className="system-section"><SectionAnchor id={id} label={title} /><p className="section-intro">{intro}</p><div className="system-grid">{items.map((item) => <article key={item.title}><h3>{item.title}</h3><p>{item.text}</p>{item.meta && <small>{item.meta}</small>}</article>)}</div></section>;
}
