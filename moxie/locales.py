"""The Locale tuple and its ready-made values (Spec section 5).

A Locale is a plain tuple of separators, date conventions, and names; the defaults are en_us.  The tuple declaration
that goes into the prelude is generated from this table so the two cannot drift apart.
"""

ORDER = ["decimal", "group", "date_order", "date_sep", "hour24",
         "days", "short_days", "months", "short_months", "am_pm"]

EN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EN_SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
EN_SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DEFAULT = {"decimal": ".", "group": ",", "date_order": "mdy", "date_sep": "/", "hour24": False,
           "days": EN_DAYS, "short_days": EN_SHORT_DAYS, "months": EN_MONTHS, "short_months": EN_SHORT_MONTHS,
           "am_pm": ["AM", "PM"]}

VALUES = {
    "en_us": {},
    "en_gb": {"date_order": "dmy", "hour24": True},
    "de_de": {"decimal": ",", "group": ".", "date_order": "dmy", "date_sep": ".", "hour24": True,
              "days": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
              "short_days": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
              "months": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
                         "November", "Dezember"],
              "short_months": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]},
    "fr_fr": {"decimal": ",", "group": " ", "date_order": "dmy", "hour24": True,
              "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
              "short_days": ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"],
              "months": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
                         "novembre", "décembre"],
              "short_months": ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]},
    "es_es": {"decimal": ",", "group": ".", "date_order": "dmy", "hour24": True,
              "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
              "short_days": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],
              "months": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
                         "noviembre", "diciembre"],
              "short_months": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]},
}


def _lit(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return "List(" + ", ".join(_lit(x) for x in v) + ")"


def tuple_source():
    """The moxie source of `tuple Locale`, with the en_us values as the field defaults."""
    types = {"decimal": "String", "group": "String", "date_order": "String", "date_sep": "String", "hour24": "Bool"}
    lines = ["tuple Locale:"]
    for k in ORDER:
        lines.append(f"  {k}: {types.get(k, 'List[String]')} = {_lit(DEFAULT[k])}")
    return "\n".join(lines) + "\n"


def full(name):
    return {**DEFAULT, **VALUES[name]}
