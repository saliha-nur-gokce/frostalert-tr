from pathlib import Path

# ---------------------------------------------------------------------------
# File paths  (relative — works locally and on Streamlit Cloud)
# ---------------------------------------------------------------------------
_BASE = Path(__file__).parent

MAIN_DATA_PATH = str(_BASE / "data" / "thesis_dataset_deflated_final.csv")
COORDS_PATH    = str(_BASE / "data" / "city_coordinates.csv")

GEOJSON_PATH = _BASE / "data" / "turkey_provinces.geojson"
GEOJSON_URL  = "https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/geo/tr-cities-utf8.json"

# ---------------------------------------------------------------------------
# Model parameters
# ---------------------------------------------------------------------------
FROST_THRESHOLD    = -2.0
FORECAST_DAYS      = 16
HISTORICAL_YEARS        = [2022, 2023, 2024]   # used for production norms only
EXPOSURE_YEARS_FULL     = list(range(2014, 2025))  # used for full historical exposure
WINTER_MONTHS      = [11, 12, 1, 2, 3]

# ---------------------------------------------------------------------------
# Sensitivity table (Sj = Lag1 coefficient × 100, verified May 2026)
# flag: None | "insufficient_signal" | "zero_response"
# ---------------------------------------------------------------------------
SENSITIVITY_TABLE = {
    "Domates":  {"sj": 15.79, "flag": None,                  "category": "Vegetables"},
    "Biber":    {"sj": 10.61, "flag": None,                  "category": "Vegetables"},
    "Patlıcan": {"sj": 16.93, "flag": None,                  "category": "Vegetables"},
    "Hıyar":    {"sj": 14.18, "flag": None,                  "category": "Vegetables"},
    "Ispanak":  {"sj":  5.06, "flag": None,                  "category": "Vegetables"},
    "Roka":     {"sj":  9.64, "flag": None,                  "category": "Vegetables"},
    "Turp":     {"sj":  2.58, "flag": None,                  "category": "Vegetables"},
    "Mandalina":{"sj":  2.52, "flag": None,                  "category": "Citrus"},
    "Nar":      {"sj":  6.08, "flag": None,                  "category": "Citrus/Other"},
    "Portakal": {"sj":  0.0,  "flag": "insufficient_signal", "category": "Citrus"},
    "Elma":     {"sj":  0.0,  "flag": "insufficient_signal", "category": "Pome"},
    "Kiraz":    {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
    "Vişne":    {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
    "Kayısı":   {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
    "Şeftali":  {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
    "Erik":     {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
    "Çilek":    {"sj":  0.0,  "flag": "zero_response",       "category": "Stone fruit"},
}

PRODUCT_BASKET = list(SENSITIVITY_TABLE.keys())

PRODUCT_DISPLAY_NAMES = {
    "Domates":   "Tomato",
    "Biber":     "Pepper",
    "Patlıcan":  "Eggplant",
    "Hıyar":     "Cucumber",
    "Ispanak":   "Spinach",
    "Roka":      "Arugula",
    "Turp":      "Radish",
    "Mandalina": "Mandarin",
    "Nar":       "Pomegranate",
    "Portakal":  "Orange",
    "Elma":      "Apple",
    "Kiraz":     "Cherry",
    "Vişne":     "Sour Cherry",
    "Kayısı":    "Apricot",
    "Şeftali":   "Peach",
    "Erik":      "Plum",
    "Çilek":     "Strawberry",
}

# Mapping from product short name to the substring used to filter Product_Name column
PRODUCT_FILTER_MAP = {
    "Domates":   "Domates",
    "Biber":     "Biber",
    "Patlıcan":  "Patlıcan",
    "Hıyar":     "Hıyar",
    "Ispanak":   "Ispanak",
    "Roka":      "Roka",
    "Turp":      "Turp",
    "Mandalina": "Mandalina",
    "Nar":       "Nar",
    "Portakal":  "Portakal",
    "Elma":      "Elma",
    "Kiraz":     "Kiraz",
    "Vişne":     "Vişne",
    "Kayısı":    "Kayısı",
    "Şeftali":   "Şeftali",
    "Erik":      "Erik",
    "Çilek":     "Çilek",
}

# ---------------------------------------------------------------------------
# GeoJSON name → dataset City name corrections (where they differ)
# ---------------------------------------------------------------------------
GEOJSON_TO_CITY = {
    "Afyon":            "Afyonkarahisar",
    "K.Maraş":          "Kahramanmaraş",
    "Kahraman Maraş":   "Kahramanmaraş",
    "Zonguldak":        "Zonguldak",
}

# ---------------------------------------------------------------------------
# Map display settings
# ---------------------------------------------------------------------------
MAP_CENTER  = {"lat": 39.0, "lon": 35.5}
MAP_ZOOM    = 5.0
MAP_STYLE   = "carto-darkmatter"
COLOR_SCALE = "YlOrRd"
