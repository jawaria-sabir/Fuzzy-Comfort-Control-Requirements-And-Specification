"""
Fuzzy Comfort Control System — Enhanced Edition
Author: jawaria-sabir | Enhanced by contributor
Stack: Python · Flask · Mamdani Fuzzy Inference · Centroid Defuzzification
"""

import logging
import os
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify


# ==============================================================================
#  FUZZY MEMBERSHIP FUNCTIONS (core engine remains importable for tests)
# ==============================================================================

# ══════════════════════════════════════════════════════════
#  FUZZY MEMBERSHIP FUNCTIONS
# ══════════════════════════════════════════════════════════

def trimf(x, a, b, c):
    """Triangular MF — peak at b"""
    if x <= a or x >= c:
        return 0.0
    if a == b:
        return 1.0 if x == b else (c - x) / (c - b)
    if b == c:
        return (x - a) / (b - a) if x <= b else 1.0
    if x <= b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)

def trapmf(x, a, b, c, d):
    """Trapezoidal MF — flat top from b to c"""
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    return (d - x) / (d - c) if d != c else 1.0

# ── Temperature (°C) MFs ──────────────────────────────────
def temp_very_cold(t):  return trapmf(t,  0,  0, 10, 15)
def temp_cold(t):       return trapmf(t,  8, 14, 18, 22)
def temp_cool(t):       return trimf(t,  18, 21, 24)
def temp_comfortable(t):return trimf(t,  21, 23, 25)
def temp_warm(t):       return trimf(t,  23, 26, 29)
def temp_hot(t):        return trapmf(t, 27, 31, 40, 40)
def temp_very_hot(t):   return trapmf(t, 35, 40, 50, 50)

# ── Humidity (%) MFs ─────────────────────────────────────
def hum_very_dry(h):    return trapmf(h,  0,  0, 20, 28)
def hum_dry(h):         return trimf(h,  20, 32, 42)
def hum_normal(h):      return trapmf(h, 38, 45, 55, 62)
def hum_humid(h):       return trimf(h,  58, 68, 78)
def hum_very_humid(h):  return trapmf(h, 74, 82, 100, 100)

# ── CO₂ (ppm) MFs ────────────────────────────────────────
def co2_fresh(c):       return trapmf(c,   0,   0, 450, 650)
def co2_normal(c):      return trimf(c,   500,  750, 1000)
def co2_elevated(c):    return trimf(c,   900, 1100, 1400)
def co2_high(c):        return trimf(c,  1200, 1600, 2200)
def co2_dangerous(c):   return trapmf(c, 2000, 2500, 5000, 5000)

# ══════════════════════════════════════════════════════════
#  OUTPUT CRISP VALUES  — HVAC Action [-1.0 .. +1.0]
#  Negative = cooling/ventilation | Positive = heating
# ══════════════════════════════════════════════════════════
OUTPUT_CRISP = {
    "full_ventilate":  -1.00,
    "strong_cool":     -0.75,
    "moderate_cool":   -0.50,
    "slight_cool":     -0.25,
    "neutral":          0.00,
    "slight_heat":      0.25,
    "moderate_heat":    0.50,
    "strong_heat":      0.75,
    "full_heat":        1.00,
}

# ══════════════════════════════════════════════════════════
#  MAMDANI INFERENCE ENGINE  — 25 rules
# ══════════════════════════════════════════════════════════
def infer(temp, humidity, co2):
    """
    Mamdani fuzzy inference with centroid defuzzification.
    Returns dict with action_value, label, comfort_score, rules_fired,
    memberships, and energy_index.
    """
    # fuzzify
    tf = {
        "very_cold": temp_very_cold(temp), "cold": temp_cold(temp),
        "cool": temp_cool(temp), "comfortable": temp_comfortable(temp),
        "warm": temp_warm(temp), "hot": temp_hot(temp), "very_hot": temp_very_hot(temp),
    }
    hf = {
        "very_dry": hum_very_dry(humidity), "dry": hum_dry(humidity),
        "normal": hum_normal(humidity), "humid": hum_humid(humidity),
        "very_humid": hum_very_humid(humidity),
    }
    cf = {
        "fresh": co2_fresh(co2), "normal": co2_normal(co2),
        "elevated": co2_elevated(co2), "high": co2_high(co2),
        "dangerous": co2_dangerous(co2),
    }

    accumulator = {}  # output_action -> max firing strength
    rules_fired = []

    def fire(strength, action, description):
        if strength > 0.005:
            accumulator[action] = max(accumulator.get(action, 0.0), strength)
            rules_fired.append({
                "strength": round(strength, 4),
                "action": action,
                "description": description
            })

    # ── TEMPERATURE-ONLY RULES ────────────────────────────
    fire(tf["very_cold"],    "full_heat",       "T=Very Cold → Full Heat")
    fire(tf["cold"],         "strong_heat",     "T=Cold → Strong Heat")
    fire(tf["cool"],         "slight_heat",     "T=Cool → Slight Heat")
    fire(tf["comfortable"],  "neutral",         "T=Comfortable → Neutral")
    fire(tf["warm"],         "slight_cool",     "T=Warm → Slight Cool")
    fire(tf["hot"],          "moderate_cool",   "T=Hot → Moderate Cool")
    fire(tf["very_hot"],     "strong_cool",     "T=Very Hot → Strong Cool")

    # ── TEMPERATURE × HUMIDITY INTERACTION ───────────────
    fire(min(tf["comfortable"], hf["very_dry"]),  "slight_heat",   "T=Comfort ∧ H=Very Dry → Slight Heat (humidify)")
    fire(min(tf["comfortable"], hf["very_humid"]), "slight_cool",  "T=Comfort ∧ H=Very Humid → Slight Cool (dehumidify)")
    fire(min(tf["hot"],  hf["very_humid"]),        "full_ventilate", "T=Hot ∧ H=Very Humid → Full Ventilate")
    fire(min(tf["cool"], hf["dry"]),               "moderate_heat",  "T=Cool ∧ H=Dry → Moderate Heat")
    fire(min(tf["warm"], hf["humid"]),             "moderate_cool",  "T=Warm ∧ H=Humid → Moderate Cool")
    fire(min(tf["cold"], hf["very_humid"]),        "moderate_heat",  "T=Cold ∧ H=Very Humid → Moderate Heat")

    # ── CO₂ OVERRIDE RULES ───────────────────────────────
    fire(cf["dangerous"],                           "full_ventilate", "CO₂=Dangerous → Full Ventilate (safety)")
    fire(min(cf["high"], tf["hot"]),                "full_ventilate", "CO₂=High ∧ T=Hot → Full Ventilate")
    fire(min(cf["high"], tf["comfortable"]),        "strong_cool",    "CO₂=High ∧ T=Comfortable → Strong Cool/Vent")
    fire(min(cf["elevated"], tf["comfortable"]),    "slight_cool",    "CO₂=Elevated ∧ T=Comfortable → Slight Vent")
    fire(min(cf["elevated"], tf["warm"]),           "moderate_cool",  "CO₂=Elevated ∧ T=Warm → Moderate Vent")
    fire(min(cf["fresh"], tf["comfortable"]),       "neutral",        "CO₂=Fresh ∧ T=Comfortable → Optimal")

    # ── COMPOUND 3-VARIABLE RULES ────────────────────────
    fire(min(tf["comfortable"], hf["normal"], cf["normal"]), "neutral",     "T=OK ∧ H=OK ∧ CO₂=OK → Perfect Neutral")
    fire(min(tf["hot"], hf["humid"], cf["elevated"]),        "full_ventilate", "All Stress → Emergency Ventilate")
    fire(min(tf["cold"], hf["dry"], cf["fresh"]),            "strong_heat",   "Cold+Dry+Fresh → Strong Heat")
    fire(min(tf["warm"], hf["normal"], cf["normal"]),        "slight_cool",   "Warm+Normal → Slight Cool")
    fire(min(tf["cool"], hf["normal"], cf["fresh"]),         "slight_heat",   "Cool+Normal+Fresh → Slight Heat")

    if not accumulator:
        return _build_result(0.0, temp, humidity, co2, tf, hf, cf, [])

    # ── CENTROID DEFUZZIFICATION ─────────────────────────
    total_w = sum(accumulator.values())
    weighted_sum = sum(OUTPUT_CRISP[k] * v for k, v in accumulator.items())
    action_value = weighted_sum / total_w

    return _build_result(action_value, temp, humidity, co2, tf, hf, cf, rules_fired, accumulator)


def _build_result(av, temp, humidity, co2, tf, hf, cf, rules_fired, accumulator=None):
    av = round(max(-1.0, min(1.0, av)), 4)

    # Human-readable label
    if av < -0.85:   label, icon = "Emergency Ventilation",  "🚨"
    elif av < -0.60: label, icon = "Strong Cooling",          "❄️"
    elif av < -0.35: label, icon = "Moderate Cooling",        "🌬️"
    elif av < -0.10: label, icon = "Slight Cooling",          "💨"
    elif av < 0.10:  label, icon = "Neutral — Hold",          "✅"
    elif av < 0.35:  label, icon = "Slight Heating",          "🌤️"
    elif av < 0.60:  label, icon = "Moderate Heating",        "🔆"
    elif av < 0.85:  label, icon = "Strong Heating",          "🔥"
    else:            label, icon = "Maximum Heating",          "♨️"

    # Comfort score 0–100
    temp_penalty  = max(0, abs(temp - 23) - 2) * 5
    hum_penalty   = max(0, abs(humidity - 50) - 10) * 1.2
    co2_penalty   = max(0, co2 - 700) / 50
    comfort = max(0, min(100, 100 - temp_penalty - hum_penalty - co2_penalty))

    # Energy efficiency index (neutral = max efficient)
    energy_index = max(0, 100 - abs(av) * 60)

    # Air quality index
    if co2 < 600:     aqi, aqi_label = 100, "Excellent"
    elif co2 < 1000:  aqi, aqi_label = 80,  "Good"
    elif co2 < 1400:  aqi, aqi_label = 55,  "Moderate"
    elif co2 < 2000:  aqi, aqi_label = 30,  "Poor"
    else:             aqi, aqi_label = 10,  "Hazardous"

    return {
        "action_value": av,
        "action_label": label,
        "action_icon":  icon,
        "comfort_score": round(comfort, 1),
        "energy_index": round(energy_index, 1),
        "air_quality_index": aqi,
        "air_quality_label": aqi_label,
        "rules_fired": sorted(rules_fired, key=lambda r: r["strength"], reverse=True),
        "rules_count": len(rules_fired),
        "memberships": {
            "temperature": {k: round(v, 3) for k, v in tf.items()},
            "humidity":    {k: round(v, 3) for k, v in hf.items()},
            "co2":         {k: round(v, 3) for k, v in cf.items()},
        },
        "output_activations": {k: round(v, 4) for k, v in (accumulator or {}).items()},
    }


# ==============================================================================
#  FLASK APP FACTORY & ROUTES
# ==============================================================================


def create_app(test_config: Dict[str, Any] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Basic config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        ENV=os.environ.get("FLASK_ENV", "production"),
    )
    if test_config:
        app.config.update(test_config)

    # Logging
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/infer", methods=["POST"])
    def api_infer():
        data = request.get_json(force=True)
        try:
            temp = float(data.get("temperature", 23))
            humidity = float(data.get("humidity", 50))
            co2 = float(data.get("co2", 600))
            temp = max(0, min(50, temp))
            humidity = max(0, min(100, humidity))
            co2 = max(0, min(5000, co2))
            result = infer(temp, humidity, co2)
            return jsonify({"status": "ok", "inputs": {"temperature": temp, "humidity": humidity, "co2": co2}, **result})
        except Exception as e:
            app.logger.exception("Error in /api/infer")
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/api/health")
    def health():
        return jsonify({"status": "healthy", "service": "Fuzzy Comfort Control System", "version": "2.0.0"})

    @app.route("/api/rules")
    def rules():
        return jsonify({
            "total_rules": 25,
            "input_variables": [
                {"name": "Temperature", "unit": "°C", "range": [0, 50],
                 "sets": ["very_cold", "cold", "cool", "comfortable", "warm", "hot", "very_hot"]},
                {"name": "Humidity", "unit": "%", "range": [0, 100],
                 "sets": ["very_dry", "dry", "normal", "humid", "very_humid"]},
                {"name": "CO₂", "unit": "ppm", "range": [0, 5000],
                 "sets": ["fresh", "normal", "elevated", "high", "dangerous"]},
            ],
            "output_variable": {"name": "HVAC Action", "range": [-1, 1],
                                "sets": list(OUTPUT_CRISP.keys())},
            "inference_method": "Mamdani",
            "defuzzification": "Centroid (COA)",
            "t_norm": "Minimum (AND)",
        })

    return app


if __name__ == "__main__":
    # Allow running with: python app.py
    env_debug = os.environ.get("FLASK_DEBUG", "0")
    debug = env_debug in ("1", "true", "True")
    _app = create_app()
    _app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug)


# ══════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/infer", methods=["POST"])
def api_infer():
    data = request.get_json(force=True)
    try:
        temp     = float(data.get("temperature", 23))
        humidity = float(data.get("humidity", 50))
        co2      = float(data.get("co2", 600))
        temp     = max(0, min(50, temp))
        humidity = max(0, min(100, humidity))
        co2      = max(0, min(5000, co2))
        result   = infer(temp, humidity, co2)
        return jsonify({"status": "ok", "inputs": {"temperature": temp, "humidity": humidity, "co2": co2}, **result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "Fuzzy Comfort Control System", "version": "2.0.0"})

@app.route("/api/rules")
def rules():
    return jsonify({
        "total_rules": 25,
        "input_variables": [
            {"name": "Temperature", "unit": "°C", "range": [0, 50],
             "sets": ["very_cold", "cold", "cool", "comfortable", "warm", "hot", "very_hot"]},
            {"name": "Humidity", "unit": "%", "range": [0, 100],
             "sets": ["very_dry", "dry", "normal", "humid", "very_humid"]},
            {"name": "CO₂", "unit": "ppm", "range": [0, 5000],
             "sets": ["fresh", "normal", "elevated", "high", "dangerous"]},
        ],
        "output_variable": {"name": "HVAC Action", "range": [-1, 1],
                            "sets": list(OUTPUT_CRISP.keys())},
        "inference_method": "Mamdani",
        "defuzzification": "Centroid (COA)",
        "t_norm": "Minimum (AND)",
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
