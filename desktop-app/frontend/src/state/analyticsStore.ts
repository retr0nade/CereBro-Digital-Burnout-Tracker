import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types
export type Point = { 
  t: number; 
  focus?: number; 
  distract?: number; 
  idle?: number; 
  totalInputs?: number; 
};

export type AppSlice = { 
  name: string; 
  minutes: number; 
};

export type Connection = { 
  backend: boolean; 
  ws: boolean; 
};

export type DashRange = {
  from: number | null;
  to: number | null;
  preset: "today" | "week" | "month";
};

export type Counters = {
  focusMinutes: number;
  distractMinutes: number;
  appSwitches: number;
  idleEvents: number;
  totalMinutes: number;
};

// Store interface
interface AnalyticsState {
  // Configuration
  rtWindowMinutes: number;
  
  // Dashboard range settings
  dashRange: DashRange;
  
  // Data
  timeseries: {
    realtime: Point[];
    dashboard: Point[];
  };
  apps: AppSlice[];
  counters: Counters;
  connection: Connection;
  
  // Actions
  actions: {
    appendRealtime(p: Point): void;
    setDashboardSeries(data: Point[]): void;
    setApps(apps: AppSlice[]): void;
    bumpCounter(key: "appSwitches" | "idleEvents", inc?: number): void;
    setCounters(partial: Partial<Counters>): void;
    setConnection(partial: Partial<Connection>): void;
    setDashRange(range: DashRange): void;
    resetRealtime(): void;
  };
}

// Initial state
const initialState = {
  rtWindowMinutes: 10,
  dashRange: {
    from: null,
    to: null,
    preset: "today" as const,
  },
  timeseries: {
    realtime: [],
    dashboard: [],
  },
  apps: [],
  counters: {
    focusMinutes: 0,
    distractMinutes: 0,
    appSwitches: 0,
    idleEvents: 0,
    totalMinutes: 0,
  },
  connection: {
    backend: false,
    ws: false,
  },
};

// Create the store
export const useAnalytics = create<AnalyticsState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      actions: {
        appendRealtime: (p: Point) => {
          set((state) => {
            const { rtWindowMinutes } = state;
            const cutoff = Date.now() - rtWindowMinutes * 60 * 1000;
            
            // Filter existing points to rolling window
            const filteredRealtime = state.timeseries.realtime.filter(
              (point) => point.t >= cutoff
            );
            
            // Add new point
            const newRealtime = [...filteredRealtime, p];
            
            // Calculate total minutes from time deltas
            let totalMinutes = 0;
            if (newRealtime.length > 1) {
              for (let i = 1; i < newRealtime.length; i++) {
                const delta = newRealtime[i].t - newRealtime[i - 1].t;
                totalMinutes += delta / (60 * 1000); // Convert ms to minutes
              }
            }
            
            return {
              timeseries: {
                ...state.timeseries,
                realtime: newRealtime,
              },
              counters: {
                ...state.counters,
                totalMinutes,
              },
            };
          });
        },
        
        setDashboardSeries: (data: Point[]) => {
          set((state) => ({
            timeseries: {
              ...state.timeseries,
              dashboard: data,
            },
          }));
        },
        
        setApps: (apps: AppSlice[]) => {
          set(() => ({ apps }));
        },
        
        bumpCounter: (key: "appSwitches" | "idleEvents", inc = 1) => {
          set((state) => ({
            counters: {
              ...state.counters,
              [key]: state.counters[key] + inc,
            },
          }));
        },
        
        setCounters: (partial: Partial<Counters>) => {
          set((state) => ({
            counters: {
              ...state.counters,
              ...partial,
            },
          }));
        },
        
        setConnection: (partial: Partial<Connection>) => {
          set((state) => ({
            connection: {
              ...state.connection,
              ...partial,
            },
          }));
        },
        
        setDashRange: (range: DashRange) => {
          set(() => ({ dashRange: range }));
        },
        
        resetRealtime: () => {
          set((state) => ({
            timeseries: {
              ...state.timeseries,
              realtime: [],
            },
            counters: {
              ...state.counters,
              totalMinutes: 0,
            },
          }));
        },
      },
    }),
    {
      name: "cerebro_state_v1",
      partialize: (state) => ({
        // Persist dashboard data, apps, range, and counters
        timeseries: {
          dashboard: state.timeseries.dashboard,
          realtime: [], // Don't persist realtime data
        },
        apps: state.apps,
        dashRange: state.dashRange,
        counters: state.counters,
        rtWindowMinutes: state.rtWindowMinutes,
      }),
    }
  )
);

// Select helpers
export const selectRealtime = (state: AnalyticsState) => state.timeseries.realtime;
export const selectDashboardSeries = (state: AnalyticsState) => state.timeseries.dashboard;
export const selectCounters = (state: AnalyticsState) => state.counters;
export const selectApps = (state: AnalyticsState) => state.apps;
export const selectConn = (state: AnalyticsState) => state.connection;
export const selectDashRange = (state: AnalyticsState) => state.dashRange;
export const selectActions = (state: AnalyticsState) => state.actions;

// Convenience hooks
export const useRealtimeData = () => useAnalytics(selectRealtime);
export const useDashboardSeries = () => useAnalytics(selectDashboardSeries);
export const useCounters = () => useAnalytics(selectCounters);
export const useApps = () => useAnalytics(selectApps);
export const useConnection = () => useAnalytics(selectConn);
export const useDashRange = () => useAnalytics(selectDashRange);
export const useAnalyticsActions = () => useAnalytics(selectActions);
