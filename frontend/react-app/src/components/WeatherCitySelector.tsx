import React, { useState, useEffect } from 'react';

/**
 * Sélecteur de ville météo : permet à l'utilisateur de choisir
 * parmi les localisations prédéfinies (provinces et villes du Burundi)
 * ou de saisir n'importe quelle localité.
 * La sélection est persistée en localStorage.
 */

const MAIN_LOCATIONS = [
  // Provinces historiques du Burundi
  'Bujumbura Mairie',
  'Bujumbura Rural',
  'Bubanza',
  'Cibitoke',
  'Kayanza',
  'Ngozi',
  'Karuzi',
  'Muramvya',
  'Mwaro',
  'Gitega',
  'Rutana',
  'Makamba',
  'Bururi',
  'Rumonge',
  'Muyinga',
  'Kirundo',
  'Cankuzo',
  'Ruyigi',
  // Nouvelles provinces
  'Buhumuza',
  'Burunga',
  'Butanyerera',
  // Communes et villes majeures
  'Nyanza-Lac',
  'Gatumba',
  'Rugombo',
  'Mabayi',
  'Bugarama',
  'Kayogoro',
  'Teza',
  'Mabanda',
  'Kabezi',
  'Gitaza',
  // Métropoles régionales
  'Kigali',
  'Bukavu',
  'Uvira',
  'Goma',
  'Nairobi',
  'Kampala',
  'Dodoma',
  'Dar es Salaam',
  'Mwanza',
];

interface WeatherCitySelectorProps {
  onCityChange: (city: string) => void;
}

const WeatherCitySelector: React.FC<WeatherCitySelectorProps> = ({ onCityChange }) => {
  const [selectedCity, setSelectedCity] = useState<string>('');

  // Charger la sélection sauvegardée depuis localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('selected_weather_city');
      if (stored) {
        setSelectedCity(stored);
      }
    } catch (e) {
      // localStorage not available, ignore
    }
  }, []);

  // Sauvegarder la sélection en localStorage à chaque changement
  useEffect(() => {
    if (selectedCity) {
      try {
        localStorage.setItem('selected_weather_city', selectedCity);
      } catch (e) {
        // ignored
      }
    }
  }, [selectedCity]);

  // Si aucune ville n'est sélectionnée, utiliser Bujumbura Mairie par défaut
  const defaultCity = selectedCity || 'Bujumbura Mairie';

  // État pour la recherche
  const [showSearch, setShowSearch] = useState(false);
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState<string>('');

  // Gestionnaire de saisie (with debounce)
  const debounce = (func: (...args: any[]) => void, wait: number) => {
    let timeout: NodeJS.Timeout;
    return function executedFunction(...args: any[]) {
      clearTimeout(timeout);
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  const debouncedSearch = useCallback(
    debounce((query: string) => {
      const lower = query.toLowerCase().trim();
      if (!lower) {
        setSearchResults([]);
        return;
      }
      // Vérifier dans la liste locale d'abord
      const exactMatches = MAIN_LOCATIONS.filter((city) =>
        city.toLowerCase().includes(lower)
      );
      if (exactMatches.length > 0) {
        setSearchResults(exactMatches);
        return;
      }
      // Sinon, c'est une recherche quelconque (Open-Meteo gérera la géocodage)
      setSearchResults([`${query} (via Open-Meteo geocoding)`]);
    }, []),
    [lower]
  );

  // Gestionnaire d'entrée de recherche
  const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchInput(value);
    const debounced = debouncedSearch(value);
  };

  // Gestionnaire de touche clavier (Enter pour sélectionner, Échap pour fermer)
  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (searchResults.length > 0) {
        onCityChange(searchResults[0]);
        setShowSearch(false);
      }
    } else if (e.key === 'Escape') {
      setShowSearch(false);
      setSearchInput('');
      setSearchResults([]);
    }
  };

  useEffect(() => {
    // Lorsque la saisie change, lancer la recherche débounced
    const handleInput = () => {
      debouncedSearch(searchInput);
    };
    const inputEl = document.getElementById('weather-city-search') as HTMLInputElement;
    if (inputEl) {
      inputEl.addEventListener('input', handleInput);
      return () => inputEl.removeEventListener('input', handleInput);
    }
  }, [searchInput, debouncedSearch]);

  return (
    <div className="flex items-center space-x-2">
      <div className="relative" style={{ width: '280px' }}>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 px-3 py-1 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
            aria-label={`Météo pour ${defaultCity}`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLineCap="round"
                strokeLineJoin="round"
                strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
            <span ref={cityRef} className="truncate w-full">{defaultCity}</span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3 mt-0.5 opacity-50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLineCap="round"
                strokeLineJoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {/* Search or dropdown */}
        {showSearch ? (
          <div className="absolute right-0 mt-2 w-full max-w-xs origin-top-left mt-2 select-search"
            role="dialog"
            aria-modal="true"
            aria-labelledby="select-title"
            style={{ zIndex: 100 }}
          >
            <div className="bg-white dark:bg-dark-800 rounded-lg shadow-lg p-4 min-w" style={{ width: '280px' }}>
              <h3 className="text-sm font-medium mb-3" id="select-title">
                Choisir une ville
              </h3>
              <div className="mb-3">
                <div className="relative">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLineCap="round"
                      strokeLineJoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a1 1 0 01-1 1H5a1 1 0 01-1-1m3.586 13.414L18 9.083"
                    />
                  </svg>
                  <input
                    type="text"
                    id="weather-city-search"
                    onInput={handleSearchInput}
                    onKeyDown={handleSearchKeyDown}
                    placeholder="Rechercher une ville...
                    "
                    className="w-full pl-8 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    autoComplete="off"
                  />
                </div>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1"
                style={{ maxHeight: '200px' }}
              >
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700 cursor-pointer"
                  onClick={() => onCityChange(selectedCity)}
                  role="menuitem"
                >
                  {/* City will be injected by JS */}
                </button>
                {searchResults.length > 0 ? (
                  searchResults.map((city, index) => (
                    <button
                      key={index}
                      className="w-full text-left px-2 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700 cursor-pointer"
                      role="menuitem"
                    >
                      {city}
                    </button>
                  ))
                  : (
                    <p className="p-2 text-sm text-gray-500 dark:text-gray-400">Aucune ville trouvée</p>
                  )}
              </div>
              <div className="mt-3 pt-3 border-t" style={{ borderColor: 'currentColor' }}>n}
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Bujumbura Mairie')}
                  role="menuitem"
                >
                  Bujumbura Mairie
                </button>
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Gitega')}
                  role="menuitem"
                >
                  Gitega
                </button>
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Bujumbura')}
                  role="menuitem"
                >
                  Bujumbura
                </button>
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Kigali')}
                  role="menuitem"
                >
                  Kigali
                </button>
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Nairobi')}
                  role="menuitem"
                >
                  Nairobi
                </button>
                <button
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                  onClick={() => onCityChange('Clear')}
                  role="menuitem"
                >
                  Effacer
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div
            role="menu"
            className="absolute right-0 mt-2 w-48 rounded-lg border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 shadow-lg z-50 min-w"
          >
            <div className="py-1" role="none">
              <button
                onClick={() => onCityChange('Bujumbura Mairie')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Bujumbura Mairie
              </button>
              <button
                onClick={() => onCityChange('Gitega')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Gitega
              </button>
              <button
                onClick={() => onCityChange('Bujumbura')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Bujumbura
              </button>
              <button
                onClick={() => onCityChange('Kigali')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Kigali
              </button>
              <button
                onClick={() => onCityChange('Nairobi')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Nairobi
              </button>
              <button
                onClick={() => onCityChange('Clear')}
                className="w-full text-left px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                role="menuitem"
              >
                Effacer la sélection
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeatherCitySelector;