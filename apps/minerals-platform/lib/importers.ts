import ExcelJS from "exceljs";
import { parse as parseCsv } from "csv-parse/sync";
import { z } from "zod";

export type ImportFormat = "csv" | "json" | "geojson" | "xlsx";
export type ImportResult = { format: ImportFormat; records: Record<string, unknown>[]; warnings: string[] };

const jsonRecord = z.record(z.string(), z.json());
const jsonArray = z.array(jsonRecord);
const geoJson = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(z.object({
    type: z.literal("Feature"),
    id: z.union([z.string(), z.number()]).optional(),
    geometry: z.record(z.string(), z.json()).nullable(),
    properties: z.record(z.string(), z.json()).nullable().default({})
  }))
});

export async function parseImport(buffer: Buffer, format: ImportFormat, options: { maxBytes?: number; maxRecords?: number } = {}): Promise<ImportResult> {
  const maxBytes = options.maxBytes ?? Number(process.env.UPLOAD_MAX_BYTES ?? 10 * 1024 * 1024);
  const maxRecords = options.maxRecords ?? 50_000;
  if (buffer.byteLength > maxBytes) throw new Error(`Import exceeds maximum size of ${maxBytes} bytes`);
  let records: Record<string, unknown>[];
  const warnings: string[] = [];

  if (format === "csv") {
    const parsed = parseCsv(buffer, { bom: true, columns: true, skip_empty_lines: true, trim: true, relax_column_count: false, max_record_size: 1024 * 1024 }) as Record<string, string>[];
    records = parsed.map((row) => ({ ...row }));
  } else if (format === "json") {
    records = jsonArray.parse(JSON.parse(buffer.toString("utf8")));
  } else if (format === "geojson") {
    const collection = geoJson.parse(JSON.parse(buffer.toString("utf8")));
    records = collection.features.map((feature, index) => ({
      ...feature.properties,
      _feature_id: feature.id ?? index,
      _geometry: feature.geometry
    }));
  } else {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(buffer);
    const sheet = workbook.worksheets[0];
    if (!sheet) return { format, records: [], warnings: ["Workbook contains no worksheets"] };
    const headerRow = sheet.getRow(1);
    const headers = headerRow.values instanceof Array ? headerRow.values.slice(1).map((value, index) => cellValue(value) || `column_${index + 1}`) : [];
    records = [];
    sheet.eachRow({ includeEmpty: false }, (row, rowNumber) => {
      if (rowNumber === 1) return;
      const values = row.values instanceof Array ? row.values.slice(1) : [];
      const record: Record<string, unknown> = {};
      headers.forEach((header, index) => { record[String(header)] = cellValue(values[index]); });
      records.push(record);
    });
  }

  if (records.length > maxRecords) throw new Error(`Import contains ${records.length} records; maximum is ${maxRecords}`);
  if (!records.length) warnings.push("No records found");
  return { format, records, warnings };
}

function cellValue(value: ExcelJS.CellValue | undefined): string | number | boolean | null {
  if (value == null) return null;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return value;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "object") {
    if ("text" in value && typeof value.text === "string") return value.text;
    if ("result" in value) {
      const result = value.result;
      if (result == null || typeof result === "string" || typeof result === "number" || typeof result === "boolean") return result ?? null;
      if (result instanceof Date) return result.toISOString();
    }
    if ("richText" in value && Array.isArray(value.richText)) return value.richText.map((item) => item.text).join("");
    if ("hyperlink" in value && typeof value.hyperlink === "string") return "text" in value && typeof value.text === "string" ? value.text : value.hyperlink;
  }
  return String(value);
}
