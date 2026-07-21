import { useEffect, useState, type Dispatch, type SetStateAction } from "react";

/**
 * State backed by localStorage so view preferences survive reloads. Falls back
 * to the initial value when storage is unavailable or holds invalid JSON.
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = window.localStorage.getItem(key);
      return stored === null ? initialValue : (JSON.parse(stored) as T);
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore quota or availability errors; preferences are best-effort.
    }
  }, [key, value]);

  return [value, setValue];
}
