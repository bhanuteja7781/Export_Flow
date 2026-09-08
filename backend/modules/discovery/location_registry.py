"""
location_registry.py - Authoritative Geographic Mapping for North American Buyer Discovery
Ensures 100% geographic consistency (city -> state -> country) across all search & discovery modules.
"""

from typing import Dict, Tuple, Optional, List

CITY_STATE_COUNTRY_MAP: Dict[str, Tuple[str, str]] = {
    # --- California ---
    "San Francisco": ("California", "United States"),
    "Los Angeles": ("California", "United States"),
    "San Diego": ("California", "United States"),
    "San Jose": ("California", "United States"),
    "Sacramento": ("California", "United States"),
    "Fresno": ("California", "United States"),
    "Long Beach": ("California", "United States"),
    "Oakland": ("California", "United States"),
    "Anaheim": ("California", "United States"),
    "Irvine": ("California", "United States"),
    "Santa Ana": ("California", "United States"),
    "Riverside": ("California", "United States"),
    "Stockton": ("California", "United States"),
    "Fremont": ("California", "United States"),
    "Beverly Hills": ("California", "United States"),
    "Pasadena": ("California", "United States"),
    "Santa Monica": ("California", "United States"),
    "Santa Barbara": ("California", "United States"),
    "Palo Alto": ("California", "United States"),
    "Bakersfield": ("California", "United States"),
    "Berkeley": ("California", "United States"),
    "Huntington Beach": ("California", "United States"),
    "Newport Beach": ("California", "United States"),
    "Artesia": ("California", "United States"),

    # --- New York ---
    "New York": ("New York", "United States"),
    "New York City": ("New York", "United States"),
    "Brooklyn": ("New York", "United States"),
    "Queens": ("New York", "United States"),
    "Buffalo": ("New York", "United States"),
    "Rochester": ("New York", "United States"),
    "Yonkers": ("New York", "United States"),
    "Syracuse": ("New York", "United States"),
    "Albany": ("New York", "United States"),
    "Long Island": ("New York", "United States"),

    # --- Texas ---
    "Houston": ("Texas", "United States"),
    "San Antonio": ("Texas", "United States"),
    "Dallas": ("Texas", "United States"),
    "Austin": ("Texas", "United States"),
    "Fort Worth": ("Texas", "United States"),
    "El Paso": ("Texas", "United States"),
    "Arlington": ("Texas", "United States"),
    "Plano": ("Texas", "United States"),
    "Irving": ("Texas", "United States"),
    "Sugar Land": ("Texas", "United States"),

    # --- Illinois ---
    "Chicago": ("Illinois", "United States"),
    "Aurora": ("Illinois", "United States"),
    "Naperville": ("Illinois", "United States"),
    "Joliet": ("Illinois", "United States"),
    "Rockford": ("Illinois", "United States"),
    "Springfield": ("Illinois", "United States"),
    "Schaumburg": ("Illinois", "United States"),

    # --- Florida ---
    "Miami": ("Florida", "United States"),
    "Orlando": ("Florida", "United States"),
    "Tampa": ("Florida", "United States"),
    "Jacksonville": ("Florida", "United States"),
    "St. Petersburg": ("Florida", "United States"),
    "Fort Lauderdale": ("Florida", "United States"),
    "Sarasota": ("Florida", "United States"),
    "Boca Raton": ("Florida", "United States"),
    "West Palm Beach": ("Florida", "United States"),
    "Naples": ("Florida", "United States"),

    # --- Washington ---
    "Seattle": ("Washington", "United States"),
    "Spokane": ("Washington", "United States"),
    "Tacoma": ("Washington", "United States"),
    "Vancouver (WA)": ("Washington", "United States"),
    "Bellevue": ("Washington", "United States"),

    # --- Georgia ---
    "Atlanta": ("Georgia", "United States"),
    "Savannah": ("Georgia", "United States"),
    "Augusta": ("Georgia", "United States"),
    "Alpharetta": ("Georgia", "United States"),
    "Duluth": ("Georgia", "United States"),

    # --- Massachusetts ---
    "Boston": ("Massachusetts", "United States"),
    "Cambridge": ("Massachusetts", "United States"),
    "Worcester": ("Massachusetts", "United States"),

    # --- Pennsylvania ---
    "Philadelphia": ("Pennsylvania", "United States"),
    "Pittsburgh": ("Pennsylvania", "United States"),
    "Allentown": ("Pennsylvania", "United States"),
    "Upper Darby": ("Pennsylvania", "United States"),

    # --- Colorado ---
    "Denver": ("Colorado", "United States"),
    "Colorado Springs": ("Colorado", "United States"),
    "Aurora (CO)": ("Colorado", "United States"),
    "Boulder": ("Colorado", "United States"),
    "Aspen": ("Colorado", "United States"),

    # --- Arizona ---
    "Phoenix": ("Arizona", "United States"),
    "Tucson": ("Arizona", "United States"),
    "Mesa": ("Arizona", "United States"),
    "Scottsdale": ("Arizona", "United States"),
    "Chandler": ("Arizona", "United States"),

    # --- New Jersey ---
    "Edison": ("New Jersey", "United States"),
    "Iselin": ("New Jersey", "United States"),
    "Jersey City": ("New Jersey", "United States"),
    "Newark": ("New Jersey", "United States"),
    "Woodbridge": ("New Jersey", "United States"),
    "Parsippany": ("New Jersey", "United States"),

    # --- North Carolina ---
    "Charlotte": ("North Carolina", "United States"),
    "Raleigh": ("North Carolina", "United States"),
    "Durham": ("North Carolina", "United States"),
    "Cary": ("North Carolina", "United States"),

    # --- Ontario, Canada ---
    "Toronto": ("Ontario", "Canada"),
    "Ottawa": ("Ontario", "Canada"),
    "Mississauga": ("Ontario", "Canada"),
    "Brampton": ("Ontario", "Canada"),
    "Hamilton": ("Ontario", "Canada"),
    "London": ("Ontario", "Canada"),
    "Markham": ("Ontario", "Canada"),
    "Vaughan": ("Ontario", "Canada"),
    "Kitchener": ("Ontario", "Canada"),
    "Windsor": ("Ontario", "Canada"),
    "Kingston": ("Ontario", "Canada"),
    "Waterloo": ("Ontario", "Canada"),
    "Guelph": ("Ontario", "Canada"),
    "Niagara Falls": ("Ontario", "Canada"),
    "Oakville": ("Ontario", "Canada"),
    "Burlington": ("Ontario", "Canada"),
    "Oshawa": ("Ontario", "Canada"),

    # --- British Columbia, Canada ---
    "Vancouver": ("British Columbia", "Canada"),
    "Victoria": ("British Columbia", "Canada"),
    "Surrey": ("British Columbia", "Canada"),
    "Burnaby": ("British Columbia", "Canada"),
    "Richmond": ("British Columbia", "Canada"),
    "Kelowna": ("British Columbia", "Canada"),
    "Coquitlam": ("British Columbia", "Canada"),
    "Nanaimo": ("British Columbia", "Canada"),

    # --- Quebec, Canada ---
    "Montreal": ("Quebec", "Canada"),
    "Quebec City": ("Quebec", "Canada"),
    "Laval": ("Quebec", "Canada"),
    "Gatineau": ("Quebec", "Canada"),
    "Longueuil": ("Quebec", "Canada"),

    # --- Alberta, Canada ---
    "Calgary": ("Alberta", "Canada"),
    "Edmonton": ("Alberta", "Canada"),
    "Red Deer": ("Alberta", "Canada"),
    "Lethbridge": ("Alberta", "Canada"),

    # --- Manitoba, Saskatchewan, Nova Scotia ---
    "Winnipeg": ("Manitoba", "Canada"),
    "Saskatoon": ("Saskatchewan", "Canada"),
    "Regina": ("Saskatchewan", "Canada"),
    "Halifax": ("Nova Scotia", "Canada")
}

MAJOR_US_METROS = [
    ("New York", "New York"),
    ("Los Angeles", "California"),
    ("Chicago", "Illinois"),
    ("San Francisco", "California"),
    ("Houston", "Texas"),
    ("Miami", "Florida"),
    ("Dallas", "Texas"),
    ("Seattle", "Washington"),
    ("Austin", "Texas"),
    ("Boston", "Massachusetts"),
    ("Atlanta", "Georgia"),
    ("Philadelphia", "Pennsylvania"),
    ("Denver", "Colorado"),
    ("Phoenix", "Arizona"),
    ("San Diego", "California")
]

MAJOR_CA_METROS = [
    ("Toronto", "Ontario"),
    ("Vancouver", "British Columbia"),
    ("Montreal", "Quebec"),
    ("Ottawa", "Ontario"),
    ("Calgary", "Alberta"),
    ("Edmonton", "Alberta"),
    ("Mississauga", "Ontario"),
    ("Brampton", "Ontario"),
    ("Victoria", "British Columbia"),
    ("Halifax", "Nova Scotia"),
    ("Winnipeg", "Manitoba")
]

MAJOR_BOTH_METROS = [
    ("New York", "New York", "United States"),
    ("Toronto", "Ontario", "Canada"),
    ("Los Angeles", "California", "United States"),
    ("Vancouver", "British Columbia", "Canada"),
    ("Chicago", "Illinois", "United States"),
    ("Montreal", "Quebec", "Canada"),
    ("San Francisco", "California", "United States"),
    ("Ottawa", "Ontario", "Canada"),
    ("Houston", "Texas", "United States"),
    ("Calgary", "Alberta", "Canada"),
    ("Miami", "Florida", "United States"),
    ("Dallas", "Texas", "United States"),
    ("Seattle", "Washington", "United States"),
    ("Austin", "Texas", "United States"),
    ("Boston", "Massachusetts", "United States")
]

def resolve_geographic_location(
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    index_hint: int = 0
) -> Tuple[str, str, str]:
    """
    Returns (clean_city, clean_state, clean_country) guaranteeing 100% geographic consistency.
    Never outputs 'United States' as a city name or misaligns city and state.
    """
    clean_city = (city or "").strip()
    clean_state = (state or "").strip()
    clean_country = (country or "").strip()

    # 1. Clean country
    is_ca = "canada" in clean_country.lower() and "united" not in clean_country.lower() and "america" not in clean_country.lower() and "usa" not in clean_country.lower()
    is_us = ("united states" in clean_country.lower() or "usa" in clean_country.lower()) and not is_ca

    # 2. If a specific city is provided, check authoritative map
    if clean_city and clean_city.lower() not in ["all", "all cities", "united states", "canada", "america & canada"]:
        # Strip common state suffixes from city name
        clean_name = clean_city.split(",")[0].strip()
        if clean_name in CITY_STATE_COUNTRY_MAP:
            mapped_state, mapped_country = CITY_STATE_COUNTRY_MAP[clean_name]
            return clean_name, mapped_state, mapped_country
        for c_key, (m_state, m_country) in CITY_STATE_COUNTRY_MAP.items():
            if c_key.lower() == clean_name.lower():
                return c_key, m_state, m_country

        # Custom city not in map: infer from state/country
        target_country = "Canada" if is_ca else "United States"
        target_state = clean_state if (clean_state and clean_state.lower() not in ["all", "all states/provinces"]) else ("Ontario" if target_country == "Canada" else "California")
        return clean_name, target_state, target_country

    # 3. If a specific state is provided (and no city)
    if clean_state and clean_state.lower() not in ["all", "all states/provinces", "all states"]:
        clean_state_name = clean_state.replace(" (USA)", "").replace(" (Canada)", "").split("(")[0].strip()
        # Find first city in that state
        for c_key, (m_state, m_country) in CITY_STATE_COUNTRY_MAP.items():
            if clean_state_name.lower() in m_state.lower():
                return c_key, m_state, m_country
        target_country = "Canada" if is_ca else "United States"
        return "Metropolitan Area", clean_state_name, target_country

    # 4. If Both Countries, USA, or Canada selected with All Cities
    if is_ca:
        sample = MAJOR_CA_METROS[index_hint % len(MAJOR_CA_METROS)]
        return sample[0], sample[1], "Canada"
    elif is_us:
        sample = MAJOR_US_METROS[index_hint % len(MAJOR_US_METROS)]
        return sample[0], sample[1], "United States"
    else:
        sample = MAJOR_BOTH_METROS[index_hint % len(MAJOR_BOTH_METROS)]
        return sample[0], sample[1], sample[2]
