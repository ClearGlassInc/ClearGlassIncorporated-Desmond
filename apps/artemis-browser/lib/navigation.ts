export type NavigationItem = {
  href: string;
  label: string;
  description: string;
};

export const primaryNavigation: NavigationItem[] = [
  { href: "/", label: "Overview", description: "The Artemis browser intelligence workspace." },
  { href: "/architecture", label: "Architecture", description: "Trust domains, runtime planes, and platform topology." },
  { href: "/ontology", label: "Ontology", description: "Temporal entities, evidence, lineage, and mission context." },
  { href: "/agents", label: "Agents", description: "Bounded copilots, typed tools, and approval-gated workflows." },
  { href: "/learning", label: "Learning loop", description: "Evaluations, reviewed improvements, and safe rollback." },
  { href: "/governance", label: "Governance", description: "Zero-trust policy, coalition boundaries, and auditability." },
];

export const routeFlow: Record<string, { related: string[]; next: string }> = {
  "/": { related: ["/architecture", "/agents", "/governance"], next: "/architecture" },
  "/architecture": { related: ["/ontology", "/agents", "/governance"], next: "/ontology" },
  "/ontology": { related: ["/architecture", "/agents", "/learning"], next: "/agents" },
  "/agents": { related: ["/ontology", "/learning", "/governance"], next: "/learning" },
  "/learning": { related: ["/agents", "/governance", "/architecture"], next: "/governance" },
  "/governance": { related: ["/architecture", "/ontology", "/learning"], next: "/" },
};

export function getNavigationItem(href: string) {
  return primaryNavigation.find((item) => item.href === href);
}
