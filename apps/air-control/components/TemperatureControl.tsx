"use client";

export interface TemperatureControlProps {
  /** current temperature in °C (16..30) */
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

/**
 * Gradient thermal column: a mercury tube whose fill height tracks the
 * temperature, paired with a range control.
 */
export function TemperatureControl({
  value,
  onChange,
  min = 16,
  max = 30,
  step = 0.5,
}: TemperatureControlProps) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  return (
    <div className="thermo">
      <div className="tube">
        <div className="mercury" style={{ height: `${pct}%` }} />
      </div>
      <input
        className="range"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-label="Temperature (°C)"
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

export default TemperatureControl;
