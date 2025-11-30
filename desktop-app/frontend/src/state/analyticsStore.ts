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
  preset: "today" | "week" | "month" | "lifetime";
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
  rtWindowMinutes: number;
  dashRange: DashRange;
  timeseries: {
    realtime: Point[];
    dashboard: Point[];
  };
  apps: AppSlice[];
  counters: Counters;
  connection: Connection;
  actions: {
    appendRealtime: (p: Point) => void;
    setDashboardSeries: (data: Point[]) => void;
    setApps: (apps: AppSlice[]) => void;
    bumpCounter: (key: "appSwitches" | "idleEvents", inc?: number) => void;
    setCounters: (partial: Partial<Counters>) => void;
    setConnection: (partial: Partial<Connection>) => void;
    setDashRange: (range: Partial<DashRange>) => void;
    setRtWindowMinutes: (minutes: number) => void;
    resetRealtime: () => void;
  };
}

// Create store with persist middleware
export const useAnalytics = create<AnalyticsState>()(
  persist(
    (set, get) => ({
      rtWindowMinutes: 10,
      dashRange: {
        from: null,
        to: null,
        preset: "today"
      },
      timeseries: {
        realtime: [],
        dashboard: []
      },
      apps: [],
      counters: {
        focusMinutes: 0,
        distractMinutes: 0,
        appSwitches: 0,
        idleEvents: 0,
        totalMinutes: 0
      },
      connection: {
        backend: false,
        ws: false
      },
      actions: {
        appendRealtime: (p: Point) => {
          set((state) => {
            const { rtWindowMinutes } = state;
            const cutoff = Date.now() - rtWindowMinutes * 60 * 1000;

            // Add new point and filter old ones
            const newRealtime = [...state.timeseries.realtime, p].filter(
              point => point.t >= cutoff
            );

            // Compute totalMinutes from minute deltas if data is available
            let totalMinutes = state.counters.totalMinutes;
            if (newRealtime.length > 1) {
              const sortedPoints = newRealtime.sort((a, b) => a.t - b.t);
              totalMinutes = 0;
              for (let i = 1; i < sortedPoints.length; i++) {
                const deltaMs = sortedPoints[i].t - sortedPoints[i - 1].t;
                const deltaMinutes = deltaMs / (1000 * 60);
                totalMinutes += deltaMinutes;
              }
            }

            return {
              timeseries: {
                ...state.timeseries,
                realtime: newRealtime
              },
              counters: {
                ...state.counters,
                totalMinutes
              }
            };
          });
        },

        setDashboardSeries: (data: Point[]) => {
          set((state) => ({
            timeseries: {
              ...state.timeseries,
              dashboard: data
            }
          }));
        },

        setApps: (apps: AppSlice[]) => {
          set({ apps });
        },

        bumpCounter: (key: "appSwitches" | "idleEvents", inc = 1) => {
          set((state) => ({
            counters: {
              ...state.counters,
              [key]: state.counters[key] + inc
            }
          }));
        },

        setCounters: (partial: Partial<Counters>) => {
          set((state) => ({
            counters: {
              ...state.counters,
              ...partial
            }
          }));
        },

        setConnection: (partial: Partial<Connection>) => {
          set((state) => ({
            connection: {
              ...state.connection,
              ...partial
            }
          }));
        },

        setDashRange: (range: Partial<DashRange>) => {
          set((state) => ({
            dashRange: {
              ...state.dashRange,
              ...range
            }
          }));
        },

        setRtWindowMinutes: (minutes: number) => {
          set({ rtWindowMinutes: minutes });
        },

        resetRealtime: () => {
          set((state) => ({
            timeseries: {
              ...state.timeseries,
              realtime: []
            }
          }));
        }
      }
    }),
    {
      name: 'cerebro_state_v1',
      // Only persist dashboard timeseries, apps, dashRange, and counters
      // Do NOT persist realtime timeseries or connection state
      partialize: (state) => ({
        dashRange: state.dashRange,
        timeseries: {
          dashboard: state.timeseries.dashboard,
          realtime: [] // Ensure realtime key exists on rehydration
        },
        apps: state.apps,
        counters: state.counters
      })
    }
  )
);

// Selector hooks for easy access
export const selectRealtime = (state: AnalyticsState) => state.timeseries.realtime;
export const selectDashboardSeries = (state: AnalyticsState) => state.timeseries.dashboard;
export const selectCounters = (state: AnalyticsState) => state.counters;
export const selectApps = (state: AnalyticsState) => state.apps;
export const selectConn = (state: AnalyticsState) => state.connection;

// Convenience hooks
export const useRealtimeData = () => useAnalytics(selectRealtime);
export const useDashboardData = () => useAnalytics(selectDashboardSeries);
export const useCounters = () => useAnalytics(selectCounters);
export const useApps = () => useAnalytics(selectApps);
export const useConnection = () => useAnalytics(selectConn);
export const useAnalyticsActions = () => useAnalytics(state => state.actions);