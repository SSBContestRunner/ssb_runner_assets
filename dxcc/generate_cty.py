"""Rebuild the bundled cty asset from the AD1C cty.dat.

Source: https://www.country-files.com/cty/cty.dat

The previously bundled Club Log XML was stale and mapped many prefixes to the
wrong entity (K4/K6/K7 -> Puerto Rico/Hawaii/Alaska, 9A -> San Marino,
R2/R5/R7 -> Ukraine/Kazakhstan/Kaliningrad, DL -> the deleted "Germany" entity).
This script rebuilds the asset from cty.dat so <adif>/<cqz>/<cont>/<ituz> are
mutually consistent and current.

cty.dat carries no ADIF entity code, so ADIF_BY_ENTITY below pins cty.dat's
entity name to its ADIF code (taken from the previous asset; the four special
stations left out - Vienna Intl Ctr, Shetland Is, Sicily, Bear Is - fall back
to their parent prefix, which is correct for callsigns).

Usage: generate_cty.py <cty.dat> <out.xml.gz>
"""

import gzip
import re
import sys
import xml.etree.ElementTree as ET

CTY_DAT = sys.argv[1]
OUT = sys.argv[2]

TOKEN_RE = re.compile(r"^([=*]?)(.+?)(?:\((\d+)\))?(?:\[(\d+)\])?$")

ADIF_BY_ENTITY = {
    'Afghanistan': 3,
    'African Italy': 248,
    'Agalega & St. Brandon': 4,
    'Aland Islands': 5,
    'Alaska': 6,
    'Albania': 7,
    'Algeria': 400,
    'American Samoa': 9,
    'Amsterdam & St. Paul Is.': 10,
    'Andaman & Nicobar Is.': 11,
    'Andorra': 203,
    'Angola': 401,
    'Anguilla': 12,
    'Annobon Island': 195,
    'Antarctica': 13,
    'Antigua & Barbuda': 94,
    'Argentina': 100,
    'Armenia': 14,
    'Aruba': 91,
    'Ascension Island': 205,
    'Asiatic Russia': 15,
    'Asiatic Turkey': 390,
    'Austral Islands': 508,
    'Australia': 150,
    'Austria': 206,
    'Aves Island': 17,
    'Azerbaijan': 18,
    'Azores': 149,
    'Bahamas': 60,
    'Bahrain': 304,
    'Baker & Howland Islands': 20,
    'Balearic Islands': 21,
    'Banaba Island': 490,
    'Bangladesh': 305,
    'Barbados': 62,
    'Belarus': 27,
    'Belgium': 209,
    'Belize': 66,
    'Benin': 416,
    'Bermuda': 64,
    'Bhutan': 306,
    'Bolivia': 104,
    'Bonaire': 520,
    'Bosnia-Herzegovina': 501,
    'Botswana': 402,
    'Bouvet': 24,
    'Brazil': 108,
    'British Virgin Islands': 65,
    'Brunei Darussalam': 345,
    'Bulgaria': 212,
    'Burkina Faso': 480,
    'Burundi': 404,
    'Cabo Verde': 81,
    'Cambodia': 312,
    'Cameroon': 406,
    'Canada': 1,
    'Canary Islands': 29,
    'Cayman Islands': 69,
    'Central African Republic': 408,
    'Central Kiribati': 31,
    'Ceuta & Melilla': 32,
    'Chad': 410,
    'Chagos Islands': 33,
    'Chatham Islands': 34,
    'Chesterfield Islands': 512,
    'Chile': 112,
    'China': 318,
    'Christmas Island': 35,
    'Clipperton Island': 36,
    'Cocos (Keeling) Islands': 38,
    'Cocos Island': 37,
    'Colombia': 116,
    'Comoros': 411,
    'Conway Reef': 489,
    'Corsica': 214,
    'Costa Rica': 308,
    "Cote d'Ivoire": 428,
    'Crete': 40,
    'Croatia': 497,
    'Crozet Island': 41,
    'Cuba': 70,
    'Curacao': 517,
    'Cyprus': 215,
    'Czech Republic': 503,
    'DPR of Korea': 344,
    'Dem. Rep. of the Congo': 414,
    'Denmark': 221,
    'Desecheo Island': 43,
    'Djibouti': 382,
    'Dodecanese': 45,
    'Dominica': 95,
    'Dominican Republic': 72,
    'Ducie Island': 513,
    'East Malaysia': 46,
    'Easter Island': 47,
    'Eastern Kiribati': 48,
    'Ecuador': 120,
    'Egypt': 478,
    'El Salvador': 74,
    'England': 223,
    'Equatorial Guinea': 49,
    'Eritrea': 51,
    'Estonia': 52,
    'Ethiopia': 53,
    'European Russia': 54,
    'European Turkey': 390,
    'Falkland Islands': 141,
    'Faroe Islands': 222,
    'Fed. Rep. of Germany': 230,
    'Fernando de Noronha': 56,
    'Fiji': 176,
    'Finland': 224,
    'France': 227,
    'Franz Josef Land': 61,
    'French Guiana': 63,
    'French Polynesia': 175,
    'Gabon': 420,
    'Galapagos Islands': 71,
    'Georgia': 75,
    'Ghana': 424,
    'Gibraltar': 233,
    'Glorioso Islands': 99,
    'Greece': 236,
    'Greenland': 237,
    'Grenada': 77,
    'Guadeloupe': 79,
    'Guam': 103,
    'Guantanamo Bay': 105,
    'Guatemala': 76,
    'Guernsey': 106,
    'Guinea': 107,
    'Guinea-Bissau': 109,
    'Guyana': 129,
    'Haiti': 78,
    'Hawaii': 110,
    'Heard Island': 111,
    'Honduras': 80,
    'Hong Kong': 321,
    'Hungary': 239,
    'ITU HQ': 117,
    'Iceland': 242,
    'India': 324,
    'Indonesia': 327,
    'Iran': 330,
    'Iraq': 333,
    'Ireland': 245,
    'Isle of Man': 114,
    'Israel': 336,
    'Italy': 248,
    'Jamaica': 82,
    'Jan Mayen': 118,
    'Japan': 339,
    'Jersey': 122,
    'Johnston Island': 123,
    'Jordan': 342,
    'Juan Fernandez Islands': 125,
    'Juan de Nova, Europa': 124,
    'Kaliningrad': 126,
    'Kazakhstan': 130,
    'Kenya': 430,
    'Kerguelen Islands': 131,
    'Kermadec Islands': 133,
    'Kingdom of Eswatini': 468,
    'Kure Island': 138,
    'Kuwait': 348,
    'Kyrgyzstan': 135,
    'Lakshadweep Islands': 142,
    'Laos': 143,
    'Latvia': 145,
    'Lebanon': 354,
    'Lesotho': 432,
    'Liberia': 434,
    'Libya': 436,
    'Liechtenstein': 251,
    'Lithuania': 146,
    'Lord Howe Island': 147,
    'Luxembourg': 254,
    'Macao': 152,
    'Macquarie Island': 153,
    'Madagascar': 438,
    'Madeira Islands': 256,
    'Malawi': 440,
    'Maldives': 159,
    'Mali': 442,
    'Malpelo Island': 161,
    'Malta': 257,
    'Mariana Islands': 166,
    'Market Reef': 167,
    'Marquesas Islands': 509,
    'Marshall Islands': 168,
    'Martinique': 84,
    'Mauritania': 444,
    'Mauritius': 165,
    'Mayotte': 169,
    'Mellish Reef': 171,
    'Mexico': 50,
    'Micronesia': 173,
    'Midway Island': 174,
    'Minami Torishima': 177,
    'Moldova': 179,
    'Monaco': 260,
    'Mongolia': 363,
    'Montenegro': 514,
    'Montserrat': 96,
    'Morocco': 446,
    'Mount Athos': 180,
    'Mozambique': 181,
    'Myanmar': 309,
    'N.Z. Subantarctic Is.': 16,
    'Namibia': 464,
    'Nauru': 157,
    'Navassa Island': 182,
    'Nepal': 369,
    'Netherlands': 263,
    'New Caledonia': 162,
    'New Zealand': 170,
    'Nicaragua': 86,
    'Niger': 187,
    'Nigeria': 450,
    'Niue': 188,
    'Norfolk Island': 189,
    'North Cook Islands': 191,
    'North Macedonia': 502,
    'Northern Ireland': 265,
    'Norway': 266,
    'Ogasawara': 192,
    'Oman': 370,
    'Pakistan': 372,
    'Palau': 22,
    'Palestine': 510,
    'Palmyra & Jarvis Islands': 197,
    'Panama': 88,
    'Papua New Guinea': 163,
    'Paraguay': 132,
    'Peru': 136,
    'Peter 1 Island': 199,
    'Philippines': 375,
    'Pitcairn Island': 172,
    'Poland': 269,
    'Portugal': 272,
    'Pr. Edward & Marion Is.': 201,
    'Pratas Island': 505,
    'Puerto Rico': 202,
    'Qatar': 376,
    'Republic of Korea': 137,
    'Republic of Kosovo': 522,
    'Republic of South Sudan': 521,
    'Republic of the Congo': 412,
    'Reunion Island': 453,
    'Revillagigedo': 204,
    'Rodriguez Island': 207,
    'Romania': 275,
    'Rotuma Island': 460,
    'Rwanda': 454,
    'Saba & St. Eustatius': 519,
    'Sable Island': 211,
    'Samoa': 190,
    'San Andres & Providencia': 216,
    'San Felix & San Ambrosio': 217,
    'San Marino': 278,
    'Sao Tome & Principe': 219,
    'Sardinia': 225,
    'Saudi Arabia': 378,
    'Scarborough Reef': 506,
    'Scotland': 279,
    'Senegal': 456,
    'Serbia': 296,
    'Seychelles': 379,
    'Sierra Leone': 458,
    'Singapore': 381,
    'Sint Maarten': 518,
    'Slovak Republic': 504,
    'Slovenia': 499,
    'Solomon Islands': 185,
    'Somalia': 232,
    'South Africa': 462,
    'South Cook Islands': 234,
    'South Georgia Island': 235,
    'South Orkney Islands': 238,
    'South Sandwich Islands': 240,
    'South Shetland Islands': 241,
    'Sov Mil Order of Malta': 246,
    'Spain': 281,
    'Spratly Islands': 247,
    'Sri Lanka': 315,
    'St. Barthelemy': 516,
    'St. Helena': 250,
    'St. Kitts & Nevis': 249,
    'St. Lucia': 97,
    'St. Martin': 213,
    'St. Paul Island': 252,
    'St. Peter & St. Paul': 253,
    'St. Pierre & Miquelon': 277,
    'St. Vincent': 137,
    'Sudan': 466,
    'Suriname': 140,
    'Svalbard': 259,
    'Swains Island': 515,
    'Sweden': 284,
    'Switzerland': 287,
    'Syria': 384,
    'Taiwan': 386,
    'Tajikistan': 262,
    'Tanzania': 470,
    'Temotu Province': 507,
    'Thailand': 387,
    'The Gambia': 422,
    'Timor - Leste': 511,
    'Togo': 483,
    'Tokelau Islands': 270,
    'Tonga': 160,
    'Trindade & Martim Vaz': 273,
    'Trinidad & Tobago': 90,
    'Tristan da Cunha & Gough': 274,
    'Tromelin Island': 276,
    'Tunisia': 474,
    'Turkmenistan': 280,
    'Turks & Caicos Islands': 89,
    'Tuvalu': 282,
    'UK Base Areas on Cyprus': 283,
    'US Virgin Islands': 285,
    'Uganda': 286,
    'Ukraine': 288,
    'United Arab Emirates': 391,
    'United Nations HQ': 289,
    'United States': 291,
    'Uruguay': 144,
    'Uzbekistan': 292,
    'Vanuatu': 158,
    'Vatican City': 295,
    'Venezuela': 148,
    'Vietnam': 293,
    'Wake Island': 297,
    'Wales': 294,
    'Wallis & Futuna Islands': 298,
    'West Malaysia': 299,
    'Western Kiribati': 301,
    'Western Sahara': 302,
    'Willis Island': 303,
    'Yemen': 492,
    'Zambia': 482,
    'Zimbabwe': 452,
}


def parse_cty(path):
    entities, cur = [], None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if not line[0].isspace():
            parts = line.split(":")
            if len(parts) < 8:
                continue
            cur = {
                "name": parts[0].strip(),
                "cq": int(parts[1]),
                "itu": int(parts[2]),
                "cont": parts[3].strip(),
                "primary": parts[-2].strip(),
                "tokens": [],
            }
            entities.append(cur)
            continue
        for tok in line.strip().rstrip(";").split(","):
            tok = tok.strip()
            if not tok:
                continue
            m = TOKEN_RE.match(tok)
            if not m:
                continue
            marker, name, cq, itu = m.groups()
            if marker == "=":
                # exact-call overrides cannot be keyed by prefix; the app
                # resolves callsigns by prefix, so they are skipped.
                continue
            cur["tokens"].append(
                (name, int(cq) if cq else cur["cq"], int(itu) if itu else cur["itu"])
            )
    return entities


def main():
    entities = parse_cty(CTY_DAT)
    missed = [e["name"] for e in entities if e["name"] not in ADIF_BY_ENTITY]
    for name in missed:
        print(f"warning: no ADIF code for {name!r}; its prefixes are skipped")

    seen, records = set(), []
    for e in entities:
        adif = ADIF_BY_ENTITY.get(e["name"])
        if adif is None:
            continue
        tokens = list(e["tokens"])
        if e["primary"]:
            tokens.insert(0, (e["primary"], e["cq"], e["itu"]))
        for call, cq, itu in tokens:
            if call.lower() in seen:
                continue
            seen.add(call.lower())
            records.append({"call": call, "entity": e["name"], "adif": adif,
                            "cqz": cq, "cont": e["cont"], "ituz": itu})

    root = ET.Element("clublog")
    entities_el = ET.SubElement(root, "entities")
    for e in entities:
        adif = ADIF_BY_ENTITY.get(e["name"])
        if adif is None:
            continue
        el = ET.SubElement(entities_el, "entity")
        ET.SubElement(el, "adif").text = str(adif)
        ET.SubElement(el, "name").text = e["name"]
        ET.SubElement(el, "prefix").text = e["primary"]
        ET.SubElement(el, "cqz").text = str(e["cq"])
        ET.SubElement(el, "cont").text = e["cont"]
        ET.SubElement(el, "deleted").text = "false"

    prefixes_el = ET.SubElement(root, "prefixes")
    for index, rec in enumerate(records, start=1):
        p = ET.SubElement(prefixes_el, "prefix", {"record": str(index)})
        ET.SubElement(p, "call").text = rec["call"]
        ET.SubElement(p, "entity").text = rec["entity"]
        ET.SubElement(p, "adif").text = str(rec["adif"])
        ET.SubElement(p, "cqz").text = str(rec["cqz"])
        ET.SubElement(p, "cont").text = rec["cont"]
        ET.SubElement(p, "ituz").text = str(rec["ituz"])

    with open(OUT, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as fh:
            ET.ElementTree(root).write(fh, encoding="utf-8")

    print(f"entities={len(entities)} prefix_records={len(records)} -> {OUT}")


main()
