'use client';

import { useEffect, useMemo, useState } from 'react';
import { AirSystemState, ZoneId } from '@/lib/types';

const STORAGE_KEY = 'clearglass-air-control-v0.1';

const initialState: AirSystemState = {
  airflow: 68,
  pressure: 2.4,
  temperature: 22.4,
  humidity: 44,
  filtration: 96,
  ventAngle: 34,
  activeZone: 'Zone A',
  autonomousMode: true,
};

export function useAirSystem() {
  const [state, setState] = useState<AirSystemState>(initialState);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) setState({ ...initialState, ...JSON.parse(saved) });
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const riskIndex = useMemo(() => {
    const tempRisk = Math.abs(state.temperature - 22) * 4;
    const humidityRisk = Math.abs(state.humidity - 45) * 0.7;
    const pressureRisk = Math.abs(state.pressure - 2.4) * 12;
    const filterRisk = Math.max(0, 98 - state.filtration) * 1.8;
    return Math.min(100, Math.round(tempRisk + humidityRisk + pressureRisk + filterRisk));
  }, [state]);

  return {
    state,
    riskIndex,
    setAirflow: (airflow: number) => setState((s) => ({ ...s, airflow })),
    setPressure: (pressure: number) => setState((s) => ({ ...s, pressure })),
    setTemperature: (temperature: number) => setState((s) => ({ ...s, temperature })),
    setHumidity: (humidity: number) => setState((s) => ({ ...s, humidity })),
    setFiltration: (filtration: number) => setState((s) => ({ ...s, filtration })),
    setVentAngle: (ventAngle: number) => setState((s) => ({ ...s, ventAngle })),
    setActiveZone: (activeZone: ZoneId) => setState((s) => ({ ...s, activeZone })),
    setAutonomousMode: (autonomousMode: boolean) => setState((s) => ({ ...s, autonomousMode })),
  };
}
