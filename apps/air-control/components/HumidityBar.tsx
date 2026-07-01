"use client";

export interface HumidityBarProps {
  /** current relative humidity in % (20..80) */
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  /** number of segment bars in the meter */
  segments?: number;
}

/**
 * Moisture-balance meter: a stack of segment bars whose widths decay from the
 * current humidity, paired with a range control.
 */
export function HumidityBar({
  value,
  onChange,
  min = 20,
  max = 80,
  segments = 8,
}: HumidityBarProps) {
  const bars = Array.from({ length: segments }, (_, i) =>
    Math.max(6, Math.min(100, value - i * 7)),
  );
  return (
    <>
      <div className="bars">
        {bars.map((w, i) => (
          <div className="bar" key={i}>
            <i style={{ width: `${w}%` }} />
          </div>
        ))}
      </div>
      <div className="control" style={{ marginTop: 18 }}>
        <input
          className="range"
          type="range"
          min={min}
          max={max}
          value={value}
          aria-label="Humidity (%)"
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </div>
    </>
  );
}

export default HumidityBar;
