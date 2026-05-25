from pathlib import Path

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
MAIN_DATA_PATH = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/thesis_dataset_deflated_final.csv"
COORDS_PATH    = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/city_coordinates.csv"
WHISKER_PATH   = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/projectFinal/HeterogeneousImpactofFrostShocksonPrices.png"
EVENT_STUDY_PATH = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/graphs_agriculture/ag_event_study.png"

GEOJSON_PATH = Path(__file__).parent / "data" / "turkey_provinces.geojson"
GEOJSON_URL  = "https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/geo/tr-cities-utf8.json"

# ---------------------------------------------------------------------------
# Model parameters
# ---------------------------------------------------------------------------
FROST_THRESHOLD    = -2.0
FORECAST_DAYS      = 16
HISTORICAL_YEARS   = [2022, 2023, 2024]
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
MAP_STYLE   = "carto-positron"
COLOR_SCALE = "YlOrRd"
