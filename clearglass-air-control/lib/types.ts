export type ZoneId = 'Zone A' | 'Zone B' | 'Zone C' | 'ICU Pod' | 'Clean Room' | 'Boardroom';

export interface AirSystemState {
  airflow: number;
  pressure: number;
  temperature: number;
  humidity: number;
  filtration: number;
  ventAngle: number;
  activeZone: ZoneId;
  autonomousMode: boolean;
}

export const zones: ZoneId[] = ['Zone A', 'Zone B', 'Zone C', 'ICU Pod', 'Clean Room', 'Boardroom'];
