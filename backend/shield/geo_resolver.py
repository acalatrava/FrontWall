import logging
import os
from functools import lru_cache
from pathlib import Path
from starlette.requests import Request

logger = logging.getLogger("frontwall.shield.geo_resolver")

_geoip_reader = None
_geoip_available = False


def _init_geoip():
    """Try to initialise the optional MaxMind GeoIP reader."""
    global _geoip_reader, _geoip_available
    try:
        import maxminddb  # noqa: F811
    except ImportError:
        logger.info("maxminddb not installed – GeoIP fallback disabled")
        return

    db_path = os.environ.get("GEOIP_DB_PATH", "/data/GeoLite2-Country.mmdb")
    if not Path(db_path).exists():
        logger.info("GeoIP database not found at %s – GeoIP fallback disabled", db_path)
        return

    try:
        _geoip_reader = maxminddb.open_database(db_path)
        _geoip_available = True
        logger.info("GeoIP database loaded from %s", db_path)
    except Exception as exc:
        logger.warning("Failed to open GeoIP database: %s", exc)


_init_geoip()


@lru_cache(maxsize=8192)
def _lookup_ip(ip: str) -> str | None:
    """Return the ISO 3166-1 alpha-2 country code for an IP address."""
    if not _geoip_reader:
        return None
    try:
        result = _geoip_reader.get(ip)
        if result and "country" in result:
            return result["country"].get("iso_code")
    except Exception:
        pass
    return None


def get_country_code(request: Request, client_ip: str) -> str | None:
    """Resolve the country code for a request.

    Priority:
      1. CF-IPCountry header (Cloudflare – zero latency)
      2. X-Country-Code header (other CDNs/proxies)
      3. Local GeoIP database lookup (if available)
    """
    cf_country = request.headers.get("cf-ipcountry")
    if cf_country and cf_country.upper() not in ("XX", "T1"):
        return cf_country.upper()

    x_country = request.headers.get("x-country-code")
    if x_country and len(x_country) == 2:
        return x_country.upper()

    return _lookup_ip(client_ip)


COUNTRY_MAP = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AS": "American Samoa",
    "AD": "Andorra", "AO": "Angola", "AG": "Antigua and Barbuda", "AR": "Argentina",
    "AM": "Armenia", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan",
    "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados",
    "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin",
    "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BW": "Botswana",
    "BR": "Brazil", "BN": "Brunei", "BG": "Bulgaria", "BF": "Burkina Faso",
    "BI": "Burundi", "KH": "Cambodia", "CM": "Cameroon", "CA": "Canada",
    "CV": "Cape Verde", "CF": "Central African Republic", "TD": "Chad", "CL": "Chile",
    "CN": "China", "CO": "Colombia", "KM": "Comoros", "CG": "Congo",
    "CD": "DR Congo", "CR": "Costa Rica", "CI": "Ivory Coast", "HR": "Croatia",
    "CU": "Cuba", "CY": "Cyprus", "CZ": "Czech Republic", "DK": "Denmark",
    "DJ": "Djibouti", "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador",
    "EG": "Egypt", "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea",
    "EE": "Estonia", "SZ": "Eswatini", "ET": "Ethiopia", "FJ": "Fiji",
    "FI": "Finland", "FR": "France", "GA": "Gabon", "GM": "Gambia",
    "GE": "Georgia", "DE": "Germany", "GH": "Ghana", "GR": "Greece",
    "GD": "Grenada", "GT": "Guatemala", "GN": "Guinea", "GW": "Guinea-Bissau",
    "GY": "Guyana", "HT": "Haiti", "HN": "Honduras", "HK": "Hong Kong",
    "HU": "Hungary", "IS": "Iceland", "IN": "India", "ID": "Indonesia",
    "IR": "Iran", "IQ": "Iraq", "IE": "Ireland", "IL": "Israel",
    "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JO": "Jordan",
    "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KP": "North Korea",
    "KR": "South Korea", "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos",
    "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho", "LR": "Liberia",
    "LY": "Libya", "LI": "Liechtenstein", "LT": "Lithuania", "LU": "Luxembourg",
    "MO": "Macau", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia",
    "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands",
    "MR": "Mauritania", "MU": "Mauritius", "MX": "Mexico", "FM": "Micronesia",
    "MD": "Moldova", "MC": "Monaco", "MN": "Mongolia", "ME": "Montenegro",
    "MA": "Morocco", "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia",
    "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand",
    "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "MK": "North Macedonia",
    "NO": "Norway", "OM": "Oman", "PK": "Pakistan", "PW": "Palau",
    "PS": "Palestine", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay",
    "PE": "Peru", "PH": "Philippines", "PL": "Poland", "PT": "Portugal",
    "QA": "Qatar", "RO": "Romania", "RU": "Russia", "RW": "Rwanda",
    "KN": "Saint Kitts and Nevis", "LC": "Saint Lucia", "VC": "Saint Vincent",
    "WS": "Samoa", "SM": "San Marino", "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles",
    "SL": "Sierra Leone", "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia",
    "SB": "Solomon Islands", "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan",
    "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan", "SR": "Suriname",
    "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan",
    "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand", "TL": "Timor-Leste",
    "TG": "Togo", "TO": "Tonga", "TT": "Trinidad and Tobago", "TN": "Tunisia",
    "TR": "Turkey", "TM": "Turkmenistan", "TV": "Tuvalu", "UG": "Uganda",
    "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu",
    "VA": "Vatican City", "VE": "Venezuela", "VN": "Vietnam", "YE": "Yemen",
    "ZM": "Zambia", "ZW": "Zimbabwe",
}

HIGH_RISK_COUNTRIES = [
    "CN", "RU", "KP", "IR", "NG", "PK", "BD", "VN", "UA", "IN",
    "ID", "BR", "TH", "RO", "BG",
]
