# 🌡️ Fuzzy Comfort Control System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Fuzzy Logic](https://img.shields.io/badge/AI--ML-Mamdani%20FIS-FF6B6B?style=for-the-badge)

**Intelligent Indoor Climate Control powered by Mamdani Fuzzy Inference**

*25 fuzzy rules · 3 input variables · 17 linguistic sets · centroid defuzzification*

[Live Demo](#-quick-start) · [Architecture](#-system-architecture) · [API Reference](#-rest-api) · [Docker Deploy](#-docker-deployment)

</div>

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [System Architecture](#-system-architecture)
3. [Fuzzy Logic Engine](#-fuzzy-logic-engine)
4. [Input / Output Variables](#-input--output-variables)
5. [Rule Base](#-rule-base)
6. [Installation](#-installation)
7. [Quick Start](#-quick-start)
8. [Docker Deployment](#-docker-deployment)
9. [REST API Reference](#-rest-api-reference)
10. [Frontend Features](#-frontend-features)
11. [Project Structure](#-project-structure)
12. [Requirements Specification](#-requirements-specification)
13. [Contributing](#-contributing)

---

## 🧠 Overview

The **Fuzzy Comfort Control System** is an AI/ML-driven HVAC decision engine that uses **Mamdani fuzzy inference** to determine the optimal heating, cooling, or ventilation action for indoor environments based on real-time sensor data.

Unlike crisp rule-based systems, fuzzy logic gracefully handles the inherent uncertainty and overlap in human comfort perception — a room at 24°C might feel "comfortable" *or* "slightly warm" depending on humidity and CO₂ — and produces a smooth, proportional control output.

### Why Fuzzy Logic?

| Approach | Handling Uncertainty | Interpretability | Smooth Control |
|---|---|---|---|
| Crisp Rules (if-else) | ❌ Binary | ✅ High | ❌ Stepwise |
| Neural Network | ✅ High | ❌ Black box | ✅ Smooth |
| **Mamdani FIS** | ✅ High | ✅ Linguistic rules | ✅ Smooth |
| PID Controller | ⚠️ Limited | ⚠️ Medium | ✅ Smooth |

---

## 🏗️ System Architecture

```

## 🗺️ Architecture Diagram (Mermaid)

The following Mermaid diagram summarizes the system pipeline and components.

```mermaid
flowchart TD
  A[Sensor Inputs\n(Temperature, Humidity, CO₂)] --> B[Fuzzification\n(trimf / trapmf)]
  B --> C[Mamdani Inference\n(25 IF-THEN rules)]
  C --> D[Aggregation\n(max per singleton)]
  D --> E[Defuzzification\n(Centroid COA)]
  E --> F[HVAC Action\n(-1.0..+1.0)]
  F --> G[Actuators & Dashboard]
  subgraph infra [Infrastructure]
    H[Flask REST API]
    I[Docker / Gunicorn]
  end
  E --> H --> I
```

┌─────────────────────────────────────────────────────────────────────────┐
│                    FUZZY COMFORT CONTROL SYSTEM v2.0                    │
│                     Mamdani Inference Architecture                      │
└─────────────────────────────────────────────────────────────────────────┘

   SENSOR INPUTS          FUZZIFICATION          INFERENCE ENGINE
  ┌─────────────┐        ┌─────────────┐        ┌─────────────────┐
  │ Temperature │──┐     │             │         │                 │
  │   (0–50°C)  │  │     │  Triangular │  μ(x)  │  Mamdani FIS   │
  │             │  ├────▶│  Trapezoidal│───────▶│                 │
  │  Humidity   │  │     │     MFs     │         │   25 IF-THEN   │
  │   (0–100%)  │  │     │             │         │     Rules      │
  │             │  │     │  17 Fuzzy   │         │                 │
  │   CO₂ ppm   │──┘     │    Sets     │         │  T-norm: min() │
  │  (0–5000)   │        │             │         │  S-norm: max() │
  └─────────────┘        └─────────────┘        └────────┬────────┘
                                                          │
                                                          ▼
  HVAC ACTUATOR           DEFUZZIFICATION        AGGREGATED OUTPUT
  ┌─────────────┐        ┌─────────────┐        ┌─────────────────┐
  │   Cooling   │        │             │         │                 │
  │  Heating    │◀───────│  Centroid   │◀────────│  9 Output       │
  │ Ventilation │        │   (COA)     │         │  Singletons     │
  │             │        │             │         │                 │
  │  Output:    │        │  ∑(wᵢ·xᵢ)  │         │  [-1.0, +1.0]  │
  │ [-1.0, 1.0] │        │  ─────────  │         │                 │
  └─────────────┘        │    ∑(wᵢ)   │         └─────────────────┘
                         └─────────────┘

   REST API LAYER                           FRONTEND DASHBOARD
  ┌────────────────────┐                  ┌──────────────────────┐
  │  Flask 3.x         │                  │  Dark ML Dashboard   │
  │  POST /api/infer   │◀────────────────▶│  Canvas Gauge        │
  │  GET  /api/health  │                  │  MF Plot Visualizer  │
  │  GET  /api/rules   │                  │  Inference Trace     │
  │  Gunicorn 4 workers│                  │  Responsive CSS Grid │
  └────────────────────┘                  └──────────────────────┘
          │
          ▼
  ┌────────────────────┐
  │  Docker Container  │
  │  python:3.12-slim  │
  │  Port 5000         │
  │  Health checks     │
  └────────────────────┘
```

### Data Flow Pipeline

```
Raw Sensor Reading
       │
       ▼
┌─────────────────────┐
│   Input Validation  │  Clamp to valid range, type check
│   & Preprocessing   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Fuzzification     │  Apply MF functions → μ ∈ [0, 1]
│   trimf / trapmf    │  Per variable, per linguistic set
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Rule Evaluation   │  For each of 25 rules:
│   (Rule Firing)     │  - Compute antecedent strength (min)
│                     │  - Aggregate consequent (max)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Defuzzification   │  Centroid of Area (COA):
│   (COA / Centroid)  │  output = Σ(wᵢ · xᵢ) / Σ(wᵢ)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Post-Processing   │  Comfort score, energy index, AQI
│   & Scoring         │  Human-readable label + icon
└──────────┬──────────┘
           │
           ▼
     JSON Response → Frontend Visualization
```

---

## ⚙️ Fuzzy Logic Engine

### Membership Functions

Two MF types are used:

**Triangular (trimf):** Best for interior sets with a single clear center.
```
       1 ──────────┐
                  /│\
                 / │ \
                /  │  \
       0 ──────/───┴───\──────
               a   b   c
```

**Trapezoidal (trapmf):** Best for boundary sets (very cold, very hot, etc.).
```
       1 ────────┌─────────┐
                /│         │\
               / │         │ \
       0 ─────/──┴─────────┴──\──
              a  b             c d
```

### Inference Method: Mamdani

1. **Fuzzify** each input using its MF sets
2. **Evaluate rules** — antecedent strength via `min()` (AND), `max()` (OR)
3. **Aggregate** — each output singleton gets the `max()` of all rules pointing to it
4. **Defuzzify** — centroid of weighted singletons: `COA = Σ(wᵢ·xᵢ) / Σ(wᵢ)`

---

## 📊 Input / Output Variables

### Input 1: Temperature (°C)

| Linguistic Set | Type | Parameters |
|---|---|---|
| Very Cold | trapmf | [0, 0, 10, 15] |
| Cold | trapmf | [8, 14, 18, 22] |
| Cool | trimf | [18, 21, 24] |
| Comfortable | trimf | [21, 23, 25] |
| Warm | trimf | [23, 26, 29] |
| Hot | trapmf | [27, 31, 40, 40] |
| Very Hot | trapmf | [35, 40, 50, 50] |

### Input 2: Humidity (%)

| Linguistic Set | Type | Parameters |
|---|---|---|
| Very Dry | trapmf | [0, 0, 20, 28] |
| Dry | trimf | [20, 32, 42] |
| Normal | trapmf | [38, 45, 55, 62] |
| Humid | trimf | [58, 68, 78] |
| Very Humid | trapmf | [74, 82, 100, 100] |

### Input 3: CO₂ Level (ppm)

| Linguistic Set | Type | Range |
|---|---|---|
| Fresh | trapmf | 0–650 |
| Normal | trimf | 500–1000 |
| Elevated | trimf | 900–1400 |
| High | trimf | 1200–2200 |
| Dangerous | trapmf | 2000–5000 |

### Output: HVAC Action [-1.0, +1.0]

| Singleton | Value | Meaning |
|---|---|---|
| Full Ventilate | -1.00 | Emergency exhaust/cooling |
| Strong Cool | -0.75 | Aggressive air conditioning |
| Moderate Cool | -0.50 | Moderate cooling |
| Slight Cool | -0.25 | Gentle cooling |
| Neutral | 0.00 | Hold current state |
| Slight Heat | +0.25 | Gentle warming |
| Moderate Heat | +0.50 | Moderate heating |
| Strong Heat | +0.75 | Aggressive heating |
| Full Heat | +1.00 | Maximum heating |

---

## 📋 Rule Base

The system uses **25 fuzzy IF-THEN rules** organized in three categories:

### Temperature-Only Rules (7)
```
R01: IF Temp=Very Cold          → Full Heat
R02: IF Temp=Cold               → Strong Heat
R03: IF Temp=Cool               → Slight Heat
R04: IF Temp=Comfortable        → Neutral
R05: IF Temp=Warm               → Slight Cool
R06: IF Temp=Hot                → Moderate Cool
R07: IF Temp=Very Hot           → Strong Cool
```

### Temperature × Humidity Interaction Rules (6)
```
R08: IF Temp=Comfortable AND Hum=Very Dry   → Slight Heat   (aid humidification)
R09: IF Temp=Comfortable AND Hum=Very Humid → Slight Cool   (dehumidify)
R10: IF Temp=Hot         AND Hum=Very Humid → Full Ventilate
R11: IF Temp=Cool        AND Hum=Dry        → Moderate Heat
R12: IF Temp=Warm        AND Hum=Humid      → Moderate Cool
R13: IF Temp=Cold        AND Hum=Very Humid → Moderate Heat
```

### CO₂ Safety / Override Rules (6)
```
R14: IF CO₂=Dangerous                       → Full Ventilate  (SAFETY)
R15: IF CO₂=High    AND Temp=Hot            → Full Ventilate
R16: IF CO₂=High    AND Temp=Comfortable    → Strong Cool / Vent
R17: IF CO₂=Elevated AND Temp=Comfortable  → Slight Vent
R18: IF CO₂=Elevated AND Temp=Warm         → Moderate Vent
R19: IF CO₂=Fresh   AND Temp=Comfortable   → Neutral
```

### Compound 3-Variable Rules (6)
```
R20: IF Temp=OK  AND Hum=OK   AND CO₂=OK        → Neutral  (Perfect comfort)
R21: IF Temp=Hot AND Hum=Humid AND CO₂=Elevated → Full Ventilate (All stress)
R22: IF Temp=Cold AND Hum=Dry AND CO₂=Fresh     → Strong Heat
R23: IF Temp=Warm AND Hum=Normal AND CO₂=Normal → Slight Cool
R24: IF Temp=Cool AND Hum=Normal AND CO₂=Fresh  → Slight Heat
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+ (3.12 recommended)
- pip
- Docker & Docker Compose (for containerised deployment)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/jawaria-sabir/Fuzzy-Comfort-Control-Requirements-And-Specification.git
cd Fuzzy-Comfort-Control-Requirements-And-Specification

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run development server
python app.py
```

Open http://localhost:5000 in your browser.

---

## ⚡ Quick Start

```bash
# Run with Flask dev server
python app.py

# Run with Gunicorn (production-like)
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

**Try the API immediately:**

```bash
curl -X POST http://localhost:5000/api/infer \
  -H "Content-Type: application/json" \
  -d '{"temperature": 28, "humidity": 70, "co2": 1200}'
```

---

## 🐳 Docker Deployment

### Build & Run (Docker)

```bash
# Build image
docker build -t fuzzy-comfort-control:latest .

# Run container
docker run -d \
  --name fuzzy-comfort-control \
  -p 5000:5000 \
  --restart unless-stopped \
  fuzzy-comfort-control:latest

# Check health
curl http://localhost:5000/api/health
```

### Docker Compose (recommended)

```bash
# Start the full stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `production` | Flask environment |
| `PYTHONUNBUFFERED` | `1` | Stream logs in real-time |

---

## 🔌 REST API Reference

### `POST /api/infer`
Run fuzzy inference on sensor inputs.

**Request:**
```json
{
  "temperature": 26.5,
  "humidity": 65,
  "co2": 900
}
```

**Response:**
```json
{
  "status": "ok",
  "inputs": { "temperature": 26.5, "humidity": 65, "co2": 900 },
  "action_value": -0.2813,
  "action_label": "Slight Cooling",
  "action_icon": "💨",
  "comfort_score": 72.4,
  "energy_index": 83.1,
  "air_quality_index": 80,
  "air_quality_label": "Good",
  "rules_count": 8,
  "rules_fired": [
    { "strength": 0.875, "action": "slight_cool", "description": "T=Warm → Slight Cool" }
  ],
  "memberships": {
    "temperature": { "very_cold": 0, "cold": 0, "cool": 0, "comfortable": 0, "warm": 0.875, "hot": 0.125, "very_hot": 0 },
    "humidity": { ... },
    "co2": { ... }
  },
  "output_activations": {
    "slight_cool": 0.875,
    "moderate_cool": 0.125
  }
}
```

### `GET /api/health`
Service health check.

```json
{ "status": "healthy", "service": "Fuzzy Comfort Control System", "version": "2.0.0" }
```

### `GET /api/rules`
Returns the full rule set metadata as JSON.

---

## 🖥️ Frontend Features

The dashboard is a **single-page ML monitoring interface** with:

| Feature | Description |
|---|---|
| **Animated Gauge** | Canvas-rendered semicircular gauge with needle animation |
| **Fuzzy Bars** | Real-time linguistic set activation display per slider |
| **MF Plot Canvas** | Four live plots: Temperature, Humidity, CO₂, and Output |
| **Inference Trace** | Full fuzzification → rule firing → defuzzification display |
| **KPI Cards** | Comfort Score · Energy Index · Air Quality Index |
| **Responsive Grid** | CSS Grid + Flexbox; adapts to mobile, tablet, desktop |
| **Quick Scenarios** | 4 preset sensor scenarios for rapid testing |
| **Hamburger Nav** | Mobile-friendly navigation menu |
| **Hero Canvas** | Animated wave visualization showing fuzzy MF concept |
| **Architecture Diagram** | Interactive system pipeline visualization |

---

## 📁 Project Structure

```
jaweria/
│
├── app.py                    # Flask app + Mamdani FIS engine
├── requirements.txt          # Python dependencies
├── Dockerfile                # Production Docker image
├── docker-compose.yml        # Full stack orchestration
│
├── templates/
│   └── index.html            # SPA dashboard template
│
├── static/
│   ├── css/
│   │   └── style.css         # Dark ML theme, CSS Grid, responsive
│   └── js/
│       └── main.js           # Canvas, inference, MF plots, slider logic
│
├── docs/
│   └── architecture.md       # Extended architecture documentation
│
└── README.md                 # This file
```

---

## 📐 Requirements Specification

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | System shall accept temperature in range [0, 50]°C |
| FR-02 | System shall accept humidity in range [0, 100]% |
| FR-03 | System shall accept CO₂ in range [0, 5000] ppm |
| FR-04 | System shall output a crisp HVAC action in [-1.0, +1.0] |
| FR-05 | System shall apply Mamdani fuzzy inference with centroid defuzzification |
| FR-06 | System shall expose results via REST API in JSON format |
| FR-07 | CO₂ levels above 2000 ppm shall always trigger ventilation (safety) |
| FR-08 | System shall display linguistic label for inferred action |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Inference latency < 10ms per request |
| NFR-02 | API shall return HTTP 400 for invalid inputs |
| NFR-03 | Container shall pass Docker health checks |
| NFR-04 | Frontend shall be responsive down to 320px viewport |
| NFR-05 | System shall run without external ML libraries (pure Python engine) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/improved-rules`
3. Commit your changes: `git commit -m 'Add winter-mode rule set'`
4. Push to the branch: `git push origin feature/improved-rules`
5. Open a Pull Request

### Areas for Enhancement
- [ ] Add PID hybrid control mode
- [ ] Time-series logging and historical charts
- [ ] MQTT integration for real IoT sensors
- [ ] Takagi-Sugeno FIS comparison mode
- [ ] Rule editor UI for non-programmers
- [ ] Export trained rule base to JSON/FCL format

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Original Project:** [jawaria-sabir](https://github.com/jawaria-sabir/Fuzzy-Comfort-Control-Requirements-And-Specification)
**Enhanced Edition v2.0** — Professional ML Architecture · Docker · Responsive UI

</div>
