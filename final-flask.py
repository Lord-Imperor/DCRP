"""
================================================================================
IMPEROR OMO - FLASK BACKEND ENGINE (COMPLETE)
DC Universe Campaign System | Karmic Framework Implementation
================================================================================

CORE PRINCIPLES:
Flask is the stateless calculation engine AND state persistence manager.

WHAT FLASK DOES:
✓ Calculates all game mechanics (combat, advancement, premonitions)
✓ Manages character state (reads/writes character.json)
✓ Manages world state (reads/writes world_state.json)
✓ Returns ONLY FACTS - never interpretation or narrative
✓ Supports Secondary LLM's automated state updates

WHAT FLASK DOES NOT DO:
✗ Narration (LLM1 domain)
✗ NPC behavior (LLM1 domain)
✗ Ability manifestation decisions (LLM1 domain - purely random)
✗ Equipment acquisition (manual/narrative domain)

STATE PERSISTENCE:
- character.json: Player stats, DC balance, abilities, equipment
- world_state.json: Escalation indicators, event thresholds, faction states
- sessions/session_N.json: Session history and snapshots

DEPLOYMENT:
- Local: http://localhost:5000/
- Tunnel: https://unquenchable-anastacia-nonobstetricitly.ngrok-free.dev/

================================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import json
import math
import os

app = Flask(__name__)
CORS(app)


# ================================================================================
# SECTION 1: EMBEDDED RULES SYSTEM
# ================================================================================

RULES = {
    "system": {
        "name": "Imperor Omo Karmic Framework",
        "universe": "DC Comics Prime Earth",
        "version": "3.0_complete",
        "karmic_cap": 22,
        "universal_max": 25,
        "stats": ["speed", "reflexes", "power", "resistance"]
    },

    "stat_multipliers": {
        "speed": 2.0,
        "reflexes": 2.0,
        "power": 4.5,
        "resistance": 10.0
    },

    "tiers": {
        0: {"name": "Below Average Human", "category": "Subhuman", "movement_speed": "0.5-1 m/s walking", "reflex_speed": "400-500ms reaction time", "power": "1-50 joules (child's push)", "resistance": "Bruises easily, no defense", "examples": ["Civilian", "Child", "Elderly"]},
        1: {"name": "Average Human", "category": "Human", "movement_speed": "1-3 m/s typical gait", "reflex_speed": "250-300ms reaction time", "power": "50-300 joules (break wood)", "resistance": "Typical human fragility", "examples": ["Untrained adult"]},
        2: {"name": "Athletic Human", "category": "Human", "movement_speed": "3-5 m/s running", "reflex_speed": "180-250ms reflex", "power": "300-1,000 joules (break boards)", "resistance": "Multi-punch survivable, mild energy resistance", "examples": ["Professional athlete"]},
        3: {"name": "Peak Human", "category": "Human", "movement_speed": "5-10 m/s (Olympic sprint)", "reflex_speed": "120-180ms elite reaction", "power": "1,000-15,000 joules (shatter doors)", "resistance": "Survive car crash, 10m+ falls", "examples": ["Green Arrow", "Black Canary", "Catwoman", "Red Hood", "Wildcat"]},
        4: {"name": "Wall Level", "category": "Enhanced Human", "movement_speed": "10-15 m/s", "reflex_speed": "90-120ms superhuman reaction", "power": "15,000-50,000 joules", "resistance": "Concrete wall level, moderate psychic defense", "examples": ["Batman (early)", "Nightwing", "Robin", "Batgirl"]},
        5: {"name": "Wall+", "category": "Enhanced Human", "movement_speed": "15-25 m/s", "reflex_speed": "60-90ms enhanced superhuman", "power": "50,000-250,000 joules", "resistance": "Reinforced concrete, assault rifle fire survivable", "examples": ["Batman (peak)", "Deathstroke", "Lady Shiva", "Katana"]},
        6: {"name": "Small Building", "category": "Enhanced Human", "movement_speed": "25-50 m/s", "reflex_speed": "40-60ms lightning fast", "power": "0.25-1 megajoule", "resistance": "Tank antimaterial rounds, -200°C to 500°C", "examples": ["Bane (high Venom)", "Killer Croc", "Mr. Freeze"]},
        7: {"name": "Small Building+", "category": "Enhanced Human", "movement_speed": "50-100 m/s", "reflex_speed": "20-40ms hypersonic reaction", "power": "1-5 megajoules", "resistance": "Tank bombs, immune to small military weapons", "examples": ["Aquaman", "Mera", "Black Adam (low)", "Starfire", "Raven"]},
        8: {"name": "Building Level", "category": "Superhuman", "movement_speed": "100-200 m/s", "reflex_speed": "10-20ms near instantaneous", "power": "5-20 megajoules", "resistance": "Survive artillery, temperatures -400°C to 2000°C", "examples": ["Wonder Woman (restrained)", "Martian Manhunter (restrained)", "Big Barda"]},
        9: {"name": "Building+ Level", "category": "Superhuman", "movement_speed": "200-500 m/s", "reflex_speed": "5-10ms superhuman processing", "power": "20-100 megajoules", "resistance": "City block defense, MOAB-scale", "examples": ["Wonder Woman (moderate)", "Superman (restrained)", "Shazam (moderate)"]},
        10: {"name": "City Block Level", "category": "Superhuman", "movement_speed": "500-1,000 m/s", "reflex_speed": "1-5ms godlike reaction", "power": "100-500 megajoules", "resistance": "Tank nuke, extreme temperature immunity", "examples": ["Superman (casual)", "Black Adam (serious)"]},
        11: {"name": "Multi-Block / Town", "category": "Superhuman", "movement_speed": "1-5 km/s", "reflex_speed": "0.5-1ms omniscient perception", "power": "500 megajoules - 2 gigajoules", "resistance": "Survive low-yield nuclear detonation", "examples": ["Superman (moderate)", "Martian Manhunter (full)", "Black Adam (full)"]},
        12: {"name": "Town Level", "category": "Superhuman", "movement_speed": "5-25 km/s", "reflex_speed": "Instantaneous local", "power": "2-10 gigajoules", "resistance": "Tank 100 kiloton nuclear weapons", "examples": ["Superman (serious)", "Orion", "Doomsday (evolving)"]},
        13: {"name": "City Level", "category": "Powerhouse", "movement_speed": "25-100 km/s", "reflex_speed": "Instantaneous regional", "power": "10-50 gigajoules", "resistance": "Survive 1 megaton city-destruction", "examples": ["Superman (full)", "Darkseid"]},
        14: {"name": "City+ Level", "category": "Powerhouse", "movement_speed": "100-500 km/s", "reflex_speed": "Instantaneous continental", "power": "50-250 gigajoules", "resistance": "Survive 10 megaton strike", "examples": ["Superman (enraged/solar charged)", "Superboy Prime (serious)"]},
        15: {"name": "Mountain Level", "category": "Powerhouse", "movement_speed": "500 km/s - 2,500 km/s", "reflex_speed": "Instantaneous planetary", "power": "250 gigajoules - 1 terajoule", "resistance": "Survive Tsar Bomb (50 megatons)", "examples": ["Superman (non-amped peak)", "Darkseid (manifest)"]},
        16: {"name": "Island Level", "category": "Powerhouse", "movement_speed": "2,500-10,000 km/s", "reflex_speed": "Omniscient planetary", "power": "1-5 terajoules", "resistance": "Survive 100 megaton strike", "examples": ["Superman (sundipped/amped)", "Wonder Woman (God of War)"]},
        17: {"name": "Country Level", "category": "Powerhouse", "movement_speed": "10,000-50,000 km/s", "reflex_speed": "Omniscient solar system", "power": "5-25 terajoules", "resistance": "Survive global-scale nuclear exchange", "examples": ["Superman (max sundip)", "Spectre (restrained)"]},
        18: {"name": "Continent Level", "category": "Cosmic", "movement_speed": "Speed of light+", "reflex_speed": "Omniscient universal", "power": "25-100 terajoules+", "resistance": "Survive planet-wide events", "examples": ["Superman (Crisis)", "Spectre (moderate)"]},
        19: {"name": "Multi-Continent", "category": "Cosmic", "movement_speed": "FTL (faster than light)", "reflex_speed": "Omniscient multiversal", "power": "100-500 terajoules", "resistance": "Survive planet-crack level damage", "examples": ["Superman (Crisis peak)", "Darkseid (true)"]},
        20: {"name": "Moon Level", "category": "Cosmic", "movement_speed": "Massive FTL", "reflex_speed": "Omniscient time-independent", "power": "0.5-2 petajoules", "resistance": "Survive lunar destruction", "examples": []},
        21: {"name": "Planet Level", "category": "Cosmic", "movement_speed": "Ultra FTL", "reflex_speed": "Transcendent perception", "power": "2-10 petajoules", "resistance": "Survive planet bursting", "examples": ["Superman (peak)", "Darkseid (true form)"]},
        22: {"name": "Large Planet Level", "category": "Cosmic", "movement_speed": "Ultra FTL", "reflex_speed": "Transcendent omniscience", "power": "10-50 petajoules", "resistance": "Survive Jupiter-scale destruction", "examples": ["Spectre (unrestrained)", "Perpetua", "Superboy Prime (absolute)"], "note": "KARMIC SYSTEM CAP"},
        23: {"name": "Star Level", "category": "Abstract", "movement_speed": "Instantaneous/Omnipresent", "reflex_speed": "Absolute omniscience", "power": "50-250 petajoules", "resistance": "Survive supernovae", "examples": ["Darkseid (full)", "Anti-Monitor"], "note": "Beyond Karmic System"},
        24: {"name": "Solar System / Galaxy", "category": "Abstract", "movement_speed": "Omnipresent", "reflex_speed": "Universal omniscience", "power": "0.25-1 exajoule+", "resistance": "Survive solar system destruction", "examples": ["Perpetua", "Monitors", "Mandrakk"], "note": "Beyond Karmic System"},
        25: {"name": "Universal / Multiversal", "category": "Abstract", "movement_speed": "Omnipresent across dimensions", "reflex_speed": "Infinite omniscience", "power": "1 exajoule+", "resistance": "Survive universal erasure", "examples": ["The Presence", "The Source", "Cosmic Armor Superman"], "note": "Beyond Karmic System"}
    },

    "progression": {
        "karmic_cap": 22,
        "universal_max": 25,
        "enhancement_formula": "ceil(10 * n^1.5)",
        "max_enhancements": 85,
        "max_enhancements_per_stat": 22
    },

    "abilities": {
        "max_active_per_character": 1,
        "domain_locked": True,
        "reroll_formula": "ceil(10 * (n+1)^1.5)",
        "available_at_enhancement": 1
    },

    "combat": {
        "stat_comparison_formula": "(actor_tier - defender_tier) * multiplier",
        "skills_formula": "(skills + resourcefulness) - dc_modifier"
    },

    "premonition": {
        "resolution": "Binary - full DC reward on success, 0 DC on failure",
        "dc_reward_formula": "(actor_tier * threat_tier)^1.55"
    },

    "armor": {
        "destruction_condition": "If incoming attack_power_tier > armor_tier, armor is destroyed",
        "effective_resilience": "If armor_tier > character_resilience_tier, use armor_tier for damage calculations"
    }
}


# ================================================================================
# SECTION 2: FILE I/O UTILITIES
# ================================================================================

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

SESSIONS_DIR = DATA_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def read_json_file(filepath):
    """Read JSON file. Returns None if not found or parse error."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None


def write_json_file(filepath, data):
    """Write data to JSON file. Creates parent directories if needed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        return False


def get_character_state():
    """Read character state from character.json"""
    char_file = DATA_DIR / "character.json"
    return read_json_file(char_file)


def save_character_state(character_data):
    """Write character state to character.json"""
    char_file = DATA_DIR / "character.json"
    return write_json_file(char_file, character_data)


def get_world_state():
    """Read world state from world_state.json"""
    world_file = DATA_DIR / "world_state.json"
    return read_json_file(world_file)


def save_world_state(world_data):
    """Write world state to world_state.json"""
    world_file = DATA_DIR / "world_state.json"
    return write_json_file(world_file, world_data)


def get_hero_from_database(hero_name):
    """Lookup hero from heroes_db.json by name"""
    db_file = DATA_DIR / "heroes_db.json"
    db = read_json_file(db_file)
    if not db or "heroes" not in db:
        return None
    
    for hero in db.get("heroes", []):
        if hero.get("name", "").lower() == hero_name.lower():
            return hero
    return None


def get_latest_session_number():
    """Get the highest session number from existing files"""
    if not SESSIONS_DIR.exists():
        return 0
    
    session_files = list(SESSIONS_DIR.glob("session_*.json"))
    if not session_files:
        return 0
    
    numbers = []
    for f in session_files:
        try:
            num = int(f.stem.split('_')[1])
            numbers.append(num)
        except:
            pass
    
    return max(numbers) if numbers else 0


# ================================================================================
# SECTION 3: CALCULATION ENGINES
# ================================================================================

def calculate_enhancement_cost(enhancement_number):
    """Calculate DC cost for stat enhancement. Formula: ceil(10 * n^1.5)"""
    if enhancement_number < 1:
        return 0
    return math.ceil(10 * (enhancement_number ** 1.5))


def calculate_ability_reroll_cost(current_enhancement_number):
    """Calculate DC cost to reroll ability (next tier price, don't increment)"""
    next_enhancement = current_enhancement_number + 1
    return math.ceil(10 * (next_enhancement ** 1.5))


def calculate_stat_advantage(actor_tier, defender_tier, stat_type):
    """Calculate raw advantage for one stat comparison"""
    if stat_type not in RULES["stat_multipliers"]:
        return {"error": f"Invalid stat_type '{stat_type}'"}
    
    multiplier = RULES["stat_multipliers"][stat_type]
    tier_difference = actor_tier - defender_tier
    advantage = tier_difference * multiplier
    
    return {
        "stat_type": stat_type,
        "actor_tier": actor_tier,
        "defender_tier": defender_tier,
        "tier_difference": tier_difference,
        "multiplier": multiplier,
        "advantage": round(advantage, 2)
    }


def calculate_skills_resourcefulness_advantage(actor_skills, actor_resourcefulness, actor_dc_mod,
                                               defender_skills, defender_resourcefulness, defender_dc_mod):
    """Calculate skills advantage with per-character DC modifiers"""
    actor_effective = (actor_skills + actor_resourcefulness) - actor_dc_mod
    defender_effective = (defender_skills + defender_resourcefulness) - defender_dc_mod
    advantage = actor_effective - defender_effective
    
    return {
        "actor_raw_score": actor_skills + actor_resourcefulness,
        "actor_dc_modifier": actor_dc_mod,
        "actor_effective_score": actor_effective,
        "defender_raw_score": defender_skills + defender_resourcefulness,
        "defender_dc_modifier": defender_dc_mod,
        "defender_effective_score": defender_effective,
        "advantage": round(advantage, 2)
    }


def calculate_premonition_dc(actor_tier, threat_tier):
    """Calculate DC reward for premonition. Formula: (actor_tier * threat_tier)^1.55"""
    dc_float = (actor_tier * threat_tier) ** 1.55
    return int(math.ceil(dc_float))


def calculate_armor_status(attack_power_tier, armor_tier, character_resilience_tier):
    """Determine if armor is destroyed and effective resilience"""
    armor_destroyed = attack_power_tier > armor_tier
    effective_resilience = max(armor_tier, character_resilience_tier)
    
    return {
        "attack_power_tier": attack_power_tier,
        "armor_tier": armor_tier,
        "character_resilience_tier": character_resilience_tier,
        "armor_destroyed": armor_destroyed,
        "effective_resilience_for_damage": effective_resilience
    }


# ================================================================================
# SECTION 4: POST ENDPOINTS - SYSTEM & STATUS
# ================================================================================

@app.route('/health', methods=['POST'])
def health_check():
    """Health check - verify Flask online"""
    return jsonify({
        "status": "ONLINE",
        "engine": RULES["system"]["name"],
        "version": RULES["system"]["version"],
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/rules/summary', methods=['POST'])
def rules_summary():
    """Get system rules and constants"""
    return jsonify({
        "status": "SUCCESS",
        "system": RULES["system"],
        "stat_multipliers": RULES["stat_multipliers"],
        "progression": RULES["progression"],
        "abilities": RULES["abilities"],
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/session/current', methods=['POST'])
def session_current():
    """Get current session number and status"""
    session_num = get_latest_session_number()
    if session_num == 0:
        session_num = 1
    
    session_file = SESSIONS_DIR / f"session_{session_num}.json"
    session_exists = session_file.exists()
    
    return jsonify({
        "status": "SUCCESS",
        "current_session_number": session_num,
        "session_file_path": str(session_file),
        "session_exists": session_exists,
        "timestamp": datetime.now().isoformat()
    }), 200


# ================================================================================
# SECTION 5: POST ENDPOINTS - COMBAT CALCULATIONS
# ================================================================================

@app.route('/calculate/stat_advantage', methods=['POST'])
def calculate_stat_advantage_endpoint():
    """Compare one stat between two entities"""
    try:
        data = request.get_json()
        actor_tier = int(data.get("actor_tier", 0))
        defender_tier = int(data.get("defender_tier", 0))
        stat_type = data.get("stat_type", "").lower()
        
        valid_stats = list(RULES["stat_multipliers"].keys())
        if stat_type not in valid_stats:
            return jsonify({
                "status": "ERROR",
                "reason": "invalid_stat_type",
                "message": f"stat_type must be one of: {valid_stats}",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        comparison = calculate_stat_advantage(actor_tier, defender_tier, stat_type)
        
        return jsonify({
            "status": "SUCCESS",
            "comparison": comparison,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/calculate/combat', methods=['POST'])
def calculate_combat():
    """Full combat calculation - all stats + skills/resourcefulness"""
    try:
        data = request.get_json()
        
        actor_data = data.get("actor", {})
        defender_data = data.get("defender", {})
        
        speed_adv = calculate_stat_advantage(
            actor_data.get("speed_tier", 1),
            defender_data.get("speed_tier", 1),
            "speed"
        )
        reflexes_adv = calculate_stat_advantage(
            actor_data.get("reflexes_tier", 1),
            defender_data.get("reflexes_tier", 1),
            "reflexes"
        )
        power_adv = calculate_stat_advantage(
            actor_data.get("power_tier", 1),
            defender_data.get("power_tier", 1),
            "power"
        )
        resistance_adv = calculate_stat_advantage(
            actor_data.get("resistance_tier", 1),
            defender_data.get("resistance_tier", 1),
            "resistance"
        )
        
        stat_total = (speed_adv.get("advantage", 0) + 
                      reflexes_adv.get("advantage", 0) + 
                      power_adv.get("advantage", 0) + 
                      resistance_adv.get("advantage", 0))
        
        skills_adv = calculate_skills_resourcefulness_advantage(
            actor_data.get("skills", 0),
            actor_data.get("resourcefulness", 0),
            actor_data.get("environment_dc_modifier", 0),
            defender_data.get("skills", 0),
            defender_data.get("resourcefulness", 0),
            defender_data.get("environment_dc_modifier", 0)
        )
        
        return jsonify({
            "status": "SUCCESS",
            "combat_data": {
                "stat_advantages": {
                    "speed": speed_adv,
                    "reflexes": reflexes_adv,
                    "power": power_adv,
                    "resistance": resistance_adv
                },
                "stat_total_advantage": round(stat_total, 2),
                "skills_resourcefulness_advantage": skills_adv
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "combat_calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 6: POST ENDPOINTS - ADVANCEMENT SYSTEM
# ================================================================================

@app.route('/calculate/enhancement_cost', methods=['POST'])
def calculate_enhancement_cost_endpoint():
    """Calculate cost to enhance a stat"""
    try:
        data = request.get_json()
        enhancement_number = int(data.get("enhancement_number", 1))
        
        max_enh = RULES["progression"]["max_enhancements"]
        if enhancement_number < 1 or enhancement_number > max_enh:
            return jsonify({
                "status": "ERROR",
                "reason": "invalid_enhancement_number",
                "message": f"enhancement_number must be 1-{max_enh}",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        cost = calculate_enhancement_cost(enhancement_number)
        
        return jsonify({
            "status": "SUCCESS",
            "enhancement_number": enhancement_number,
            "dc_cost": cost,
            "formula": f"ceil(10 * {enhancement_number}^1.5) = {cost}",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "enhancement_calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/character/enhance_stat', methods=['POST'])
def enhance_stat():
    """Enhance a character stat (tier up), spend DC from balance"""
    try:
        data = request.get_json()
        stat_name = data.get("stat", "").lower()
        dc_to_spend = int(data.get("dc_amount", 0))
        
        # Load character state
        character = get_character_state()
        if not character:
            return jsonify({
                "status": "ERROR",
                "reason": "character_not_found",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Validate stat
        if stat_name not in RULES["system"]["stats"]:
            return jsonify({
                "status": "ERROR",
                "reason": "invalid_stat",
                "message": f"stat must be one of: {RULES['system']['stats']}",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Check DC balance
        dc_balance = character.get("advancement", {}).get("dc_balance", {}).get("current_balance", 0)
        if dc_to_spend != dc_to_spend or dc_balance < dc_to_spend:
            return jsonify({
                "status": "ERROR",
                "reason": "insufficient_dc",
                "message": f"Required: {dc_to_spend} DC, Current: {dc_balance} DC",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Get current tier
        current_tier = character.get("tiers", {}).get(stat_name, 1)
        
        # Check if already at Karmic cap
        if current_tier >= RULES["progression"]["karmic_cap"]:
            return jsonify({
                "status": "ERROR",
                "reason": "karmic_cap_reached",
                "message": f"Cannot enhance beyond Tier {RULES['progression']['karmic_cap']} via Karmic System",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Update character state
        character["tiers"][stat_name] = current_tier + 1
        character["advancement"]["dc_balance"]["current_balance"] -= dc_to_spend
        character["advancement"]["dc_balance"]["spent_total"] += dc_to_spend
        
        # Add to log
        if "enhancement_log" not in character["advancement"]:
            character["advancement"]["enhancement_log"] = []
        
        character["advancement"]["enhancement_log"].append({
            "timestamp": datetime.now().isoformat(),
            "stat": stat_name,
            "from_tier": current_tier,
            "to_tier": current_tier + 1,
            "dc_spent": dc_to_spend
        })
        
        # Save
        save_character_state(character)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "stat_enhanced",
            "stat": stat_name,
            "previous_tier": current_tier,
            "new_tier": current_tier + 1,
            "dc_spent": dc_to_spend,
            "dc_balance_after": character["advancement"]["dc_balance"]["current_balance"],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "enhancement_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 7: POST ENDPOINTS - PREMONITION SYSTEM
# ================================================================================

@app.route('/calculate/premonition_dc', methods=['POST'])
def calculate_premonition_dc_endpoint():
    """Calculate DC reward for premonition"""
    try:
        data = request.get_json()
        actor_tier = int(data.get("actor_tier", 1))
        threat_tier = int(data.get("threat_tier", 1))
        
        if actor_tier < 1 or threat_tier < 1:
            return jsonify({
                "status": "ERROR",
                "reason": "invalid_tier_values",
                "message": "actor_tier and threat_tier must be >= 1",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        raw_value = (actor_tier * threat_tier) ** 1.55
        dc_reward = calculate_premonition_dc(actor_tier, threat_tier)
        
        return jsonify({
            "status": "SUCCESS",
            "dc_reward": dc_reward,
            "calculation": {
                "actor_tier": actor_tier,
                "threat_tier": threat_tier,
                "formula": "(actor_tier * threat_tier)^1.55",
                "raw_value": round(raw_value, 2)
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "premonition_calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/character/premonition/resolve', methods=['POST'])
def resolve_premonition():
    """Resolve premonition - award or deny DC points"""
    try:
        data = request.get_json()
        success = data.get("success", False)
        actor_tier = int(data.get("actor_tier", 1))
        threat_tier = int(data.get("threat_tier", 1))
        
        # Calculate DC if success
        dc_awarded = 0
        if success:
            dc_awarded = calculate_premonition_dc(actor_tier, threat_tier)
        
        # Load character
        character = get_character_state()
        if not character:
            return jsonify({
                "status": "ERROR",
                "reason": "character_not_found",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Update character state
        if "dc_balance" not in character.get("advancement", {}):
            character["advancement"]["dc_balance"] = {"current_balance": 0, "earned_total": 0, "spent_total": 0}
        
        character["advancement"]["dc_balance"]["current_balance"] += dc_awarded
        character["advancement"]["dc_balance"]["earned_total"] += dc_awarded
        
        # Track premonition
        if "premonitions_completed" not in character["advancement"]:
            character["advancement"]["premonitions_completed"] = []
        
        character["advancement"]["premonitions_completed"].append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "actor_tier": actor_tier,
            "threat_tier": threat_tier,
            "dc_awarded": dc_awarded
        })
        
        # Save
        save_character_state(character)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "premonition_resolved",
            "success": success,
            "dc_awarded": dc_awarded,
            "new_dc_balance": character["advancement"]["dc_balance"]["current_balance"],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "premonition_resolution_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 8: POST ENDPOINTS - ABILITY SYSTEM
# ================================================================================

@app.route('/calculate/ability_reroll_cost', methods=['POST'])
def calculate_ability_reroll_cost_endpoint():
    """Calculate cost to reroll ability"""
    try:
        data = request.get_json()
        current_enhancement = int(data.get("current_enhancement_number", 1))
        
        if current_enhancement < 1:
            return jsonify({
                "status": "ERROR",
                "reason": "cannot_reroll_nonexistent_ability",
                "message": "Ability must exist (enhancement >= 1) to reroll",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        reroll_cost = calculate_ability_reroll_cost(current_enhancement)
        
        return jsonify({
            "status": "SUCCESS",
            "current_enhancement_number": current_enhancement,
            "reroll_cost": reroll_cost,
            "next_enhancement_number": current_enhancement + 1,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "reroll_calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/character/ability/manifest', methods=['POST'])
def manifest_ability():
    """Grant an ability to character"""
    try:
        data = request.get_json()
        ability_name = data.get("ability_name", "")
        domain = data.get("domain", "")
        enhancement_level = int(data.get("enhancement_level", 1))
        
        if not ability_name or not domain:
            return jsonify({
                "status": "ERROR",
                "reason": "missing_fields",
                "message": "ability_name and domain required",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Load character
        character = get_character_state()
        if not character:
            return jsonify({
                "status": "ERROR",
                "reason": "character_not_found",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Check if already has active ability
        if "active_ability" in character and character["active_ability"]:
            return jsonify({
                "status": "ERROR",
                "reason": "ability_already_active",
                "message": f"Active ability: {character['active_ability'].get('name')}. Can only have one.",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Create ability record
        ability = {
            "name": ability_name,
            "domain": domain,
            "enhancement_level": enhancement_level,
            "manifested_date": datetime.now().isoformat(),
            "enhancements": []
        }
        
        character["active_ability"] = ability
        
        # Track in log
        if "ability_log" not in character["advancement"]:
            character["advancement"]["ability_log"] = []
        
        character["advancement"]["ability_log"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "manifested",
            "ability_name": ability_name,
            "domain": domain,
            "initial_enhancement": enhancement_level
        })
        
        # Save
        save_character_state(character)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "ability_manifested",
            "ability": ability,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "ability_manifestation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/character/ability/reroll', methods=['POST'])
def reroll_ability():
    """Reroll current ability - costs DC but doesn't increment counter"""
    try:
        data = request.get_json()
        new_ability_name = data.get("new_ability_name", "")
        new_domain = data.get("new_domain", "")
        dc_to_spend = int(data.get("dc_amount", 0))
        
        # Load character
        character = get_character_state()
        if not character:
            return jsonify({
                "status": "ERROR",
                "reason": "character_not_found",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Check if has active ability
        if "active_ability" not in character or not character["active_ability"]:
            return jsonify({
                "status": "ERROR",
                "reason": "no_active_ability",
                "message": "Cannot reroll - no active ability",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Check DC balance
        dc_balance = character.get("advancement", {}).get("dc_balance", {}).get("current_balance", 0)
        if dc_balance < dc_to_spend:
            return jsonify({
                "status": "ERROR",
                "reason": "insufficient_dc",
                "message": f"Required: {dc_to_spend} DC, Current: {dc_balance} DC",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Get old ability info
        old_ability = character["active_ability"].copy()
        old_enhancement_level = old_ability.get("enhancement_level", 1)
        
        # Update ability (name, domain change but keep enhancement level)
        character["active_ability"]["name"] = new_ability_name
        character["active_ability"]["domain"] = new_domain
        character["active_ability"]["rerolled_date"] = datetime.now().isoformat()
        
        # Spend DC
        character["advancement"]["dc_balance"]["current_balance"] -= dc_to_spend
        character["advancement"]["dc_balance"]["spent_total"] += dc_to_spend
        
        # Track in log
        character["advancement"]["ability_log"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "rerolled",
            "old_ability": old_ability["name"],
            "new_ability": new_ability_name,
            "old_domain": old_ability["domain"],
            "new_domain": new_domain,
            "enhancement_level_unchanged": old_enhancement_level,
            "dc_spent": dc_to_spend
        })
        
        # Save
        save_character_state(character)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "ability_rerolled",
            "old_ability": old_ability["name"],
            "new_ability": new_ability_name,
            "enhancement_level_preserved": old_enhancement_level,
            "dc_spent": dc_to_spend,
            "dc_balance_after": character["advancement"]["dc_balance"]["current_balance"],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "ability_reroll_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 9: POST ENDPOINTS - STATE MANAGEMENT
# ================================================================================

@app.route('/character/get_state', methods=['POST'])
def get_character_state_endpoint():
    """Get current character state"""
    try:
        character = get_character_state()
        
        if not character:
            return jsonify({
                "status": "NOT_FOUND",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "status": "SUCCESS",
            "character": character,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "character_load_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/world/get_state', methods=['POST'])
def get_world_state_endpoint():
    """Get current world state"""
    try:
        world = get_world_state()
        
        if not world:
            return jsonify({
                "status": "NOT_FOUND",
                "message": "world_state.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "status": "SUCCESS",
            "world": world,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "world_load_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/world/escalation/update', methods=['POST'])
def update_world_escalation():
    """Update world escalation indicators (Secondary LLM calls this)"""
    try:
        data = request.get_json()
        updates = data.get("escalation_updates", {})
        
        # Load world state
        world = get_world_state()
        if not world:
            return jsonify({
                "status": "ERROR",
                "reason": "world_not_found",
                "message": "world_state.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Update escalation indicators
        if "escalation_indicators" not in world:
            world["escalation_indicators"] = {}
        
        for indicator_name, new_value in updates.items():
            world["escalation_indicators"][indicator_name] = {
                "value": new_value,
                "last_updated": datetime.now().isoformat()
            }
        
        # Save
        save_world_state(world)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "escalation_updated",
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "escalation_update_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/world/date/advance', methods=['POST'])
def advance_world_date():
    """Advance world date (Secondary LLM calls this between sessions)"""
    try:
        data = request.get_json()
        days_advance = int(data.get("days", 0))
        
        # Load world state
        world = get_world_state()
        if not world:
            return jsonify({
                "status": "ERROR",
                "reason": "world_not_found",
                "message": "world_state.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Update date (assuming world has "current_date" field)
        if "current_date" in world:
            from datetime import datetime as dt, timedelta
            current = dt.fromisoformat(world["current_date"])
            new_date = current + timedelta(days=days_advance)
            world["current_date"] = new_date.isoformat()
        
        # Save
        save_world_state(world)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "date_advanced",
            "days_advanced": days_advance,
            "new_date": world.get("current_date"),
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "date_advancement_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 10: POST ENDPOINTS - REFERENCE DATA
# ================================================================================

@app.route('/hero/lookup', methods=['POST'])
def hero_lookup():
    """Lookup hero from database"""
    try:
        data = request.get_json()
        hero_name = data.get("hero_name", "").strip()
        
        if not hero_name:
            return jsonify({
                "status": "ERROR",
                "reason": "missing_hero_name",
                "message": "hero_name is required",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        hero = get_hero_from_database(hero_name)
        
        if not hero:
            return jsonify({
                "status": "NOT_FOUND",
                "hero_name": hero_name,
                "message": f"Hero '{hero_name}' not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "status": "SUCCESS",
            "hero": hero,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "hero_lookup_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/tier/info', methods=['POST'])
def tier_info():
    """Get tier definition"""
    try:
        data = request.get_json()
        tier_num = int(data.get("tier", 0))
        
        if tier_num not in RULES["tiers"]:
            return jsonify({
                "status": "ERROR",
                "reason": "invalid_tier",
                "message": f"Tier {tier_num} not defined. Valid range: 0-25",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        return jsonify({
            "status": "SUCCESS",
            "tier_number": tier_num,
            "tier_definition": RULES["tiers"][tier_num],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "tier_lookup_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 11: POST ENDPOINTS - ARMOR SYSTEM
# ================================================================================

@app.route('/calculate/armor_status', methods=['POST'])
def calculate_armor_status_endpoint():
    """Determine if armor is destroyed in attack"""
    try:
        data = request.get_json()
        attack_power = int(data.get("attack_power_tier", 1))
        armor_tier = int(data.get("armor_tier", 1))
        character_resilience = int(data.get("character_resilience_tier", 1))
        
        armor_status = calculate_armor_status(attack_power, armor_tier, character_resilience)
        
        return jsonify({
            "status": "SUCCESS",
            "armor_data": armor_status,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "armor_calculation_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/character/armor/destroy', methods=['POST'])
def destroy_armor():
    """Mark armor as destroyed"""
    try:
        data = request.get_json()
        
        # Load character
        character = get_character_state()
        if not character:
            return jsonify({
                "status": "ERROR",
                "reason": "character_not_found",
                "message": "character.json not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Update armor status
        if "equipment" not in character:
            character["equipment"] = {}
        
        character["equipment"]["armor_destroyed"] = True
        character["equipment"]["armor_destroyed_date"] = datetime.now().isoformat()
        
        # Save
        save_character_state(character)
        
        return jsonify({
            "status": "SUCCESS",
            "action": "armor_destroyed",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "reason": "armor_destruction_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ================================================================================
# SECTION 12: STARTUP
# ================================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("IMPEROR OMO - FLASK ENGINE COMPLETE v3.0")
    print("=" * 80)
    print(f"System: {RULES['system']['name']}")
    print(f"Universe: {RULES['system']['universe']}")
    print(f"Karmic Cap: Tier {RULES['system']['karmic_cap']}")
    print()
    print("POST ENDPOINTS:")
    print("  /health                           - Status check")
    print("  /rules/summary                    - Get system rules")
    print("  /session/current                  - Current session info")
    print()
    print("  /calculate/stat_advantage         - Compare one stat")
    print("  /calculate/combat                 - Full combat calc")
    print("  /calculate/premonition_dc         - Premonition DC calc")
    print("  /calculate/enhancement_cost       - Stat enhancement cost")
    print("  /calculate/ability_reroll_cost    - Ability reroll cost")
    print("  /calculate/armor_status           - Armor destruction check")
    print()
    print("  /character/enhance_stat           - Enhance stat (spend DC)")
    print("  /character/premonition/resolve    - Resolve premonition")
    print("  /character/ability/manifest       - Grant ability")
    print("  /character/ability/reroll         - Reroll ability")
    print("  /character/armor/destroy          - Mark armor destroyed")
    print("  /character/get_state              - Get character state")
    print()
    print("  /world/get_state                  - Get world state")
    print("  /world/escalation/update          - Update escalation (Sec LLM)")
    print("  /world/date/advance               - Advance date (Sec LLM)")
    print()
    print("  /hero/lookup                      - Lookup hero stats")
    print("  /tier/info                        - Get tier definition")
    print("=" * 80)
    print()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
