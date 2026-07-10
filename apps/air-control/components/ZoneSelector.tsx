"use client";

import type { ZoneName } from "../hooks/useAirSystem";

export interface ZoneSelectorProps {
  zones: readonly ZoneName[];
  active: ZoneName;
  onSelect: (zone: ZoneName) => void;
}

/**
 * Selectable active comfort cells. The pressed zone is the active climate focus;
 * the rest report STANDBY. Uses `aria-pressed` for accessible toggle semantics.
 */
export function ZoneSelector({ zones, active, onSelect }: ZoneSelectorProps) {
  return (
    <div className="zones">
      {zones.map((z) => (
        <button
          key={z}
          type="button"
          className="zone"
          aria-pressed={z === active}
          onClick={() => onSelect(z)}
        >
          <b>{z}</b>
          <span>{z === active ? "ACTIVE" : "STANDBY"}</span>
        </button>
      ))}
    </div>
  );
}

export default ZoneSelector;
