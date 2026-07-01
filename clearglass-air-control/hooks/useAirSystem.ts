'use client';

import { useEffect, useMemo, useState } from 'react';
import { AirSystemState, ZoneId } from '@/lib/types';

const STORAGE_KEY = 'clearglass-air-system-v0.2';

const defaultState: AirSystemState = {
  airflow: 68,
  pressure: 101.3,
  temperature: 22.4,
  humidity: 42,
  filtration: 94,
  ventAngle: 45,
  activeZone: 'Zone A',
  autonomousMode: false,
};

export function useAirSystem() {
  const [state, setState] = useState<AirSystemState>(defaultState);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) return;

    try {
      setState({ ...defaultState, ...JSON.parse(saved) });
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const update = (key: keyof AirSystemState, value: number | string | boolean) => {
    setState((prev) => ({ ...prev, [key]: value }));
  };

  const riskIndex = useMemo(() => {
    const tempRisk = Math.abs(state.temperature - 22) * 4;
    const humidityRisk = Math.abs(state.humidity - 45) * 0.7;
    const pressureRisk = Math.abs(state.pressure - 101.3) * 1.6;
    const filterRisk = Math.max(0, 98 - state.filtration) * 1.8;
    return Math.min(100, Math.round(tempRisk + humidityRisk + pressureRisk + filterRisk));
  }, [state]);

  return {
    state,
    riskIndex,
    update,
    setAirflow: (airflow: number) => update('airflow', airflow),
    setPressure: (pressure: number) => update('pressure', pressure),
    setTemperature: (temperature: number) => update('temperature', temperature),
    setHumidity: (humidity: number) => update('humidity', humidity),
    setFiltration: (filtration: number) => update('filtration', filtration),
    setVentAngle: (ventAngle: number) => update('ventAngle', ventAngle),
    setActiveZone: (activeZone: ZoneId) => update('activeZone', activeZone),
    setAutonomousMode: (autonomousMode: boolean) => update('autonomousMode', autonomousMode),
  };
}
