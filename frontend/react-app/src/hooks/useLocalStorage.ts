import { useState, useEffect, useCallback } from 'react';

/**
 * Stockage local JSON avec support des valeurs fonctionnelles
 * et d'un "reviver" (utile pour reconstituer les Dates apres JSON.parse).
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  reviver?: (value: T) => T,
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (!item) return initialValue;
      const parsed = JSON.parse(item);
      return reviver ? reviver(parsed) : parsed;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Persistance a chaque changement de valeur
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    setStoredValue((prev) => (value instanceof Function ? value(prev) : value));
  }, []);

  return [storedValue, setValue];
}
