
// Type definition for Tauri window object
declare global {
    interface Window {
        __TAURI__: {
            invoke?: (command: string, args?: any) => Promise<any>;
            core?: {
                invoke: (command: string, args?: any) => Promise<any>;
            };
        };
    }
}

/**
 * Safely invokes a Tauri command, handling differences between Tauri v1 and v2.
 * @param command The command name to invoke
 * @param args Optional arguments for the command
 * @returns Promise resolving to the command result
 */
export const invoke = async <T = any>(command: string, args?: any): Promise<T> => {
    if (typeof window === 'undefined') {
        throw new Error('Window object is not available');
    }

    // Check for Tauri v2 (window.__TAURI__.core.invoke)
    if (window.__TAURI__?.core?.invoke) {
        return window.__TAURI__.core.invoke(command, args);
    }

    // Check for Tauri v1 (window.__TAURI__.invoke)
    if (window.__TAURI__?.invoke) {
        return window.__TAURI__.invoke(command, args);
    }

    throw new Error('Tauri API is not available. Make sure you are running in a Tauri environment.');
};

/**
 * Checks if the Tauri API is available.
 */
export const isTauriAvailable = (): boolean => {
    return typeof window !== 'undefined' &&
        !!(window.__TAURI__?.core?.invoke || window.__TAURI__?.invoke);
};
