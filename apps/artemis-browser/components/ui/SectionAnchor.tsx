export function SectionAnchor({ id, label }: { id: string; label: string }) {
  return <a className="section-anchor" href={`#${id}`} aria-label={`Link to ${label}`}><span aria-hidden="true">#</span>{label}</a>;
}
