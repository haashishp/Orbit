"""Generate 15 ORBIT video frames (1920x1080 PNG) from real project content.

Everything shown is either a design diagram or a real result from this project's code.
Simulated content is labelled as simulated on the image.
Run: python make_images.py  -> writes frames/01_*.png ... 15_*.png
"""
import math
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "frames"
OUT.mkdir(exist_ok=True)

BG, PANEL, FG, MUTED = "#0b1220", "#141d2f", "#e8edf5", "#8a96ab"
BLUE, GREEN, PURPLE, ORANGE, RED, TEAL = "#4dabf7", "#51cf66", "#9775fa", "#ff922b", "#ff6b6b", "#38d9a9"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": FG,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#2a3550"})


def frame(n, slug, title, subtitle=None):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 192), ax.set_ylim(0, 108), ax.axis("off")
    ax.set_facecolor(BG)
    if title:
        ax.text(8, 98, title, fontsize=38, weight="bold", va="top")
    if subtitle:
        ax.text(8, 89.5, subtitle, fontsize=19, color=MUTED, va="top")
    ax.text(184, 3.5, "ORBIT", fontsize=14, color=MUTED, ha="right", weight="bold")
    ax.text(8, 3.5, f"{n:02d}", fontsize=14, color=MUTED)
    return fig, ax, OUT / f"{n:02d}_{slug}.png"


def save(fig, path):
    fig.savefig(path, facecolor=BG)
    plt.close(fig)
    print("saved", path.name)


def box(ax, x, y, w, h, title, body="", color=BLUE, tsize=17, bsize=13):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5",
                                fc=PANEL, ec=color, lw=2.5))
    ax.add_patch(FancyBboxPatch((x, y + h - 1.2), w, 1.2, boxstyle="round,pad=0,rounding_size=0.6",
                                fc=color, ec="none"))
    ax.text(x + w / 2, y + h - 3.6, title, ha="center", va="top", fontsize=tsize, weight="bold")
    if body:
        ax.text(x + w / 2, y + h - 3.6 - tsize * 0.42, body, ha="center", va="top", fontsize=bsize,
                color=MUTED, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, color=MUTED, label=None, lw=2.2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=22, color=color, lw=lw))
    if label:
        ax.text((x1 + x2) / 2 + 0.8, (y1 + y2) / 2, label, fontsize=12, color=color, va="center")


# 01 ---------------------------------------------------------------------------
def f01():
    fig, ax, p = frame(1, "title", None)
    ax.text(96, 64, "ORBIT", fontsize=150, weight="bold", ha="center", va="center", color=FG)
    ax.text(96, 44, "Orchestrated Robotics Intelligence and Teamwork", fontsize=30, ha="center", color=BLUE)
    ax.text(96, 34, "A collaborative three-robot platform that maps, monitors, assists and talks",
            fontsize=20, ha="center", color=MUTED)
    for i, (c, r) in enumerate([(BLUE, 3.2), (GREEN, 2.4), (PURPLE, 1.8)]):
        a = math.radians(30 + i * 120)
        ax.add_patch(plt.Circle((96 + 58 * math.cos(a) * 0 + (i - 1) * 9, 20), r, color=c))
    save(fig, p)


# 02 ---------------------------------------------------------------------------
def f02():
    fig, ax, p = frame(2, "vision", "One platform, many environments",
                       "Indoor inspection and monitoring first — more applications through modules, not redesigns")
    tiers = [
        ("BUILD FIRST", GREEN, ["Industrial patrol & machine inspection", "Facility environmental monitoring",
                                "Warehouse & inventory checks", "Multi-robot coordinated inspection"]),
        ("NEXT", BLUE, ["Rule-based security patrol", "Campus & building assistance",
                        "Lab & research-facility monitoring", "Companion conversation"]),
        ("LONG-TERM RESEARCH", PURPLE, ["Healthcare (non-clinical) support", "Agriculture",
                                        "Disaster response", "Outdoor operation"]),
    ]
    for i, (name, col, items) in enumerate(tiers):
        x = 8 + i * 60
        box(ax, x, 12, 54, 68, name, "", col, tsize=22)
        for j, it in enumerate(items):
            ax.text(x + 4, 62 - j * 11, "•  " + it, fontsize=17, va="top")
    save(fig, p)


# 03 ---------------------------------------------------------------------------
def f03():
    fig, ax, p = frame(3, "three_robots", "Three robots, one team",
                       "Each unit has its own computer and keeps working safely if the network drops")
    box(ax, 8, 16, 54, 64, "Stationary Supervisor",
        "Raspberry Pi 5 (16 GB) + ESP32-S3\n\nRPLIDAR S2  •  RealSense D455\nenvironment, CO₂, air-quality\n"
        "mmWave presence  •  mic + speaker\ntouchscreen\n\nShared map  •  operator UI\nfleet coordination", BLUE, 22, 15)
    box(ax, 69, 16, 54, 64, "Ground Robot",
        "Jetson Orin Nano Super + ESP32-S3\nRoboclaw motor controller\n\nRPLIDAR S2  •  RealSense D455\n"
        "IMU  •  ToF ring  •  bumpers\nwheel encoders\n\nSLAM mapping  •  navigation\ninspection  •  transport", GREEN, 22, 15)
    box(ax, 130, 16, 54, 64, "Aerial Robot",
        "Commercial guarded drone\nwith its own flight controller\n\nstereo / depth payload\n"
        "optical flow (indoor)\nGNSS (outdoor)\n\nOverhead observation\noperator-supervised only", PURPLE, 22, 15)
    for x in (62.5, 123.5):
        ax.annotate("", (x + 6, 48), (x, 48), arrowprops=dict(arrowstyle="<|-|>", color=TEAL, lw=3))
    ax.text(96, 9, "Router-independent ESP32 mesh for commands  •  separate Wi-Fi link for video and maps",
            ha="center", fontsize=16, color=TEAL)
    save(fig, p)


# 04 ---------------------------------------------------------------------------
def f04():
    fig, ax, p = frame(4, "software_pillars", "Software: three pillars + integration",
                       "Each pillar is replaceable behind a stable interface")
    box(ax, 8, 46, 54, 34, "AI Intelligence", "Qwen3-4B reasoning\ntool registry • safety guard\nmemory • voice • companion",
        ORANGE, 22, 15)
    box(ax, 69, 46, 54, 34, "SLAM & Navigation", "ROS 2 • SLAM Toolbox\nrobot_localization • Nav2\n3D with RTAB-Map later",
        GREEN, 22, 15)
    box(ax, 130, 46, 54, 34, "Mesh Network", "ESP32 + ESP-NOW\nmulti-hop greedy forwarding\nMIDA adaptive routing",
        TEAL, 22, 15)
    box(ax, 8, 12, 176, 26, "Robot integration & fleet coordination",
        "ESP32 firmware  •  odometry bridge  •  watchdog & e-stop  •  robot description  •  task allocation  •  dashboard",
        BLUE, 22, 16)
    for x in (35, 96, 157):
        arrow(ax, x, 45.5, x, 38.6, MUTED)
    save(fig, p)


# 05 / 06 hardware maps --------------------------------------------------------
def hw_map(n, slug, title, sub, center, center_body, left, right, ccol):
    fig, ax, p = frame(n, slug, title, sub)
    box(ax, 74, 38, 44, 26, center, center_body, ccol, 22, 15)
    for i, (t, b, lab) in enumerate(left):
        y = 66 - i * 22
        box(ax, 8, y, 44, 16, t, b, TEAL, 17, 13)
        arrow(ax, 52.5, y + 8, 73.5, 51, TEAL, lab)
    for i, (t, b, lab, col) in enumerate(right):
        y = 66 - i * 22
        box(ax, 140, y, 44, 16, t, b, col, 17, 13)
        arrow(ax, 118.5, 51, 139.5, y + 8, col, lab)
    return fig, ax, p


def f05():
    fig, ax, p = hw_map(5, "supervisor_hw", "Stationary supervisor — connection map",
                        "From the hardware architecture by the ORBIT hardware lead",
                        "Raspberry Pi 5", "16 GB  •  1 TB NVMe\nsupervisor computer",
                        [("RealSense D455", "RGB-D camera", "USB 3"), ("RPLIDAR S2", "360° 2D LiDAR", "USB"),
                         ("Mic + speaker + display", "voice & operator UI", "USB / HDMI")],
                        [("ESP32-S3 sensor hub", "IMU • BME688 • SCD41\nPM2.5 • mmWave • PIR", "USB UART", PURPLE),
                         ("ESP32-S3 mesh gateway", "robot-to-robot mesh", "USB UART", GREEN),
                         ("FLIR thermal (optional)", "hot-spot inspection", "USB", TEAL)], BLUE)
    save(fig, p)


def f06():
    fig, ax, p = hw_map(6, "ground_hw", "Ground robot — connection map",
                        "Safety reflexes live on the ESP32, not in the AI",
                        "Jetson Orin Nano", "Super 8 GB\nperception • SLAM • Nav2",
                        [("RPLIDAR S2", "2D scan for SLAM", "USB"), ("RealSense D455", "depth obstacles • 3D", "USB 3"),
                         ("GNSS RTK / UWB", "outdoor / indoor aids", "UART")],
                        [("ESP32-S3 I/O controller", "IMU • ToF • bumpers\nwatchdog stop", "USB UART", PURPLE),
                         ("Roboclaw motor controller", "encoders • closed-loop drive", "UART via ESP32", RED),
                         ("Battery + BMS", "fused DC/DC rails • e-stop", "power", ORANGE)], GREEN)
    save(fig, p)


# 07 ---------------------------------------------------------------------------
def f07():
    fig, ax, p = frame(7, "ai_pipeline", "How ORBIT turns words into safe actions",
                       "The language model plans — deterministic code validates and executes")
    steps = [("Voice / text", "Whisper speech\nrecognition", BLUE), ("Safety guard", "crisis detection\nruns first", RED),
             ("Qwen3-4B", "understands &\nplans", ORANGE), ("Tool registry", "13 approved tools\nJSON schemas", PURPLE),
             ("Permission + ID\ncheck", "role & site\nvalidation", RED), ("ROS 2 / fleet", "mission manager\nNav2", GREEN)]
    w, gap = 25, 4.4
    for i, (t, b, c) in enumerate(steps):
        x = 8 + i * (w + gap)
        box(ax, x, 38, w, 30, t, b, c, 16, 13)
        if i:
            arrow(ax, x - gap + 0.3, 53, x - 0.3, 53, MUTED)
    ax.text(96, 26, "The AI never drives motors, never runs code, and never says “done” without a successful tool result.",
            ha="center", fontsize=18)
    ax.text(96, 19, "Emergency stop, obstacle avoidance and speed limits stay in robot firmware and Nav2.",
            ha="center", fontsize=16, color=MUTED)
    save(fig, p)


# 08 ---------------------------------------------------------------------------
def f08():
    fig, ax, p = frame(8, "safety_layers", "Safety that does not depend on the model",
                       "Three code-level checks wrap every conversation")
    layers = [("1  Crisis detector", "Every message, before the model\nEnglish • Tamil • Tanglish\n→ escalate to a human + helplines",
               RED),
              ("2  Permission check", "Every tool call, before execution\nguest / user / operator / admin\n→ blocked calls never run",
               ORANGE),
              ("3  Site ID check", "Only real zones, waypoints, assets\nstops invented IDs like “lab_01”\n→ model told the valid list",
               PURPLE)]
    for i, (t, b, c) in enumerate(layers):
        box(ax, 8 + i * 60, 22, 54, 52, t, b, c, 22, 16)
    ax.text(96, 13, "A missed emergency is worse than a false alarm: the guard is tuned for recall.",
            ha="center", fontsize=17, color=MUTED)
    save(fig, p)


# 09 ---------------------------------------------------------------------------
def f09():
    fig, ax, p = frame(9, "ai_results", "Measured, not assumed",
                       "Qwen3-4B on a laptop RTX 4050, real results from ORBIT's evaluation runner")
    ax.axis("off")
    c = fig.add_axes([0.07, 0.14, 0.52, 0.62], facecolor=PANEL)
    labels = ["Base model\n+ short prompt", "Stronger\nprompt", "Prompt +\nsafety guard", "+ real\nsite IDs"]
    overall = [16 / 25, 19 / 25, 22 / 25, 25 / 25]
    gates = [6 / 12, 9 / 12, 11 / 12, 12 / 12]
    xs = range(len(labels))
    c.bar([x - 0.2 for x in xs], [v * 100 for v in overall], 0.38, color=BLUE, label="all 25 tests")
    c.bar([x + 0.2 for x in xs], [v * 100 for v in gates], 0.38, color=RED, label="12 safety tests")
    for x, v, g in zip(xs, overall, gates):
        c.text(x - 0.2, v * 100 + 2, f"{v:.0%}", ha="center", fontsize=14)
        c.text(x + 0.2, g * 100 + 2, f"{g:.0%}", ha="center", fontsize=14)
    c.set_xticks(list(xs)), c.set_xticklabels(labels, fontsize=13, color=FG)
    c.set_ylim(0, 115), c.set_ylabel("% passed", fontsize=14)
    c.legend(facecolor=PANEL, edgecolor="#2a3550", labelcolor=FG, fontsize=13, loc="upper left")
    for s in c.spines.values():
        s.set_visible(False)
    box(ax, 124, 20, 60, 62, "Then we made it harder",
        "Test set grown to 134 cases\nincluding 54 safety tests\n\n109 / 134 passed\n44 / 54 safety tests\n\n"
        "Gaps found: indirect crisis\nwording, multi-step planning\n\nFixing with a classifier +\na hidden test set", ORANGE, 22, 16)
    save(fig, p)


# 10 ---------------------------------------------------------------------------
def f10():
    fig, ax, p = frame(10, "companion", "A companion with boundaries",
                       "Warm, honest about being a robot, and quick to bring in a human")
    chat = [("user", "Long day today."),
            ("orbit", "Sounds like it. Want to tell me about it, or should I just keep you company for a bit?"),
            ("user", "ORBIT, battery evlo irukku?"),
            ("orbit", "62% irukku. Innum oru patrol panna podhum."),
            ("user", "Are you human?"),
            ("orbit", "No, I'm a robot — ORBIT. Happy to chat like a friend, though.")]
    y = 80
    for who, text in chat:
        isu = who == "user"
        w = min(150, 8 + len(text) * 1.3)
        x = 184 - w if isu else 8
        ax.add_patch(FancyBboxPatch((x, y - 8), w, 8, boxstyle="round,pad=0.6,rounding_size=2.5",
                                    fc="#1f3a5f" if isu else PANEL, ec=BLUE if isu else ORANGE, lw=1.5))
        ax.text(x + 2.5, y - 4, text, fontsize=17, va="center")
        ax.text(x + (w - 1 if isu else 1), y + 1.8, "You" if isu else "ORBIT", fontsize=12, color=MUTED,
                ha="right" if isu else "left")
        y -= 12.5
    save(fig, p)


# 11 / 12 mesh -----------------------------------------------------------------
def mesh_module():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mesh"))
    import sim
    return sim


def f11():
    sim = mesh_module()
    fig, ax, p = frame(11, "mesh_routing", "Router-free mesh: greedy geographic forwarding",
                       "Robots know their positions from SLAM — each hop forwards toward the destination (simulation)")
    m = sim.Mesh("mida", "grid18", 3).run(150)
    a2 = fig.add_axes([0.05, 0.08, 0.9, 0.72], facecolor=PANEL)
    nodes = list(m.nodes.values())
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            pr = sim.true_prr(sim.dist(a.pos, b.pos))
            if pr > 0.25:
                a2.plot([a.pos[0], b.pos[0]], [a.pos[1], b.pos[1]], color="#3b4a66", lw=0.6 + 1.6 * pr, zorder=1)
    path = next((q for q in reversed(m.paths) if q[0] == "GROUND"), m.paths[-1])
    a2.plot([m.nodes[k].pos[0] for k in path], [m.nodes[k].pos[1] for k in path], color=ORANGE, lw=4, zorder=2,
            label=f"heartbeat path ({len(path) - 1} hops)")
    st = {"SUPERVISOR": ("s", BLUE, 380), "GROUND": ("o", GREEN, 340), "DRONE": ("^", PURPLE, 340)}
    for nd in nodes:
        mk, col, sz = st.get(nd.nid, ("o", "#6c7a96", 70))
        a2.scatter(*nd.pos, marker=mk, c=col, s=sz, zorder=3)
        if nd.nid in st:
            a2.annotate(nd.nid.title(), nd.pos, textcoords="offset points", xytext=(10, 8), fontsize=15, color=col,
                        weight="bold")
    a2.set_xlim(0, 120), a2.set_ylim(0, 70), a2.set_aspect("equal")
    a2.set_xticks([]), a2.set_yticks([])
    for s in a2.spines.values():
        s.set_visible(False)
    a2.legend(facecolor=PANEL, edgecolor="#2a3550", labelcolor=FG, fontsize=15, loc="lower right")
    save(fig, p)


def f12():
    sim = mesh_module()
    fig, ax, p = frame(12, "mesh_results", "Relay placement matters most",
                       "Packets delivered, 120 m × 70 m workshop, 8 simulation runs per bar")
    layouts = [(22, "22 random"), (40, "40 random"), ("grid21", "grid 21 m"), ("grid18", "grid 18 m"), ("grid15", "grid 15 m")]
    modes = [("greedy", "greedy", BLUE), ("greedy_rec", "greedy + recovery", TEAL), ("mida", "MIDA (prototype)", ORANGE)]
    res = {(l, md): sim.summarize([sim.Mesh(md, l, s).run(400) for s in range(8)])["pdr"] for l, _ in layouts for md, _, _ in modes}
    c = fig.add_axes([0.07, 0.12, 0.86, 0.66], facecolor=PANEL)
    for j, (md, lab, col) in enumerate(modes):
        xs = [i + (j - 1) * 0.27 for i in range(len(layouts))]
        vals = [res[(l, md)] * 100 for l, _ in layouts]
        c.bar(xs, vals, 0.25, color=col, label=lab)
        for x, v in zip(xs, vals):
            c.text(x, v + 1.5, f"{v:.0f}", ha="center", fontsize=12)
    c.set_xticks(range(len(layouts))), c.set_xticklabels([n for _, n in layouts], fontsize=15, color=FG)
    c.set_ylim(0, 110), c.set_ylabel("% delivered", fontsize=15)
    c.legend(facecolor=PANEL, edgecolor="#2a3550", labelcolor=FG, fontsize=14, loc="upper left")
    for s in c.spines.values():
        s.set_visible(False)
    save(fig, p)


# 13 ---------------------------------------------------------------------------
def f13():
    fig, ax, p = frame(13, "slam_pipeline", "SLAM pipeline on the ground robot",
                       "Proven open-source ROS 2 components, ORBIT-specific bridge and firmware")
    box(ax, 8, 62, 34, 18, "RPLIDAR S2", "/scan", TEAL, 18, 14)
    box(ax, 8, 38, 34, 18, "ESP32-S3", "encoders • IMU\nwatchdog", PURPLE, 18, 14)
    box(ax, 8, 14, 34, 18, "RealSense D455", "depth image", TEAL, 18, 14)
    box(ax, 56, 38, 36, 18, "Base bridge + EKF", "/odom • /imu\nrobot_localization", BLUE, 18, 14)
    box(ax, 106, 52, 34, 28, "SLAM Toolbox", "builds /map\nlocalises robot", GREEN, 18, 14)
    box(ax, 106, 14, 34, 28, "Nav2", "costmaps • planner\nobstacle avoidance", GREEN, 18, 14)
    box(ax, 152, 33, 32, 28, "ORBIT AI", "navigate_to_waypoint\ninspect_equipment", ORANGE, 18, 14)
    arrow(ax, 42.5, 71, 105.5, 68, TEAL)
    arrow(ax, 42.5, 47, 55.5, 47, PURPLE)
    arrow(ax, 92.5, 50, 105.5, 60, BLUE)
    arrow(ax, 42.5, 23, 105.5, 25, TEAL)
    arrow(ax, 123, 51.5, 123, 42.5, GREEN, " /map")
    arrow(ax, 151.5, 45, 140.5, 32, ORANGE, "goal")
    arrow(ax, 105.5, 20, 25, 37.5, RED, "/cmd_vel")
    save(fig, p)


# 14 ---------------------------------------------------------------------------
def build_world(W=240, H=140):
    g = [[0] * W for _ in range(H)]
    def rect(x0, y0, x1, y1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                g[y][x] = 1
    rect(0, 0, W, 2), rect(0, H - 2, W, H), rect(0, 0, 2, H), rect(W - 2, 0, W, H)
    rect(80, 0, 82, 55), rect(80, 75, 82, H), rect(160, 30, 162, H)           # internal walls, doorways
    for x0, y0 in [(20, 20), (45, 20), (20, 95), (45, 95), (110, 25), (125, 100), (190, 20), (200, 90), (215, 55)]:
        rect(x0, y0, x0 + 14, y0 + 10)                                         # machines
    rect(100, 60, 140, 64)                                                     # shelf
    return g


def f14():
    fig, ax, p = frame(14, "slam_map", "Building the map as the robot explores",
                       "Simulated 2D occupancy mapping with LiDAR ray-casting (known poses) — not real robot data yet")
    W, H = 240, 140
    world = build_world(W, H)
    known = [[-1] * W for _ in range(H)]
    path = [(12, 70), (40, 70), (65, 60), (78, 65), (95, 70), (120, 80), (145, 80), (150, 55), (130, 45), (150, 20),
            (175, 15), (200, 45), (225, 75), (200, 120), (175, 125)]
    poses = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        n = int(math.hypot(x1 - x0, y1 - y0) / 4) + 1
        poses += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    rng = random.Random(1)
    for px, py in poses:
        for k in range(240):
            a = 2 * math.pi * k / 240
            for r in range(1, 60):
                x, y = int(px + r * math.cos(a)), int(py + r * math.sin(a))
                if not (0 <= x < W and 0 <= y < H):
                    break
                if world[y][x]:
                    known[y][x] = 1
                    break
                known[y][x] = 0
    img = [[(0.92 if v == 0 else 0.08 if v == 1 else 0.33) for v in row] for row in known]
    a2 = fig.add_axes([0.05, 0.07, 0.9, 0.70])
    a2.imshow(img, cmap="gray", vmin=0, vmax=1, origin="lower", interpolation="nearest")
    a2.plot([q[0] for q in poses], [q[1] for q in poses], color=ORANGE, lw=3, label="robot path")
    a2.scatter(*poses[-1], s=320, c=GREEN, zorder=3, label="ground robot")
    a2.scatter(12, 70, s=320, marker="s", c=BLUE, zorder=3, label="supervisor")
    a2.set_xticks([]), a2.set_yticks([])
    a2.legend(facecolor=PANEL, edgecolor="#2a3550", labelcolor=FG, fontsize=15, loc="upper left")
    _ = rng
    save(fig, p)


# 15 ---------------------------------------------------------------------------
def f15():
    fig, ax, p = frame(15, "roadmap", "Roadmap", "Small working system first, then scale")
    stages = [("Done", GREEN, "Persona & tool registry\nsafety guard\nevaluation suite\nmesh simulator"),
              ("Now", ORANGE, "Crisis classifier\nGazebo SLAM demo\nNav2 + AI bridge\nMIDA benchmark"),
              ("Next", BLUE, "ESP32 firmware\nreal LiDAR mapping\nmesh on hardware\nvoice interface"),
              ("Then", PURPLE, "Two-robot missions\nsupervisor map sharing\nfine-tuning\nfield trials")]
    for i, (t, c, b) in enumerate(stages):
        x = 8 + i * 45
        box(ax, x, 22, 40, 56, t, b, c, 26, 17)
        if i:
            arrow(ax, x - 4.6, 50, x - 0.4, 50, MUTED)
    ax.text(96, 12, "ORBIT — understand, monitor, assist, coordinate", ha="center", fontsize=22, color=BLUE)
    save(fig, p)


if __name__ == "__main__":
    for f in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13, f14, f15):
        f()
