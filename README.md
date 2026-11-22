# ORBIT — Orchestrated Robotics Intelligence and Teamwork

**A collaborative three-robot platform that maps, monitors, assists and talks.**

ORBIT is a modular robot team — a stationary supervisor, an autonomous ground robot and a guarded aerial
robot — built on three software pillars: **AI intelligence**, **SLAM & navigation**, and a **router-free mesh
network**, all on top of a deterministic robot-integration and safety layer.

📄 **Presentation:** [docs/ORBIT_Robotics_Team.pdf](docs/ORBIT_Robotics_Team.pdf)

> **Status:** research prototype. Items marked *planned* are not built yet; simulation results are labelled
> as simulation. Nothing here is a claim about a finished, deployed product.

---

## The problem
Facilities still depend on manual patrols and inspections. Faults are found late, coverage varies by person
and shift, and single-purpose robots can't adapt to new tasks.

## Design principles
1. Modular and replaceable  2. Safety independent of AI  3. Works without internet
4. Observation ≠ interpretation  5. Privacy by design  6. Measure, never assume

## The three-robot team
| Unit | Compute | Role |
|---|---|---|
| Stationary Supervisor | Raspberry Pi 5 (16 GB) + ESP32-S3 | Sensor hub, shared map, operator interface, fleet coordination |
| Ground Robot | Jetson Orin Nano Super + ESP32-S3 + Roboclaw | Mapping, navigation, inspection, transport |
| Aerial Robot | Commercial guarded drone (own flight controller) | Overhead observation, operator-supervised only |

Safety lives below the AI: microcontrollers handle real-time I/O, motors are never driven by the AI,
a physical e-stop and heartbeat watchdog stop the robot, and power rails are separately fused.

---

## What's in this repository

```text
orbit/
├── docs/
│   ├── persona.md              ORBIT persona spec — annotation guideline for all AI data
│   └── ORBIT_Robotics_Team.pdf presentation deck
├── tools/
│   ├── tool_schemas.json       13 tools: JSON schemas, permission levels, timeouts
│   └── validate_call.py        schema + role-permission validator
├── safety/
│   └── guard.py                crisis detector, permission check, site-ID check, LLM classifier layer
├── config/
│   └── site_demo.json          demo site: robots, zones, waypoints, assets
├── datasets/
│   ├── build_gold.py           50 hand-written gold training examples
│   ├── build_eval.py           134-case evaluation set (54 safety tests)
│   ├── check_dataset.py        automatic dataset quality checks
│   ├── run_eval.py             evaluation runner against a local Ollama model (--guard = full pipeline)
│   ├── eval_crisis.py          crisis-detector scorer (dev + hidden sets)
│   ├── gold/ eval/ results/    data files and recorded results
├── mesh/
│   ├── sim.py                  mesh routing simulator: greedy, greedy+recovery, multi-metric
│   └── mesh_scenario.png
└── video/
    ├── make_images.py          generates the project slides from real results
    └── frames/                 15 slides, 1920×1080
```

---

## Pillar 1 — AI Intelligence
- **Qwen3-4B-Instruct-2507** runs locally (Ollama, Q4_K_M) as the reasoning core. The model plans;
  deterministic code validates and executes.
- Flow: voice/text → **safety guard** → Qwen3-4B → **tool registry** → **permission + site-ID check** → ROS 2 / fleet.
- The AI never drives motors, never runs code, and never says "done" without a successful tool result.
- Companion persona: warm, honest about being a robot, English / Tamil / Tanglish, with hard boundaries
  (no diagnosis, no romantic roleplay, no face identification).

### Measured results (laptop RTX 4050, median ≈ 3.5 s)
| Setup | All tests (25) | Safety tests (12) |
|---|---|---|
| Base model, short prompt | 64% | 50% |
| Stronger prompt | 76% | 75% |
| Prompt + safety guard | 88% | 92% |
| + real site IDs | 100% | 100% |

On a harder **134-case** set: **109/134 overall, 44/54 safety tests**. Known gaps: indirect crisis wording and
multi-step planning. In progress: an LLM crisis-classifier layer evaluated on a hidden test set.
LoRA fine-tuning is planned only after these baselines.

```bash
ollama pull qwen3:4b-instruct-2507-q4_K_M
pip install jsonschema
cd datasets
python build_gold.py && python build_eval.py
python check_dataset.py gold/gold_v0.1.jsonl --eval eval/eval_v0.2.jsonl
python run_eval.py --model qwen3:4b-instruct-2507-q4_K_M --guard
```

## Pillar 2 — SLAM & Navigation *(planned)*
RPLIDAR S2 → **SLAM Toolbox**; ESP32 encoders + IMU → odometry bridge + EKF (`robot_localization`);
RealSense D455 → obstacle detection; **Nav2** plans motion; ORBIT AI sends goals. 3D mapping with RTAB-Map later.
The ground robot builds the map; the supervisor localises on it and watches for changes.

## Pillar 3 — Mesh Network
Router-free, internet-free communication: ESP32 nodes over ESP-NOW with an ORBIT multi-hop layer on top.
Robots know their positions from SLAM, so packets use **greedy geographic forwarding** — no routing tables
to rebuild as robots move. **MIDA** (Multi-metric Intelligent Dynamic Adaptation), the team's own routing
algorithm, weighs geographic progress, link stability and congestion.

**Simulation** (120 m × 70 m workshop, 8 runs each): 18 m relay grid → 92–96% delivered; 15 m grid → 99%;
sparse random relays → 32–40%. Recovery mode adds up to 17 points in patchy layouts.
*Note:* the "mida" mode in `mesh/sim.py` is a simplified placeholder, not the full MIDA algorithm.
A full MIDA benchmark against GPSR and OLSR under heavy load is planned.

```bash
pip install matplotlib
cd mesh && python sim.py --plot
```

---

## Roadmap
| Done | Now (planned) | Next (planned) | Then (planned) |
|---|---|---|---|
| Persona + tool registry | Crisis classifier | ESP32 firmware | Two-robot missions |
| Safety guard | Gazebo SLAM demo | Real LiDAR mapping | Supervisor map sharing |
| Evaluation suite | Nav2 + AI bridge | Mesh on hardware | Fine-tuning |
| Mesh simulator | MIDA benchmark | Voice interface | Field trials |

---

**ORBIT — Understand. Monitor. Assist. Coordinate.**
