import Link from "next/link";

export function Breadcrumbs({ label }: { label: string }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb"><ol><li><Link href="/">Artemis</Link></li><li aria-current="page">{label}</li></ol></nav>;
}
