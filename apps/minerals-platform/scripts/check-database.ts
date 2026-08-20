import { PrismaClient } from "@prisma/client";

const db = new PrismaClient();

try {
  const [minerals, countries, sources, organizations, users] = await Promise.all([
    db.mineral.count(),
    db.country.count(),
    db.dataSource.count(),
    db.organization.count(),
    db.user.count()
  ]);
  const expected = { minerals: 26, countries: 10, sources: 9, organizations: 1, users: 1 };
  const actual = { minerals, countries, sources, organizations, users };
  for (const [key, minimum] of Object.entries(expected)) {
    if (actual[key as keyof typeof actual] < minimum) throw new Error(`${key}: expected at least ${minimum}, got ${actual[key as keyof typeof actual]}`);
  }
  console.log("Database integration check passed", actual);
} finally {
  await db.$disconnect();
}
