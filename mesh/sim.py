"""ORBIT mesh routing simulator — greedy geographic forwarding.

Why geographic routing fits ORBIT: every robot already knows its position from SLAM, and poses are shared
over the mesh anyway. So a node can forward a packet to whichever neighbour is closest to the destination,
with no routing tables to build or repair when robots move.

Layering (matches the hardware doc):
  ESP-NOW  = single-hop radio primitive (broadcast beacons + acked unicast, ~250 B payload)
  THIS     = ORBIT multi-hop layer on top (greedy forwarding), turning ESP-NOW into a real mesh
  Fleet    = decides WHAT to send (tasks, heartbeats, alarms). Video/maps go over the separate Wi-Fi link.

Routing modes compared:
  greedy        pure greedy: forward to the neighbour closest to the destination; drop at a void
  greedy_rec    greedy + recovery: at a void, try the best unvisited neighbour (bounded by TTL)
  mida          multi-metric greedy (MIDA idea): score = progress + link quality + low congestion,
                with the same recovery
NOTE: recovery here is a simple visited-list backtrack, not GPSR face routing (which needs graph
planarization). It is good enough to compare against; GPSR is a later benchmark.

Run: python sim.py            (experiment table)
     python sim.py --plot     (also saves mesh_scenario.png)
"""
import argparse
import math
import random
from collections import Counter, deque
from dataclasses import dataclass, field

RANGE = 25.0          # metres, nominal radio range (indoor ESP32 with walls: set from real measurements)
AREA = (120.0, 70.0)  # workshop floor, metres
QMAX = 20             # packet queue length per node
SERVICE = 3           # packets a node can transmit per tick
RETRIES = 3           # MAC retries per hop (ESP-NOW unicast acks)
TTL = 32
BEACON_EWMA = 0.3     # smoothing for link-quality estimate
NEIGH_TIMEOUT = 5     # ticks before a silent neighbour is dropped


def frange(start, stop, step):
    v = start
    while v < stop:
        yield v
        v += step


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def true_prr(d):
    """Packet reception ratio vs distance: solid up close, fading near the edge."""
    if d <= 0.6 * RANGE:
        return 0.98
    if d >= RANGE:
        return 0.0
    return 0.98 - 0.88 * (d - 0.6 * RANGE) / (0.4 * RANGE)


@dataclass
class Packet:
    pid: int
    src: str
    dst: str
    created: int
    kind: str = "heartbeat"
    ttl: int = TTL
    hops: int = 0
    visited: set = field(default_factory=set)
    path: list = field(default_factory=list)


@dataclass
class Node:
    nid: str
    pos: tuple
    mobile: bool = False
    waypoints: list = field(default_factory=list)
    speed: float = 0.0
    queue: deque = field(default_factory=deque)
    neigh: dict = field(default_factory=dict)  # nid -> {pos, lq, q, seen}

    def step_motion(self):
        if not self.mobile or not self.waypoints:
            return
        tx, ty = self.waypoints[0]
        d = dist(self.pos, (tx, ty))
        if d <= self.speed:
            self.pos = (tx, ty)
            self.waypoints.append(self.waypoints.pop(0))  # loop the patrol
        else:
            self.pos = (self.pos[0] + (tx - self.pos[0]) * self.speed / d,
                        self.pos[1] + (ty - self.pos[1]) * self.speed / d)


class Mesh:
    def __init__(self, mode, n_relays, seed, traffic=0.6):
        self.mode, self.rng, self.t, self.traffic = mode, random.Random(seed), 0, traffic
        self.stats = Counter()
        self.lat, self.hops, self.paths = [], [], []
        self.pid = 0
        W, H = AREA
        self.nodes = {
            "SUPERVISOR": Node("SUPERVISOR", (8.0, H / 2)),
            "GROUND": Node("GROUND", (20.0, 15.0), True,
                           [(110, 10), (110, 60), (60, 60), (20, 15)], 1.2),
            "DRONE": Node("DRONE", (100.0, 55.0), True, [(60, 35), (115, 65), (100, 20)], 2.0),
        }
        if isinstance(n_relays, str) and n_relays.startswith("grid"):
            # Planned deployment: relays on a grid with given spacing, small placement error.
            s = float(n_relays[4:])
            pts = [(x, y) for x in frange(s / 2, W, s) for y in frange(s / 2, H, s)]
        else:
            pts = [(self.rng.uniform(5, W - 5), self.rng.uniform(5, H - 5)) for _ in range(n_relays)]
        for i, (x, y) in enumerate(pts):
            j = 1.5 if isinstance(n_relays, str) else 0
            self.nodes[f"R{i:02d}"] = Node(f"R{i:02d}", (x + self.rng.uniform(-j, j), y + self.rng.uniform(-j, j)))

    # ---------- link layer ----------
    def beacons(self):
        for a in self.nodes.values():
            for b in self.nodes.values():
                if a is b:
                    continue
                p = true_prr(dist(a.pos, b.pos))
                got = self.rng.random() < p
                e = b.neigh.get(a.nid)
                if got:
                    # New neighbours start pessimistic; quality must be earned over several beacons.
                    lq = (e["lq"] * (1 - BEACON_EWMA) + BEACON_EWMA) if e else BEACON_EWMA
                    b.neigh[a.nid] = {"pos": a.pos, "lq": lq, "q": len(a.queue), "seen": self.t}
                elif e:
                    e["lq"] *= (1 - BEACON_EWMA)
            a.neigh = {k: v for k, v in a.neigh.items() if self.t - v["seen"] <= NEIGH_TIMEOUT}

    def send_hop(self, a, b):
        p = true_prr(dist(a.pos, b.pos))
        return any(self.rng.random() < p for _ in range(RETRIES))

    # ---------- routing ----------
    def next_hops(self, node, pkt):
        """Ranked candidate next hops (best first). Empty list = void / nowhere to go."""
        dpos = self.nodes[pkt.dst].pos  # pose table: positions shared via heartbeats (SLAM poses)
        nb = {k: v for k, v in node.neigh.items() if v["lq"] > 0.25}
        my_d = dist(node.pos, dpos)
        closer = {k: v for k, v in nb.items() if dist(v["pos"], dpos) < my_d}
        if closer:
            if self.mode == "mida":
                def score(item):
                    k, v = item
                    if k == pkt.dst:
                        return 10 * v["lq"]  # destination in range: strongly prefer if link is decent
                    progress = (my_d - dist(v["pos"], dpos)) / RANGE
                    return 0.5 * progress + 0.3 * v["lq"] + 0.2 * (1 - v["q"] / QMAX)
                ranked = sorted(closer.items(), key=score, reverse=True)
            else:
                ranked = sorted(closer.items(), key=lambda kv: dist(kv[1]["pos"], dpos))
            return [k for k, _ in ranked]
        # void: no neighbour makes progress
        self.stats["void_hits"] += 1
        if self.mode == "greedy":
            return []
        options = {k: v for k, v in nb.items() if k not in pkt.visited}
        return [k for k, _ in sorted(options.items(), key=lambda kv: dist(kv[1]["pos"], dpos))]

    # ---------- traffic ----------
    def generate(self):
        for src in ("GROUND", "DRONE"):
            if self.rng.random() < self.traffic:
                self.inject(src, "SUPERVISOR", "heartbeat")
        if self.rng.random() < 0.3:
            self.inject("SUPERVISOR", self.rng.choice(["GROUND", "DRONE"]), "task")

    def inject(self, src, dst, kind):
        self.pid += 1
        node = self.nodes[src]
        pkt = Packet(self.pid, src, dst, self.t, kind, visited={src}, path=[src])
        self.stats["sent"] += 1
        if len(node.queue) >= QMAX:
            self.stats["drop_queue"] += 1
        else:
            node.queue.append(pkt)

    def forward(self):
        moves = []
        for node in self.nodes.values():
            for _ in range(min(SERVICE, len(node.queue))):
                pkt = node.queue.popleft()
                if pkt.ttl <= 0:
                    self.stats["drop_ttl"] += 1
                    continue
                cands = self.next_hops(node, pkt)
                if not cands:
                    self.stats["drop_void"] += 1
                    continue
                nh = None
                for c in cands[:3]:  # if a hop fails after retries, try the next-best neighbour
                    if self.send_hop(node, self.nodes[c]):
                        nh = c
                        break
                    node.neigh[c]["lq"] *= 0.5  # penalise the failed link
                if nh is None:
                    self.stats["drop_link"] += 1
                    continue
                pkt.ttl -= 1
                pkt.hops += 1
                pkt.visited.add(nh)
                pkt.path.append(nh)
                moves.append((nh, pkt))
        for nh, pkt in moves:  # deliver after all nodes transmit (one hop per tick)
            if nh == pkt.dst:
                self.stats["delivered"] += 1
                self.lat.append(self.t - pkt.created + 1)
                self.hops.append(pkt.hops)
                self.paths.append(pkt.path)
            elif len(self.nodes[nh].queue) >= QMAX:
                self.stats["drop_queue"] += 1
            else:
                self.nodes[nh].queue.append(pkt)

    def run(self, ticks=400):
        for _ in range(ticks):
            self.t += 1
            for n in self.nodes.values():
                n.step_motion()
            self.beacons()
            self.generate()
            self.forward()
        return self


def summarize(meshes):
    s = Counter()
    lat, hops = [], []
    for m in meshes:
        s.update(m.stats)
        lat += m.lat
        hops += m.hops
    sent = s["sent"] or 1
    return {
        "pdr": s["delivered"] / sent,
        "hops": sum(hops) / len(hops) if hops else 0,
        "lat": sum(lat) / len(lat) if lat else 0,
        "void": s["drop_void"] / sent, "link": s["drop_link"] / sent,
        "queue": s["drop_queue"] / sent, "ttl": s["drop_ttl"] / sent,
    }


def experiment(seeds=8, ticks=400):
    print(f"{'relays':>6} {'mode':>11} | {'delivered':>9} {'avg hops':>8} {'latency':>7} | "
          f"{'void':>6} {'link':>6} {'queue':>6} {'ttl':>5}")
    print("-" * 80)
    for n in (22, 40, "grid21", "grid18", "grid15"):
        for mode in ("greedy", "greedy_rec", "mida"):
            r = summarize([Mesh(mode, n, seed).run(ticks) for seed in range(seeds)])
            print(f"{str(n):>6} {mode:>11} | {r['pdr']:>8.1%} {r['hops']:>8.2f} {r['lat']:>6.1f}t | "
                  f"{r['void']:>6.1%} {r['link']:>6.1%} {r['queue']:>6.1%} {r['ttl']:>5.1%}")
        print("-" * 80)


def plot(path="mesh_scenario.png", n="grid18", seed=3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m = Mesh("mida", n, seed).run(150)
    fig, ax = plt.subplots(figsize=(10, 6))
    nodes = list(m.nodes.values())
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            p = true_prr(dist(a.pos, b.pos))
            if p > 0.25:
                ax.plot([a.pos[0], b.pos[0]], [a.pos[1], b.pos[1]], color="#bbbbbb", lw=0.5 + 1.5 * p, zorder=1)
    if m.paths:
        # most recent heartbeat from the ground robot, so drawn positions match routing-time positions
        long = next((p for p in reversed(m.paths) if p[0] == "GROUND"), m.paths[-1])
        xs = [m.nodes[k].pos[0] for k in long]
        ys = [m.nodes[k].pos[1] for k in long]
        ax.plot(xs, ys, color="#d9480f", lw=2.5, zorder=2, label=f"packet path ({len(long) - 1} hops)")
    style = {"SUPERVISOR": ("s", "#1c7ed6", 160), "GROUND": ("o", "#2b8a3e", 150), "DRONE": ("^", "#7048e8", 150)}
    for nd in nodes:
        mk, col, sz = style.get(nd.nid, ("o", "#495057", 45))
        ax.scatter(*nd.pos, marker=mk, c=col, s=sz, zorder=3)
        ax.annotate(nd.nid, nd.pos, textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.set_xlim(0, AREA[0]), ax.set_ylim(0, AREA[1]), ax.set_aspect("equal")
    ax.set_title("ORBIT mesh — multi-metric greedy forwarding (positions at t=150)")
    ax.set_xlabel("metres"), ax.set_ylabel("metres"), ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("saved", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    a = ap.parse_args()
    experiment()
    if a.plot:
        plot()
