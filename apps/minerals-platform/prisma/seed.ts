import { PrismaClient, UserRole } from "@prisma/client";

const db = new PrismaClient();

const minerals = [
  ["lithium", "Lithium", "Li", "Battery materials"],
  ["cobalt", "Cobalt", "Co", "Battery materials"],
  ["nickel", "Nickel", "Ni", "Battery materials"],
  ["copper", "Copper", "Cu", "Base metals"],
  ["graphite", "Graphite", "C", "Battery materials"],
  ["rare-earth-elements", "Rare earth elements", null, "Rare earths"],
  ["neodymium", "Neodymium", "Nd", "Rare earths"],
  ["praseodymium", "Praseodymium", "Pr", "Rare earths"],
  ["dysprosium", "Dysprosium", "Dy", "Rare earths"],
  ["terbium", "Terbium", "Tb", "Rare earths"],
  ["gallium", "Gallium", "Ga", "Technology metals"],
  ["germanium", "Germanium", "Ge", "Technology metals"],
  ["tungsten", "Tungsten", "W", "Strategic metals"],
  ["tin", "Tin", "Sn", "Base metals"],
  ["manganese", "Manganese", "Mn", "Battery materials"],
  ["chromium", "Chromium", "Cr", "Alloy metals"],
  ["vanadium", "Vanadium", "V", "Alloy metals"],
  ["platinum-group-metals", "Platinum-group metals", null, "Precious metals"],
  ["uranium", "Uranium", "U", "Energy minerals"],
  ["phosphate", "Phosphate", null, "Industrial minerals"],
  ["potash", "Potash", null, "Industrial minerals"],
  ["iron-ore", "Iron ore", "Fe", "Bulk commodities"],
  ["gold", "Gold", "Au", "Precious metals"],
  ["silver", "Silver", "Ag", "Precious metals"],
  ["bauxite-aluminum", "Bauxite / aluminum", "Al", "Base metals"],
  ["silicon-industrial-minerals", "Silicon / industrial minerals", "Si", "Industrial minerals"]
] as const;

const sources = [
  ["prices", "ClearGlass Public Minerals Feed", "Price snapshots", 3600],
  ["production", "ClearGlass Public Minerals Feed", "Production snapshots", 86400],
  ["reserves", "ClearGlass Public Minerals Feed", "Reserve snapshots", 86400],
  ["trade", "ClearGlass Public Minerals Feed", "Trade snapshots", 21600],
  ["policy", "ClearGlass Public Minerals Feed", "Policy snapshots", 21600],
  ["sanctions", "ClearGlass Public Minerals Feed", "Sanctions snapshots", 21600],
  ["supply-risk", "ClearGlass Public Minerals Feed", "Supply-risk snapshots", 21600],
  ["news", "ClearGlass Public Minerals Feed", "Trusted news snapshots", 3600],
  ["provenance", "ClearGlass Public Minerals Feed", "Provenance snapshots", 21600]
] as const;

async function main() {
  const organizationId = "00000000-0000-0000-0000-000000000001";
  const userId = "00000000-0000-0000-0000-000000000001";
  await db.organization.upsert({ where: { slug: "clearglass-development" }, create: { id: organizationId, slug: "clearglass-development", name: "ClearGlass Development" }, update: { name: "ClearGlass Development" } });
  await db.user.upsert({ where: { email: "developer@clearglass.local" }, create: { id: userId, email: "developer@clearglass.local", name: "Development Administrator", subject: "dev-admin" }, update: { name: "Development Administrator" } });
  await db.organizationMember.upsert({ where: { organizationId_userId: { organizationId, userId } }, create: { organizationId, userId, role: UserRole.ADMINISTRATOR }, update: { role: UserRole.ADMINISTRATOR } });

  for (const [slug, name, symbol, group] of minerals) {
    await db.mineral.upsert({ where: { slug }, create: { slug, name, symbol, group }, update: { name, symbol, group, deletedAt: null } });
  }

  const countrySeed = [
    ["CA", "CAN", "Canada", "Americas"],
    ["US", "USA", "United States", "Americas"],
    ["AU", "AUS", "Australia", "Oceania"],
    ["CD", "COD", "Democratic Republic of the Congo", "Africa"],
    ["CN", "CHN", "China", "Asia"],
    ["CL", "CHL", "Chile", "Americas"],
    ["AR", "ARG", "Argentina", "Americas"],
    ["ID", "IDN", "Indonesia", "Asia"],
    ["ZA", "ZAF", "South Africa", "Africa"],
    ["BR", "BRA", "Brazil", "Americas"]
  ] as const;
  for (const [iso2, iso3, name, region] of countrySeed) {
    await db.country.upsert({ where: { iso3 }, create: { iso2, iso3, name, region }, update: { iso2, name, region } });
  }

  for (const [key, provider, dataset, ttlSeconds] of sources) {
    await db.dataSource.upsert({
      where: { key },
      create: { key, provider, dataset, sourceUrl: `https://www.clearglassinc.com/data/minerals/latest/${key}.json`, license: "See upstream source metadata", cadence: "provider-defined", ttlSeconds, enabled: true, freshnessStatus: "UNKNOWN" },
      update: { provider, dataset, sourceUrl: `https://www.clearglassinc.com/data/minerals/latest/${key}.json`, ttlSeconds, enabled: true }
    });
  }
  console.log(`Seeded ${minerals.length} minerals, ${countrySeed.length} countries, ${sources.length} source adapters.`);
}

main().finally(async () => db.$disconnect());
