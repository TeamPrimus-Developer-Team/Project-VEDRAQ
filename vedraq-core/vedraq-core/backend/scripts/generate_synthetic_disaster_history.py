"""
Generate synthetic 10-year disaster history (2017-2026) for VEDRAQ scenarios:
- Varanasi (Z01 - Z15)
- Nepal (N01 - N10)
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

VARANASI_HISTORY = {
    "Z01": [
        {
            "year": 2017,
            "type": "Monsoon Riverine Flood",
            "severity": "High",
            "description": "Ganga backflow submerged lower riparian agriculture plots and flooded primary access roads.",
            "affectedPopulation": 2400,
            "duration": "6 days",
            "outcome": "Water subsided; relief boats deployed"
        },
        {
            "year": 2018,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "Prolonged 45°C temperatures led to acute drinking water shortages across tube-well clusters.",
            "affectedPopulation": 1800,
            "duration": "12 days",
            "outcome": "Municipal water tankers mobilized"
        },
        {
            "year": 2019,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Intense pre-monsoon shower inundated low-lying settlements for over 48 hours.",
            "affectedPopulation": 1500,
            "duration": "3 days",
            "outcome": "Drainage pumps installed"
        },
        {
            "year": 2021,
            "type": "Flash Inundation",
            "severity": "High",
            "description": "Unprecedented 180mm 24-hour rainfall overwhelmed local canals and cut off northern hamlets.",
            "affectedPopulation": 3100,
            "duration": "5 days",
            "outcome": "Evacuation to higher ground completed"
        },
        {
            "year": 2022,
            "type": "Severe Thunderstorm & Lightning",
            "severity": "Low",
            "description": "Squall wind gusting at 75 km/h knocked down feeder power lines and damaged kutcha dwellings.",
            "affectedPopulation": 750,
            "duration": "14 hours",
            "outcome": "Power grid restored in 24 hours"
        },
        {
            "year": 2024,
            "type": "River Flood",
            "severity": "Critical",
            "description": "Ganga surpassed danger mark by 1.2m, completely submerging 40% of residential structures.",
            "affectedPopulation": 3800,
            "duration": "8 days",
            "outcome": "Mass evacuation and community relief camp set up"
        },
        {
            "year": 2025,
            "type": "Urban Flooding",
            "severity": "High",
            "description": "Monsoon surge inundated internal connecting roads, stranding school buses and commuters.",
            "affectedPopulation": 2600,
            "duration": "4 days",
            "outcome": "Temporary bypass operationalized"
        }
    ],
    "Z02": [
        {
            "year": 2017,
            "type": "Drainage Overflow",
            "severity": "Moderate",
            "description": "Silt build-up in primary storm drain caused knee-deep inundation in western marketplaces.",
            "affectedPopulation": 2800,
            "duration": "3 days",
            "outcome": "Desilting conducted post-event"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "High",
            "description": "Extended heatwave with thermal heat-index exceeding 48°C triggered power grid overloads.",
            "affectedPopulation": 4500,
            "duration": "14 days",
            "outcome": "Cooling centers and hydration posts established"
        },
        {
            "year": 2020,
            "type": "Urban Flooding",
            "severity": "Moderate",
            "description": "Heavy monsoon downpour inundated low-lying housing blocks and basement warehouses.",
            "affectedPopulation": 3200,
            "duration": "4 days",
            "outcome": "Submersible dewatering pumps deployed"
        },
        {
            "year": 2022,
            "type": "Electrical Fire Incident",
            "severity": "Moderate",
            "description": "Transformer burst during heat spike triggered localized commercial hub fire.",
            "affectedPopulation": 1100,
            "duration": "8 hours",
            "outcome": "Contained by fire tenders with zero casualties"
        },
        {
            "year": 2023,
            "type": "Monsoon Waterlogging",
            "severity": "High",
            "description": "Continuous 72-hour rain caused extensive stagnation along main transport arteries.",
            "affectedPopulation": 5200,
            "duration": "5 days",
            "outcome": "Traffic rerouted to peripheral corridors"
        },
        {
            "year": 2025,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "High velocity windstorm uprooted trees and disrupted telecommunication lines.",
            "affectedPopulation": 1400,
            "duration": "18 hours",
            "outcome": "Rapid debris clearance by civic teams"
        }
    ],
    "Z03": [
        {
            "year": 2018,
            "type": "Waterlogging & Road Block",
            "severity": "Moderate",
            "description": "Monsoon overflow inundated connecting link road R4, isolating southern farming hamlets.",
            "affectedPopulation": 1200,
            "duration": "4 days",
            "outcome": "Temporary gravel bund built"
        },
        {
            "year": 2019,
            "type": "Severe Drought-like Conditions",
            "severity": "Moderate",
            "description": "Delayed monsoon caused ground-water depletion and borewell drying across agricultural tracts.",
            "affectedPopulation": 1400,
            "duration": "25 days",
            "outcome": "Emergency tanker distribution organized"
        },
        {
            "year": 2021,
            "type": "Riverine Inundation",
            "severity": "High",
            "description": "Tributary backflow breached village perimeter embankment, flooding homes up to 1 meter.",
            "affectedPopulation": 1850,
            "duration": "6 days",
            "outcome": "Civilians evacuated to Govindpur community hall"
        },
        {
            "year": 2023,
            "type": "Thunderstorm & Lightning Strike",
            "severity": "Low",
            "description": "Severe pre-monsoon thunderstorm damaged rooftop solar installations and cattle sheds.",
            "affectedPopulation": 450,
            "duration": "6 hours",
            "outcome": "Local veterinary and emergency support provided"
        },
        {
            "year": 2024,
            "type": "Urban Flooding",
            "severity": "High",
            "description": "Torrential monsoon spell overwhelmed primary storm channel, stranding over 70% of residents.",
            "affectedPopulation": 1900,
            "duration": "5 days",
            "outcome": "Rescue rafts deployed for dry ration delivery"
        }
    ],
    "Z04": [
        {
            "year": 2017,
            "type": "Severe Heatwave",
            "severity": "High",
            "description": "Intense urban heat island effect drove ambient temperatures to 46.5°C in dense settlements.",
            "affectedPopulation": 4800,
            "duration": "10 days",
            "outcome": "Public health emergency advisories issued"
        },
        {
            "year": 2019,
            "type": "Commercial Substation Fire",
            "severity": "Moderate",
            "description": "Short circuit at commercial grid junction triggered localized power loss and smoke hazards.",
            "affectedPopulation": 1900,
            "duration": "12 hours",
            "outcome": "Successfully doused; circuit breakers replaced"
        },
        {
            "year": 2020,
            "type": "Urban Flash Waterlogging",
            "severity": "Moderate",
            "description": "Cloudburst-like 95mm downpour inundated main bazaar basements within 90 minutes.",
            "affectedPopulation": 3400,
            "duration": "2 days",
            "outcome": "High-capacity diesel pumps deployed"
        },
        {
            "year": 2022,
            "type": "Monsoon Street Flooding",
            "severity": "High",
            "description": "Prolonged monsoon spell submerged Bhelpur crossing and halted secondary emergency transit.",
            "affectedPopulation": 3900,
            "duration": "4 days",
            "outcome": "Ambulance routes diverted to outer ring"
        },
        {
            "year": 2024,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "Gale winds damaged commercial hoardings and caused brief power interruptions.",
            "affectedPopulation": 1200,
            "duration": "10 hours",
            "outcome": "Safety audit ordered for high-rise hoardings"
        },
        {
            "year": 2026,
            "type": "Urban Flooding",
            "severity": "Moderate",
            "description": "Early monsoon storm waterlogging caused traffic gridlock across hospital approaches.",
            "affectedPopulation": 2700,
            "duration": "3 days",
            "outcome": "Traffic police coordinated alternate access corridors"
        }
    ],
    "Z05": [
        {
            "year": 2017,
            "type": "Monsoon River Flood",
            "severity": "High",
            "description": "River swelling submerged lower agricultural fields and isolated 80 households.",
            "affectedPopulation": 1100,
            "duration": "7 days",
            "outcome": "Motorized rescue boats deployed by NDRF"
        },
        {
            "year": 2019,
            "type": "Severe Water Shortage & Heatwave",
            "severity": "Moderate",
            "description": "Extreme summer heat caused local groundwater drawdown and agricultural distress.",
            "affectedPopulation": 900,
            "duration": "18 days",
            "outcome": "Emergency water tankers deployed"
        },
        {
            "year": 2020,
            "type": "Tributary Flood Inundation",
            "severity": "High",
            "description": "Overflow from minor river basin submerged primary access road R6 under 1.5m water.",
            "affectedPopulation": 1300,
            "duration": "8 days",
            "outcome": "Helicopter airdrop of essentials conducted"
        },
        {
            "year": 2022,
            "type": "Monsoon Storm Surge",
            "severity": "Critical",
            "description": "Unprecedented waterlogging and road breach left the zone completely inaccessible by ground.",
            "affectedPopulation": 1450,
            "duration": "11 days",
            "outcome": "Air-corridor airlift mission initiated"
        },
        {
            "year": 2023,
            "type": "Pre-Monsoon Lightning Strikes",
            "severity": "Low",
            "description": "Intense lightning activity damaged agricultural pump sets and temporary shelters.",
            "affectedPopulation": 320,
            "duration": "8 hours",
            "outcome": "Lightning arrestor installation proposed"
        },
        {
            "year": 2024,
            "type": "Severe River Flood",
            "severity": "Critical",
            "description": "Ganga and tributary confluence surge submerged 85% of village residential plots.",
            "affectedPopulation": 1450,
            "duration": "9 days",
            "outcome": "Total population moved to Safe Zone S03"
        },
        {
            "year": 2025,
            "type": "Urban Runoff Waterlogging",
            "severity": "Moderate",
            "description": "Late monsoon excess runoff ponded in settlement depressions for five days.",
            "affectedPopulation": 850,
            "duration": "5 days",
            "outcome": "Dewatering canals dredged"
        }
    ],
    "Z06": [
        {
            "year": 2017,
            "type": "Severe Heatwave",
            "severity": "High",
            "description": "Prolonged heat spell pushed community clinic admissions to historic peaks.",
            "affectedPopulation": 5800,
            "duration": "15 days",
            "outcome": "Hospital surge capacity activated"
        },
        {
            "year": 2018,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Overnight 120mm downpour caused road ponding around temple complex and schools.",
            "affectedPopulation": 4200,
            "duration": "3 days",
            "outcome": "Municipal drainage cleared"
        },
        {
            "year": 2020,
            "type": "Electrical Feeder Fire",
            "severity": "Low",
            "description": "Overheated sub-station transformer sparked localized fire near commercial strip.",
            "affectedPopulation": 1600,
            "duration": "6 hours",
            "outcome": "Fire neutralized; backup grid routed"
        },
        {
            "year": 2021,
            "type": "Urban Flooding",
            "severity": "High",
            "description": "Severe monsoon downpour inundated residential apartment basements and internal roads.",
            "affectedPopulation": 6400,
            "duration": "5 days",
            "outcome": "Emergency dewatering pumps run continuously"
        },
        {
            "year": 2023,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "High winds snapped telecom lines and damaged roadside merchant stalls.",
            "affectedPopulation": 1900,
            "duration": "12 hours",
            "outcome": "Civic maintenance teams restored access"
        },
        {
            "year": 2024,
            "type": "Extreme Heat Surge",
            "severity": "High",
            "description": "Day temperatures touched 47.1°C with severe water pressure drop in municipal mains.",
            "affectedPopulation": 7200,
            "duration": "11 days",
            "outcome": "Rotational water distribution enforced"
        },
        {
            "year": 2025,
            "type": "Monsoon Street Flooding",
            "severity": "Moderate",
            "description": "Clogged storm drains caused 2-foot water accumulation on key transit nodes.",
            "affectedPopulation": 3800,
            "duration": "3 days",
            "outcome": "Rapid clearance of drainage gullies"
        }
    ],
    "Z07": [
        {
            "year": 2018,
            "type": "Monsoon Flooding",
            "severity": "High",
            "description": "Backwater from drainage canal overflowed into eastern residential settlements.",
            "affectedPopulation": 2400,
            "duration": "6 days",
            "outcome": "Temporary embankments reinforced with sandbags"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "High humidity heat wave caused widespread thermal distress among informal workers.",
            "affectedPopulation": 1800,
            "duration": "10 days",
            "outcome": "Community shaded rest shelters set up"
        },
        {
            "year": 2021,
            "type": "Flash Waterlogging",
            "severity": "Moderate",
            "description": "Torrential rain submerged Sikandarpur market area and stalled local vehicles.",
            "affectedPopulation": 1950,
            "duration": "3 days",
            "outcome": "Portable dewatering pumps deployed"
        },
        {
            "year": 2022,
            "type": "Lightning & Heavy Rain",
            "severity": "Low",
            "description": "Multiple lightning strikes accompanied by heavy squall damaged local power poles.",
            "affectedPopulation": 820,
            "duration": "16 hours",
            "outcome": "Power infrastructure repaired promptly"
        },
        {
            "year": 2024,
            "type": "River Inundation & Overflow",
            "severity": "High",
            "description": "Canal breached embankments following upstream discharge, flooding 120 houses.",
            "affectedPopulation": 2800,
            "duration": "7 days",
            "outcome": "Displaced families accommodated in Sikandarpur primary school"
        },
        {
            "year": 2025,
            "type": "Urban Runoff Flooding",
            "severity": "Moderate",
            "description": "Surface runoff from northern slopes submerged local link road R5.",
            "affectedPopulation": 1700,
            "duration": "4 days",
            "outcome": "Drainage gradient deepened"
        }
    ],
    "Z08": [
        {
            "year": 2017,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Railway underpass flooded, blocking vehicular passage between eastern and western sectors.",
            "affectedPopulation": 2100,
            "duration": "3 days",
            "outcome": "Automated pump sump activated"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "Dry heat conditions triggered peak demand on water supply and clinic OPDs.",
            "affectedPopulation": 1950,
            "duration": "9 days",
            "outcome": "Water tanker trips doubled"
        },
        {
            "year": 2021,
            "type": "Urban Flooding",
            "severity": "Moderate",
            "description": "Heavy rainfall caused temporary waterlogging across several low-lying railway quarters.",
            "affectedPopulation": 2160,
            "duration": "3 days",
            "outcome": "Drains cleared by municipal railway authority"
        },
        {
            "year": 2023,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "Gusty winds brought down tree branches and billboard structures along R2 highway.",
            "affectedPopulation": 900,
            "duration": "12 hours",
            "outcome": "Highway cleared within 4 hours"
        },
        {
            "year": 2024,
            "type": "Heavy Monsoon Downpour",
            "severity": "Moderate",
            "description": "Water accumulated in railway colony open yards with temporary power blackouts.",
            "affectedPopulation": 1750,
            "duration": "2 days",
            "outcome": "Submersible pumps drained floodwater"
        }
    ],
    "Z09": [
        {
            "year": 2017,
            "type": "Monsoon Riverine Flood",
            "severity": "High",
            "description": "Lowland paddy fields and rural road R7 submerged under 1.2m of muddy backwater.",
            "affectedPopulation": 2200,
            "duration": "7 days",
            "outcome": "Relief camps operationalized; cattle moved to bund"
        },
        {
            "year": 2019,
            "type": "Severe Drought-like Conditions",
            "severity": "Moderate",
            "description": "Pre-monsoon dry spell dried village ponds and dropped water table by 4 meters.",
            "affectedPopulation": 1600,
            "duration": "22 days",
            "outcome": "Emergency borewell deepening undertaken"
        },
        {
            "year": 2021,
            "type": "Flash Flood Inundation",
            "severity": "High",
            "description": "Sudden cloudburst over basin resulted in swift torrent cutting off southern approach.",
            "affectedPopulation": 2450,
            "duration": "6 days",
            "outcome": "NDRF inflatable boats used for evacuation"
        },
        {
            "year": 2022,
            "type": "Pre-Monsoon Thunderstorm & Lightning",
            "severity": "Low",
            "description": "Lightning strikes destroyed two transformers and killed livestock in open pastures.",
            "affectedPopulation": 650,
            "duration": "14 hours",
            "outcome": "Disaster compensation distributed"
        },
        {
            "year": 2024,
            "type": "Critical River Flood",
            "severity": "Critical",
            "description": "Embankment breach submerged 73% of village homes, knocking out all road connections.",
            "affectedPopulation": 2600,
            "duration": "10 days",
            "outcome": "Total zone evacuation to Safe Zone Delta"
        },
        {
            "year": 2025,
            "type": "Monsoon Waterlogging",
            "severity": "High",
            "description": "Stagnant floodwater blocked sanitation access and contaminated drinking wells.",
            "affectedPopulation": 2100,
            "duration": "6 days",
            "outcome": "Chlorination tablets and mobile RO units distributed"
        }
    ],
    "Z10": [
        {
            "year": 2018,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Excess rainfall clogged roadside ditches, submerging Madanpur Khurd main road.",
            "affectedPopulation": 2600,
            "duration": "3 days",
            "outcome": "Excavators deployed to clear drainage blockages"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "Prolonged high ambient heat affected construction and market workforce.",
            "affectedPopulation": 2200,
            "duration": "11 days",
            "outcome": "Working hours shifted to early morning / evening"
        },
        {
            "year": 2021,
            "type": "Monsoon Flooding",
            "severity": "High",
            "description": "Overflow from nearby irrigation channel submerged 350 ground-floor residences.",
            "affectedPopulation": 3360,
            "duration": "5 days",
            "outcome": "Dewatering pumps operated around the clock"
        },
        {
            "year": 2023,
            "type": "Severe Thunderstorm",
            "severity": "Low",
            "description": "Gale winds uprooted trees along R8 highway and severed power feeds.",
            "affectedPopulation": 1100,
            "duration": "15 hours",
            "outcome": "Clearance teams restored traffic by dawn"
        },
        {
            "year": 2024,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Inundation of peripheral access roads slowed vehicular movement for 72 hours.",
            "affectedPopulation": 2800,
            "duration": "4 days",
            "outcome": "Traffic redirected through bypass lanes"
        },
        {
            "year": 2026,
            "type": "Urban Flooding",
            "severity": "Moderate",
            "description": "Early pre-monsoon storm flooded market basements and low-lying courtyards.",
            "affectedPopulation": 2400,
            "duration": "3 days",
            "outcome": "Portable pumping units deployed"
        }
    ],
    "Z11": [
        {
            "year": 2017,
            "type": "Riverine Flood",
            "severity": "High",
            "description": "Ganga high-tide overflow submerged riverbank hamlets and disrupted road R9.",
            "affectedPopulation": 1500,
            "duration": "7 days",
            "outcome": "Villagers relocated to flood shelter"
        },
        {
            "year": 2019,
            "type": "Extreme Heatwave",
            "severity": "Moderate",
            "description": "Peak summer temperature of 46°C caused borehole yield to drop drastically.",
            "affectedPopulation": 1200,
            "duration": "13 days",
            "outcome": "Emergency water tankers deployed daily"
        },
        {
            "year": 2020,
            "type": "Monsoon Flash Flood",
            "severity": "High",
            "description": "Torrential run-off breached agricultural bunds, flooding 60% of settlements.",
            "affectedPopulation": 1600,
            "duration": "6 days",
            "outcome": "Rescue boats distributed rations and medical kits"
        },
        {
            "year": 2022,
            "type": "Lightning & Squall",
            "severity": "Low",
            "description": "Sudden thunderstorm damaged power distribution transformers.",
            "affectedPopulation": 550,
            "duration": "10 hours",
            "outcome": "Repaired within 18 hours"
        },
        {
            "year": 2024,
            "type": "Catastrophic River Flood",
            "severity": "Critical",
            "description": "Record flood surge completely isolated Khajuri Khas, making road access impassable.",
            "affectedPopulation": 1710,
            "duration": "9 days",
            "outcome": "Evacuation executed via river rescue flotilla"
        },
        {
            "year": 2025,
            "type": "Waterlogging & Siltation",
            "severity": "High",
            "description": "Post-flood silt blocked natural drainage, leaving standing water for over a week.",
            "affectedPopulation": 1400,
            "duration": "8 days",
            "outcome": "Heavy earthmovers engaged for channel dredging"
        }
    ],
    "Z12": [
        {
            "year": 2018,
            "type": "Severe Heatwave",
            "severity": "High",
            "description": "Extended heatwave caused widespread dehydration cases and cattle distress.",
            "affectedPopulation": 2400,
            "duration": "16 days",
            "outcome": "Veterinary and medical relief camps organized"
        },
        {
            "year": 2020,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Temporary inundation of low-lying agricultural fields and peripheral road.",
            "affectedPopulation": 1500,
            "duration": "3 days",
            "outcome": "Natural drainage into depression completed"
        },
        {
            "year": 2021,
            "type": "Drought-like Dry Spell",
            "severity": "Moderate",
            "description": "Prolonged dry interval during monsoon stunted kharif crop growth.",
            "affectedPopulation": 1800,
            "duration": "20 days",
            "outcome": "Subsidized electricity provided for tube-wells"
        },
        {
            "year": 2023,
            "type": "Thunderstorm & Hail",
            "severity": "Low",
            "description": "Isolated hailstorm damaged vegetable orchards and asbestos roofing.",
            "affectedPopulation": 750,
            "duration": "8 hours",
            "outcome": "Damage assessments conducted for relief"
        },
        {
            "year": 2025,
            "type": "Urban Runoff Waterlogging",
            "severity": "Moderate",
            "description": "Heavy monsoon shower caused brief waterlogging along R8 highway junction.",
            "affectedPopulation": 1800,
            "duration": "2 days",
            "outcome": "Drainage outfall cleared by road authority"
        }
    ],
    "Z13": [
        {
            "year": 2017,
            "type": "Heavy Rainfall & Waterlogging",
            "severity": "Moderate",
            "description": "Monsoon downpour submerged village market square and link road R10.",
            "affectedPopulation": 1600,
            "duration": "4 days",
            "outcome": "Excavator cleared culvert debris"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "Scorching temperatures dried community ponds and affected dairy farming.",
            "affectedPopulation": 1400,
            "duration": "12 days",
            "outcome": "Water supply augmented with mobile tankers"
        },
        {
            "year": 2020,
            "type": "Flash Inundation",
            "severity": "High",
            "description": "Drainage breach from highway culvert flooded low-lying residential clusters.",
            "affectedPopulation": 1950,
            "duration": "6 days",
            "outcome": "Sandbag dykes erected by village youth"
        },
        {
            "year": 2022,
            "type": "Severe Lightning Storm",
            "severity": "Moderate",
            "description": "Series of intense lightning strikes damaged telecom tower and rural power lines.",
            "affectedPopulation": 950,
            "duration": "14 hours",
            "outcome": "Restored within 24 hours"
        },
        {
            "year": 2024,
            "type": "Riverine Backflow Flood",
            "severity": "Critical",
            "description": "Ganga tributary backwater submerged 76% of agricultural land and 300 homes.",
            "affectedPopulation": 2100,
            "duration": "8 days",
            "outcome": "Residents moved to Baragaon intermediate school shelter"
        },
        {
            "year": 2025,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Continuous 48-hour rain left water stagnant in unpaved lanes.",
            "affectedPopulation": 1300,
            "duration": "4 days",
            "outcome": "De-watering pumps deployed"
        }
    ],
    "Z14": [
        {
            "year": 2017,
            "type": "Varuna River Flood",
            "severity": "High",
            "description": "Varuna river overflow submerged Chaukaghat bridge approaches and riverside wards.",
            "affectedPopulation": 4200,
            "duration": "6 days",
            "outcome": "Traffic closed on low bridge; rescue boats deployed"
        },
        {
            "year": 2018,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "High humidity heat wave affected dense urban colonies along the river corridor.",
            "affectedPopulation": 3500,
            "duration": "10 days",
            "outcome": "Civic drinking water kiosks opened"
        },
        {
            "year": 2020,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Torrential rain waterlogged major transit crossing, stranding commercial transport.",
            "affectedPopulation": 3900,
            "duration": "3 days",
            "outcome": "Traffic police coordinated alternate routing"
        },
        {
            "year": 2021,
            "type": "Varuna River Overflow",
            "severity": "High",
            "description": "Rapid water level rise inundated hundreds of ground-floor residences and workshops.",
            "affectedPopulation": 4750,
            "duration": "7 days",
            "outcome": "Evacuation carried out to Chaukaghat cultural center"
        },
        {
            "year": 2023,
            "type": "Commercial Fire Outbreak",
            "severity": "Moderate",
            "description": "Fire in timber depot near bridge required 6 fire tenders to prevent residential spread.",
            "affectedPopulation": 1800,
            "duration": "10 hours",
            "outcome": "Fire fully controlled with no loss of life"
        },
        {
            "year": 2024,
            "type": "Monsoon Flood Inundation",
            "severity": "High",
            "description": "Simultaneous Ganga and Varuna swelling caused backflow flooding in 12 colonies.",
            "affectedPopulation": 4750,
            "duration": "6 days",
            "outcome": "Relief camps distributed ready-to-eat meals"
        },
        {
            "year": 2026,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "Gale winds knocked down commercial hoardings and caused brief traffic blockage.",
            "affectedPopulation": 1600,
            "duration": "12 hours",
            "outcome": "Prompt road clearance by municipal crews"
        }
    ],
    "Z15": [
        {
            "year": 2017,
            "type": "Ganga Peak Inundation",
            "severity": "High",
            "description": "Ganga water rose up to Assi Ghat steps and flooded lower residential lanes.",
            "affectedPopulation": 4800,
            "duration": "7 days",
            "outcome": "Boat services suspended; riverside evacuation completed"
        },
        {
            "year": 2018,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Heavy localized monsoon downpour overwhelmed drainage outfalls into the river.",
            "affectedPopulation": 3600,
            "duration": "4 days",
            "outcome": "Drain gates cleared of polythene waste"
        },
        {
            "year": 2019,
            "type": "Severe Heatwave",
            "severity": "Moderate",
            "description": "Severe heat wave affected religious pilgrims, tourists, and resident population.",
            "affectedPopulation": 4100,
            "duration": "11 days",
            "outcome": "Emergency medical tents set up on ghat approaches"
        },
        {
            "year": 2021,
            "type": "Major Ghat Overflow",
            "severity": "Critical",
            "description": "Ganga overflowed by 2 meters, submerging primary ghat markets and entering homes.",
            "affectedPopulation": 5760,
            "duration": "9 days",
            "outcome": "Mass evacuation to upper university hostels"
        },
        {
            "year": 2022,
            "type": "Severe Thunderstorm Squall",
            "severity": "Low",
            "description": "High-velocity river winds capsized anchored dinghies and damaged heritage awnings.",
            "affectedPopulation": 1400,
            "duration": "8 hours",
            "outcome": "Water police recovered all boats"
        },
        {
            "year": 2024,
            "type": "Monsoon River Flood",
            "severity": "Critical",
            "description": "Sustained flood discharge from upstream barrages submerged Assi corridor for over a week.",
            "affectedPopulation": 5760,
            "duration": "8 days",
            "outcome": "Disaster rescue boats ferried essential provisions"
        },
        {
            "year": 2025,
            "type": "Post-Monsoon Water Stagnation",
            "severity": "Moderate",
            "description": "Residual floodwaters in low alleys caused mosquito breeding concerns and access delays.",
            "affectedPopulation": 2900,
            "duration": "5 days",
            "outcome": "Anti-larval fogging and rapid pumping executed"
        }
    ]
}

NEPAL_HISTORY = {
    "N01": [
        {
            "year": 2017,
            "type": "Alpine Flash Flood",
            "severity": "High",
            "description": "Melamchi river surge washed away suspension footbridges and flooded riverside terrace farms.",
            "affectedPopulation": 3200,
            "duration": "5 days",
            "outcome": "Temporary ropeways installed by community"
        },
        {
            "year": 2018,
            "type": "Mountain Slope Landslide",
            "severity": "Moderate",
            "description": "Heavy monsoon rains triggered slope failure, blocking arterial road NR3 for 48 hours.",
            "affectedPopulation": 2100,
            "duration": "3 days",
            "outcome": "Bulldozers cleared boulders and mud"
        },
        {
            "year": 2019,
            "type": "Winter Snowstorm & Freeze",
            "severity": "Moderate",
            "description": "Unseasonal heavy snowfall in upper catchment isolated upper pastures and disrupted communications.",
            "affectedPopulation": 1500,
            "duration": "6 days",
            "outcome": "Winter relief supplies distributed via 4x4 convoys"
        },
        {
            "year": 2021,
            "type": "Catastrophic Debris Torrent",
            "severity": "Critical",
            "description": "Upstream glacial lake outburst and cloudburst triggered massive debris flow destroying 60 buildings.",
            "affectedPopulation": 4200,
            "duration": "14 days",
            "outcome": "Army helicopter rescue operations and emergency shelter established"
        },
        {
            "year": 2022,
            "type": "Monsoon River Flood",
            "severity": "High",
            "description": "Melamchi river swelled again, eroding reinforced riverbanks and threatening valley school.",
            "affectedPopulation": 2800,
            "duration": "5 days",
            "outcome": "Gabion wire mesh wall reinforced"
        },
        {
            "year": 2024,
            "type": "Cloudburst & Flash Flood",
            "severity": "Critical",
            "description": "Intense localized cloudburst dropped 140mm in 2 hours, cutting primary ground access entirely.",
            "affectedPopulation": 4200,
            "duration": "8 days",
            "outcome": "Air corridor airlift activated for medical evacuees"
        },
        {
            "year": 2025,
            "type": "Seismic Tremor & Rockfall",
            "severity": "Moderate",
            "description": "Magnitude 5.1 tremor triggered rockfalls along upper canyon passes, blocking supply vehicles.",
            "affectedPopulation": 1900,
            "duration": "3 days",
            "outcome": "Road cleared by Nepal Army engineers"
        }
    ],
    "N02": [
        {
            "year": 2017,
            "type": "Monsoon Landslide",
            "severity": "High",
            "description": "Steep hillside failure blocked road NR5 and damaged 18 residential stone homes.",
            "affectedPopulation": 3600,
            "duration": "6 days",
            "outcome": "Displaced families sheltered in community hall"
        },
        {
            "year": 2019,
            "type": "Severe Hailstorm & Wind",
            "severity": "Low",
            "description": "Violent squall and hail damaged hillside terrace crops and tin roofs.",
            "affectedPopulation": 1800,
            "duration": "12 hours",
            "outcome": "Emergency roofing sheets distributed"
        },
        {
            "year": 2020,
            "type": "River Flash Flood",
            "severity": "High",
            "description": "Torrential monsoon rains swollen mountain river, flooding riverside market stalls.",
            "affectedPopulation": 4100,
            "duration": "5 days",
            "outcome": "River training work initiated"
        },
        {
            "year": 2022,
            "type": "Major Slope Slump",
            "severity": "Critical",
            "description": "Deep-seated slope reactivation threatened central market ridge with ground fissure movement.",
            "affectedPopulation": 5100,
            "duration": "10 days",
            "outcome": "Partial evacuation to Chautara safe grounds"
        },
        {
            "year": 2023,
            "type": "Forest Fire Incident",
            "severity": "Moderate",
            "description": "Dry spring pine forest fire approached eastern fringe settlements before containment.",
            "affectedPopulation": 2400,
            "duration": "4 days",
            "outcome": "Contained by fire-line cutting and aerial water bucket drop"
        },
        {
            "year": 2024,
            "type": "Monsoon Debris Flow",
            "severity": "High",
            "description": "Gully washout deposited tons of gravel and boulders across agricultural terraces.",
            "affectedPopulation": 3800,
            "duration": "5 days",
            "outcome": "Heavy machinery cleared arterial paths"
        }
    ],
    "N03": [
        {
            "year": 2018,
            "type": "Hillside Mudslide",
            "severity": "Moderate",
            "description": "Continuous rain induced mudslide across foothill road NR4, delaying transit.",
            "affectedPopulation": 2200,
            "duration": "3 days",
            "outcome": "Road cleared in 36 hours"
        },
        {
            "year": 2020,
            "type": "Pre-Monsoon Thunderstorm & Lightning",
            "severity": "Low",
            "description": "High-intensity lightning strikes knocked out ridge telecom repeater towers.",
            "affectedPopulation": 1400,
            "duration": "18 hours",
            "outcome": "Telecom restored via solar backup generator"
        },
        {
            "year": 2021,
            "type": "Flash Flood & Stream Swell",
            "severity": "Moderate",
            "description": "Mountain stream breached culvert, eroding road edge near district hospital.",
            "affectedPopulation": 2900,
            "duration": "4 days",
            "outcome": "Concrete retaining wall constructed"
        },
        {
            "year": 2023,
            "type": "Major Slope Landslide",
            "severity": "High",
            "description": "Heavy monsoon rains caused slope failure above settlement, requiring precautionary evacuation.",
            "affectedPopulation": 3900,
            "duration": "6 days",
            "outcome": "Evacuated to Chautara multipurpose shelter"
        },
        {
            "year": 2025,
            "type": "Winter Cold Wave & Frost",
            "severity": "Low",
            "description": "Sub-zero cold spell caused water pipe freezing and agricultural frost damage.",
            "affectedPopulation": 1700,
            "duration": "8 days",
            "outcome": "Blankets and firewood supplies mobilized"
        }
    ],
    "N04": [
        {
            "year": 2017,
            "type": "Winter Avalanche Threat",
            "severity": "High",
            "description": "High altitude snow avalanche severed mule trail and buried upper outpost storage shed.",
            "affectedPopulation": 1100,
            "duration": "8 days",
            "outcome": "Trail reopened by mountain rescue teams"
        },
        {
            "year": 2019,
            "type": "Alpine Cloudburst",
            "severity": "High",
            "description": "Intense cloudburst washed away two pedestrian wooden bridges, isolating northern settlements.",
            "affectedPopulation": 1600,
            "duration": "6 days",
            "outcome": "Airdrop of medical supplies conducted"
        },
        {
            "year": 2021,
            "type": "Mountain Torrent & Washout",
            "severity": "Critical",
            "description": "Glacial stream overflow destroyed road connection NR6, leaving the zone completely cut off.",
            "affectedPopulation": 2100,
            "duration": "12 days",
            "outcome": "Helicopter airlift established as sole lifeline"
        },
        {
            "year": 2022,
            "type": "Severe Snowstorm & Blizzard",
            "severity": "Moderate",
            "description": "Three feet of snowfall halted all trekking routes and caused livestock losses.",
            "affectedPopulation": 1400,
            "duration": "5 days",
            "outcome": "Snow clearance performed by local volunteers"
        },
        {
            "year": 2024,
            "type": "Massive Rockfall & Slide",
            "severity": "Critical",
            "description": "Seismic activity triggered cliff collapse, blocking the gorge and damaging 85% of infrastructure.",
            "affectedPopulation": 2100,
            "duration": "15 days",
            "outcome": "High-altitude airlift of all vulnerable persons"
        },
        {
            "year": 2025,
            "type": "Flash Flood Inundation",
            "severity": "High",
            "description": "Rapid snowmelt coupled with rainfall eroded valley terrace foundations.",
            "affectedPopulation": 1800,
            "duration": "5 days",
            "outcome": "Erosion prevention wire crates placed"
        }
    ],
    "N05": [
        {
            "year": 2018,
            "type": "Salinadi River Inundation",
            "severity": "High",
            "description": "Salinadi river burst banks, flooding historic peri-urban settlements and brick kilns.",
            "affectedPopulation": 3800,
            "duration": "4 days",
            "outcome": "Rescue teams deployed boats for evacuation"
        },
        {
            "year": 2019,
            "type": "Monsoon Street Waterlogging",
            "severity": "Moderate",
            "description": "Drainage canal overflow inundated agricultural lowlands and connecting link road NR1.",
            "affectedPopulation": 2900,
            "duration": "3 days",
            "outcome": "Drainage desilted post-monsoon"
        },
        {
            "year": 2021,
            "type": "Severe Thunderstorm & Lightning",
            "severity": "Low",
            "description": "Squall wind and lightning damaged electric feeder transformers.",
            "affectedPopulation": 1200,
            "duration": "12 hours",
            "outcome": "Power restored within a day"
        },
        {
            "year": 2023,
            "type": "Flash Flood & Overflow",
            "severity": "High",
            "description": "Upstream torrential rains flooded 220 ground-floor houses and artisan workshops.",
            "affectedPopulation": 4500,
            "duration": "5 days",
            "outcome": "Community schools served as temporary shelters"
        },
        {
            "year": 2025,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Extended rainfall saturated agricultural basin, slowing outbound commodity transit.",
            "affectedPopulation": 2700,
            "duration": "4 days",
            "outcome": "Emergency culverts opened"
        }
    ],
    "N06": [
        {
            "year": 2017,
            "type": "Hanumante River Overflow",
            "severity": "High",
            "description": "Hanumante river overflow flooded eastern cultural basin and market access routes.",
            "affectedPopulation": 3600,
            "duration": "5 days",
            "outcome": "Dewatering pumps operated in heritage zones"
        },
        {
            "year": 2019,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Intense 80mm rainfall caused street flooding and blocked low bridges.",
            "affectedPopulation": 2800,
            "duration": "3 days",
            "outcome": "Civic authority cleared clogged culverts"
        },
        {
            "year": 2021,
            "type": "Flash Flood Inundation",
            "severity": "High",
            "description": "Basin water level rose rapidly, inundating pottery squares and ground floor shops.",
            "affectedPopulation": 4100,
            "duration": "4 days",
            "outcome": "Emergency boat rescue deployed by Nepal Armed Police"
        },
        {
            "year": 2022,
            "type": "Thunderstorm Squall",
            "severity": "Low",
            "description": "High winds damaged temple restoration scaffolding and power poles.",
            "affectedPopulation": 1100,
            "duration": "14 hours",
            "outcome": "Scaffolding dismantled safely"
        },
        {
            "year": 2024,
            "type": "Monsoon River Surge",
            "severity": "Moderate",
            "description": "River backflow flooded low-lying bus park and access highway NR2.",
            "affectedPopulation": 3200,
            "duration": "4 days",
            "outcome": "Traffic diverted to high bypass road"
        },
        {
            "year": 2026,
            "type": "Urban Runoff Waterlogging",
            "severity": "Moderate",
            "description": "Pre-monsoon storm runoff caused basement inundations in residential wards.",
            "affectedPopulation": 2400,
            "duration": "2 days",
            "outcome": "Dewatering pumps deployed"
        }
    ],
    "N07": [
        {
            "year": 2018,
            "type": "Hillside Soil Erosion & Slide",
            "severity": "Moderate",
            "description": "Heavy continuous rains caused roadside embankment erosion along highway NR8.",
            "affectedPopulation": 2100,
            "duration": "3 days",
            "outcome": "Retaining bio-engineering planted"
        },
        {
            "year": 2020,
            "type": "Pre-Monsoon Lightning Strikes",
            "severity": "Low",
            "description": "Lightning damaged ridge telecom antennas and solar transmission hubs.",
            "affectedPopulation": 1300,
            "duration": "16 hours",
            "outcome": "Repaired within 24 hours"
        },
        {
            "year": 2022,
            "type": "Monsoon Waterlogging & Silt",
            "severity": "Moderate",
            "description": "Runoff from northern ridge ponded in lower gateway roundabout.",
            "affectedPopulation": 2400,
            "duration": "3 days",
            "outcome": "Road culverts cleared of silt"
        },
        {
            "year": 2023,
            "type": "Forest Fire Threat",
            "severity": "Moderate",
            "description": "Pine ridge fire threatened outer hotel and hospital zone perimeters.",
            "affectedPopulation": 2800,
            "duration": "3 days",
            "outcome": "Controlled by community fire brigade"
        },
        {
            "year": 2025,
            "type": "Hillside Landslide",
            "severity": "High",
            "description": "Slope failure near highway junction obstructed emergency transport corridor.",
            "affectedPopulation": 3200,
            "duration": "4 days",
            "outcome": "One-way alternating traffic maintained"
        }
    ],
    "N08": [
        {
            "year": 2017,
            "type": "Puniavati River Inundation",
            "severity": "High",
            "description": "Puniavati stream overflowed, submerging main trade highway NR7 and shops.",
            "affectedPopulation": 3400,
            "duration": "4 days",
            "outcome": "Excavators widened river discharge mouth"
        },
        {
            "year": 2019,
            "type": "Urban Waterlogging",
            "severity": "Moderate",
            "description": "Monsoon cloudburst flooded low-lying Banepa bus terminal under 0.8m of water.",
            "affectedPopulation": 2600,
            "duration": "3 days",
            "outcome": "Heavy suction pumps cleared water"
        },
        {
            "year": 2021,
            "type": "Severe Flash Flood",
            "severity": "High",
            "description": "Sudden torrential surge flooded 300 business premises and disrupted Kathmandu artery.",
            "affectedPopulation": 3700,
            "duration": "5 days",
            "outcome": "Relief trucks deployed; highway restored"
        },
        {
            "year": 2023,
            "type": "Thunderstorm & Hail",
            "severity": "Low",
            "description": "Hail and high winds damaged greenhouse plastic tunnels and power cables.",
            "affectedPopulation": 1100,
            "duration": "10 hours",
            "outcome": "Agricultural relief assessed"
        },
        {
            "year": 2024,
            "type": "Monsoon Street Flooding",
            "severity": "Moderate",
            "description": "Drainage overflow inundated market core, causing temporary commercial shutdown.",
            "affectedPopulation": 3100,
            "duration": "3 days",
            "outcome": "Drainage deepened with stone lining"
        }
    ],
    "N09": [
        {
            "year": 2017,
            "type": "Gorge Landslide & Road Severance",
            "severity": "Critical",
            "description": "Major rockfall collapsed 120m of Araniko Highway NR10, completely cutting border access.",
            "affectedPopulation": 2700,
            "duration": "14 days",
            "outcome": "Nepal Army deployed rock blasters to reopen trail"
        },
        {
            "year": 2018,
            "type": "Bhotekoshi Flash Flood",
            "severity": "High",
            "description": "Violent glacial river surge eroded road embankments and washed away border check-post stalls.",
            "affectedPopulation": 2100,
            "duration": "6 days",
            "outcome": "Customs operations shifted to temporary tents"
        },
        {
            "year": 2020,
            "type": "Winter Snow Avalanche",
            "severity": "Moderate",
            "description": "Heavy snowfall induced chute avalanche, blocking Kodari mountain pass for 5 days.",
            "affectedPopulation": 1600,
            "duration": "5 days",
            "outcome": "Snowplows reopened single lane corridor"
        },
        {
            "year": 2021,
            "type": "Debris Torrent & Rockfall",
            "severity": "Critical",
            "description": "Intense cloudburst unleashed massive boulder debris slide, flattening 14 transit warehouses.",
            "affectedPopulation": 2700,
            "duration": "12 days",
            "outcome": "Air force helicopters evacuated stranded transport crews"
        },
        {
            "year": 2023,
            "type": "Seismic Tremor & Rockslide",
            "severity": "High",
            "description": "M4.9 localized tremor triggered widespread cliff fractures and rock falls on pass.",
            "affectedPopulation": 2200,
            "duration": "7 days",
            "outcome": "Rockfall safety nets installed"
        },
        {
            "year": 2024,
            "type": "Catastrophic Monsoon Landslide",
            "severity": "Critical",
            "description": "Continuous 96-hour rain saturated gorge face, creating an impassable 300m mud barrier.",
            "affectedPopulation": 2700,
            "duration": "16 days",
            "outcome": "Airlift corridor established to Kodari outpost"
        },
        {
            "year": 2025,
            "type": "Glacial Stream Washout",
            "severity": "High",
            "description": "Meltwater surge swept away temporary Bailey bridge, cutting northern border trade.",
            "affectedPopulation": 2300,
            "duration": "8 days",
            "outcome": "Suspension footbridge restored"
        }
    ],
    "N10": [
        {
            "year": 2018,
            "type": "Floodplain Inundation",
            "severity": "High",
            "description": "Jhikhu Khola stream breached banks, submerging 400 hectares of commercial vegetable crops.",
            "affectedPopulation": 2800,
            "duration": "5 days",
            "outcome": "Agricultural relief and subsidized seed distribution"
        },
        {
            "year": 2019,
            "type": "Severe Pre-Monsoon Dry Spell",
            "severity": "Moderate",
            "description": "Extended drought dropped irrigation canal discharge by 65% across valley farms.",
            "affectedPopulation": 2200,
            "duration": "24 days",
            "outcome": "Rotational electric pump sharing implemented"
        },
        {
            "year": 2021,
            "type": "River Flash Flood",
            "severity": "High",
            "description": "High-intensity monsoon deluge caused fast-flowing floodwaters to inundate 180 valley houses.",
            "affectedPopulation": 3000,
            "duration": "5 days",
            "outcome": "Community flood shelter activated"
        },
        {
            "year": 2023,
            "type": "Thunderstorm & Lightning",
            "severity": "Low",
            "description": "Lightning strikes killed farm livestock and disrupted local power transformer.",
            "affectedPopulation": 950,
            "duration": "14 hours",
            "outcome": "Transformer replaced within 24 hours"
        },
        {
            "year": 2024,
            "type": "Seasonal River Surge",
            "severity": "Moderate",
            "description": "Stream overflow inundated link road NR9, slowing vegetable produce transport.",
            "affectedPopulation": 2500,
            "duration": "3 days",
            "outcome": "Road cleared of mud once water receded"
        },
        {
            "year": 2026,
            "type": "Monsoon Waterlogging",
            "severity": "Moderate",
            "description": "Continuous rain caused standing water in low-elevation valley depressions.",
            "affectedPopulation": 2100,
            "duration": "4 days",
            "outcome": "Natural percolation and drainage ditches opened"
        }
    ]
}

def main():
    varanasi_path = DATA_DIR / "scenarios" / "varanasi" / "disaster_history.json"
    nepal_path = DATA_DIR / "scenarios" / "nepal" / "disaster_history.json"
    root_path = DATA_DIR / "disaster_history.json"

    varanasi_path.parent.mkdir(parents=True, exist_ok=True)
    nepal_path.parent.mkdir(parents=True, exist_ok=True)

    with open(varanasi_path, "w", encoding="utf-8") as f:
        json.dump(VARANASI_HISTORY, f, indent=2, ensure_ascii=False)
    print(f"Wrote Varanasi disaster history: {varanasi_path} ({len(VARANASI_HISTORY)} zones)")

    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(VARANASI_HISTORY, f, indent=2, ensure_ascii=False)
    print(f"Wrote Root India disaster history: {root_path} ({len(VARANASI_HISTORY)} zones)")

    with open(nepal_path, "w", encoding="utf-8") as f:
        json.dump(NEPAL_HISTORY, f, indent=2, ensure_ascii=False)
    print(f"Wrote Nepal disaster history: {nepal_path} ({len(NEPAL_HISTORY)} zones)")

if __name__ == "__main__":
    main()
