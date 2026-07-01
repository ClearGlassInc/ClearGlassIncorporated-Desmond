import type { ReactNode } from "react";

export interface GlassPanelProps {
  kicker?: string;
  title?: string;
  value?: ReactNode;
  unit?: string;
  wide?: boolean;
  className?: string;
  children?: ReactNode;
}

/**
 * Reusable frosted-glass panel: an optional header (kicker + title + value/unit)
 * over a translucent, blurred surface. The visual system lives in globals.css
 * (`.glass`, `.panel`, `.panel-head`, `.value`, `.unit`).
 */
export function GlassPanel({
  kicker,
  title,
  value,
  unit,
  wide = false,
  className = "",
  children,
}: GlassPanelProps) {
  const hasHeader = kicker || title || value != null;
  return (
    <article className={`glass panel ${wide ? "wide" : ""} ${className}`.trim()}>
      {hasHeader && (
        <div className="panel-head">
          <div>
            {kicker && <div className="kicker">{kicker}</div>}
            {title && <h2>{title}</h2>}
          </div>
          {value != null && (
            <div>
              <span className="value">{value}</span>
              {unit && <span className="unit">{unit}</span>}
            </div>
          )}
        </div>
      )}
      {children}
    </article>
  );
}

export default GlassPanel;
