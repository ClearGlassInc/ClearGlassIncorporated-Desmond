import { describe, expect, it } from "vitest";
import { parseImport } from "@/lib/importers";

describe("import framework", () => {
  it("parses header-based CSV", async () => {
    const result = await parseImport(Buffer.from("name,mineral\nAlpha,Lithium\nBeta,Copper\n"), "csv");
    expect(result.records).toHaveLength(2);
    expect(result.records[0]).toEqual({ name: "Alpha", mineral: "Lithium" });
  });

  it("requires JSON arrays of objects", async () => {
    const result = await parseImport(Buffer.from(JSON.stringify([{ name: "Alpha", risk: 20 }])), "json");
    expect(result.records[0]?.risk).toBe(20);
    await expect(parseImport(Buffer.from(JSON.stringify({ name: "not-an-array" })), "json")).rejects.toThrow();
  });

  it("preserves GeoJSON geometry separately from properties", async () => {
    const result = await parseImport(Buffer.from(JSON.stringify({ type: "FeatureCollection", features: [{ type: "Feature", id: "a", geometry: { type: "Point", coordinates: [-80, 43] }, properties: { name: "Project A" } }] })), "geojson");
    expect(result.records[0]?.name).toBe("Project A");
    expect(result.records[0]?._feature_id).toBe("a");
    expect(result.records[0]?._geometry).toEqual({ type: "Point", coordinates: [-80, 43] });
  });

  it("enforces byte limits before parsing", async () => {
    await expect(parseImport(Buffer.from("12345"), "csv", { maxBytes: 4 })).rejects.toThrow(/maximum size/i);
  });
});
