"use client";

import { useCallback, useMemo, useState } from "react";

export type ZoneName = "Atrium" | "Lab" | "Hangar" | "Command";
export const ZONES: readonly ZoneName[] = ["Atrium", "Lab", "Hangar", "Command"];

export interface AirState {
  airflow: number; // 20..100 %
  temp: number; //    16..30  °C
  humidity: number; // 20..80 %
  filter: number; //   0..100 %
  vent: number; //   -90..90  °
  zone: ZoneName;
}

/** Numeric fields that carry a clamped range. */
export type NumericField = "airflow" | "temp" | "humidity" | "vent" | "filter";

const RANGES: Record<NumericField, readonly [number, number]> = {
  airflow: [20, 100],
  temp: [16, 30],
  humidity: [20, 80],
  vent: [-90, 90],
  filter: [0, 100],
};

const INITIAL: AirState = {
  airflow: 72,
  temp: 21.5,
  humidity: 48,
  filter: 87,
  vent: 38,
  zone: "Atrium",
};

const clamp = (v: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Number.isFinite(v) ? v : min));

export interface AirLog {
  id: number;
  t: string;
  msg: string;
}

export interface AirDerived {
  pressure: number;
  pressureState: "NOMINAL" | "ELEVATED";
  efficiency: number;
  comfort: "A" | "A+";
}

export interface AirSystem {
  state: AirState;
  logs: AirLog[];
  derived: AirDerived;
  zones: readonly ZoneName[];
  log: (msg: string) => void;
  setNumber: (key: NumericField, value: number) => void;
  setZone: (zone: ZoneName) => void;
  optimize: () => void;
  purge: () => void;
}

/**
 * Single source of truth for the Air Systems Control Surface.
 * Every setter clamps to a safe range; derived metrics are memoised; the log is bounded.
 */
export function useAirSystem(): AirSystem {
  const [state, setState] = useState<AirState>(INITIAL);
  const [logs, setLogs] = useState<AirLog[]>([]);

  const log = useCallback((msg: string) => {
    setLogs((prev) => {
      const id = (prev[0]?.id ?? 0) + 1;
      const t = new Date().toISOString().slice(11, 19);
      return [{ id, t, msg }, ...prev].slice(0, 8);
    });
  }, []);

  const setNumber = useCallback((key: NumericField, value: number) => {
    const [min, max] = RANGES[key];
    setState((prev) => ({ ...prev, [key]: clamp(value, min, max) }));
  }, []);

  const setZone = useCallback(
    (zone: ZoneName) => {
      setState((prev) => ({ ...prev, zone }));
      log("Zone focus shifted to " + zone);
    },
    [log],
  );

  const optimize = useCallback(() => {
    setState((prev) => ({ ...prev, airflow: 76, temp: 22, humidity: 50, vent: 24 }));
    log("AIP optimizer applied comfort/efficiency target vector");
  }, [log]);

  const purge = useCallback(() => {
    setState((prev) => ({ ...prev, airflow: 100, vent: 72 }));
    log("Manual purge cycle staged for operator confirmation");
  }, [log]);

  const derived = useMemo<AirDerived>(() => {
    const pressure = Number(
      (24 + state.airflow * 0.105 + (state.vent / 90) * 1.2).toFixed(1),
    );
    const efficiency = clamp(
      Math.round(
        state.filter * 0.45 +
          (100 - Math.abs(22 - state.temp) * 6) * 0.25 +
          (100 - Math.abs(50 - state.humidity)) * 0.3,
      ),
      0,
      100,
    );
    const comfort: "A" | "A+" =
      Math.abs(22 - state.temp) < 2 && Math.abs(50 - state.humidity) < 12 ? "A+" : "A";
    return {
      pressure,
      pressureState: pressure > 34 ? "ELEVATED" : "NOMINAL",
      efficiency,
      comfort,
    };
  }, [state]);

  return { state, logs, derived, zones: ZONES, log, setNumber, setZone, optimize, purge };
}
