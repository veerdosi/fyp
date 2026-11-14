"""Run a live, two-player MuJoCo bout with independent tactical command slots.

The 194-float GGSD observation layout and exported policy math follow the
authors' BSD-3-Clause web player (js/game/sim.js, policy.js and registry.js).
"""
import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

import mujoco as mj
import numpy as np

from arena import make_arena
from fetch_assets import ROOT, RUNS

SIDES = ("me", "foe")
FIGHTERS = ("teal", "amber")
DT = 1 / 30
DECIMATION = 16
HP = 25000
SKILLS = ("turn_right", "advance", "turn_left", "punch", "power", "pull")
JOINTS = (
    "left_hip_pitch", "right_hip_pitch", "waist_yaw",
    "left_hip_roll", "right_hip_roll", "waist_roll",
    "left_hip_yaw", "right_hip_yaw", "waist_pitch",
    "left_knee", "right_knee", "left_shoulder_pitch", "right_shoulder_pitch",
    "left_ankle_pitch", "right_ankle_pitch", "left_shoulder_roll", "right_shoulder_roll",
    "left_ankle_roll", "right_ankle_roll", "left_shoulder_yaw", "right_shoulder_yaw",
    "left_elbow", "right_elbow",
)
RESET = np.zeros(23)
RESET[[15, 16, 21, 22]] = [.25, -.25, 1.57, 1.57]
EXTENDED = ("jab", "cross", "hook", "slip_left", "slip_right", "low_kick", "front_kick",
            "knee", "push", "cover", "feint", "custom", "close", "angle_left", "angle_right")
MOVES = SKILLS + EXTENDED + ("auto",)


class Policy:
    def __init__(self, run):
        path = ROOT / "exports/g1_boxing/ckpts" / run
        meta = json.loads((path / "policy.json").read_text())
        weights = np.fromfile(path / "weights.bin", dtype="<f4")
        tensors = {t["name"]: weights[t["offset"]//4:t["offset"]//4+t["count"]].reshape(t["shape"])
                   for t in meta["tensors"]}
        self.stacks = {
            key: [(tensors[f"{key}_w{i}"], tensors[f"{key}_b{i}"]) for i in range(meta[setting])]
            for key, setting in (("hl", "num_high_level_layers"), ("ll", "num_low_level_layers"))
        }
        self.codes = np.eye(meta["num_skills"], dtype=np.float32)

    def predict(self, vector, key):
        vector = np.asarray(vector, dtype=np.float32)
        for i, (weight, bias) in enumerate(self.stacks[key]):
            vector = weight @ vector + bias
            if i < len(self.stacks[key]) - 1:
                negative = vector < 0
                vector[negative] = np.expm1(vector[negative])
        return vector

    def action(self, observation, code):
        return np.tanh(self.predict(np.r_[observation[2:88], code], "ll"))


@dataclass
class Robot:
    root: int
    root_vel: int
    pelvis: int
    torso: int
    head: int
    hands: np.ndarray
    feet: np.ndarray
    knees: np.ndarray
    leg_targets: np.ndarray
    arms: list
    arm_weights: list
    joints: np.ndarray
    q: np.ndarray
    v: np.ndarray
    act: np.ndarray
    limits: np.ndarray
    scale: np.ndarray

    @classmethod
    def build(cls, model, side):
        def body(link):
            return model.body(f"{side}_{link}_link").id

        joints = np.array([model.joint(f"{side}_{name}_joint").id for name in JOINTS])
        root_joint = model.joint(f"{side}_root")
        limbs = ("left", "right")
        arm_links = ("shoulder_yaw", "elbow", "wrist_roll", "wrist_pitch", "wrist_yaw", "wrist_yaw_back")
        arms = [[body(f"{limb}_{link}") for link in arm_links] for limb in limbs]
        weights = [model.body_mass[arm] / sum(model.body_mass[arm]) for arm in arms]
        limits = model.jnt_range[joints]
        return cls(int(root_joint.qposadr[0]), int(root_joint.dofadr[0]), model.body(side + "_pelvis").id,
                   body("torso"), body("head"),
                   np.array([body(f"{limb}_wrist_yaw") for limb in limbs]),
                   np.array([body(f"{limb}_ankle_roll") for limb in limbs]),
                   np.array([body(f"{limb}_knee") for limb in limbs]),
                   np.array([body(f"{limb}_{link}") for limb in limbs for link in ("hip_yaw", "knee")]),
                   arms, weights, joints, model.jnt_qposadr[joints], model.jnt_dofadr[joints],
                   np.array([model.actuator(f"{side}_{name}_joint").id for name in JOINTS]),
                   limits, 1.4 * np.max(np.abs(limits), axis=1))


def wrap(angle):
    return (angle + np.pi) % (2*np.pi) - np.pi


def yaw_rotation(matrix):
    yaw = math.atan2(matrix[1, 0], matrix[0, 0])
    c, s = math.cos(yaw), math.sin(yaw)
    return yaw, np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


class Bout:
    def __init__(self, seed, opening, seconds, output, endurance=False, assisted_getup=True,
                 physics_recovery=False, load_policy=True):
        self.model = mj.MjModel.from_xml_string(make_arena())
        self.data = mj.MjData(self.model)
        self.robots = [Robot.build(self.model, side) for side in SIDES]
        self.policies = [Policy(run) for run in RUNS] if load_policy else []
        self.rng = np.random.default_rng(seed)
        self.output = output
        self.endurance = endurance
        self.assisted_getup = assisted_getup
        self.physics_recovery = physics_recovery
        self.damage = np.zeros(2)
        self.hp = np.full(2, float(HP))
        self.last_action = np.zeros((2, 23))
        self.frame = 0
        self.limit = round(seconds / DT)
        self.fall_frames = np.zeros(2, dtype=int)
        self.recovery = np.zeros(2, dtype=int)
        self.heading_targets = [None, None]
        self.previous_speed = np.zeros((2, 6, 6))
        self.contact_frame = defaultdict(lambda: -100)
        self.events = []
        self.records = []
        self.poses = []
        self.camera_state = []
        self.history = []
        self.moves = ("auto", "auto")
        self.velocity = np.zeros((self.model.nbody, 3))
        self.weapon_type = {}
        self.targets = {}
        for i, robot in enumerate(self.robots):
            for b in (*robot.hands, *robot.feet, *robot.knees):
                self.weapon_type[int(b)] = i
            for b in (robot.torso, robot.head, *robot.leg_targets):
                self.targets[int(b)] = i
        for i, (robot, x, yaw) in enumerate(zip(self.robots, [-opening/2, opening/2], [0, math.pi])):
            self.data.qpos[robot.root:robot.root+7] = [
                x, (-1)**i * .015, 1., math.cos(yaw/2), 0, 0, math.sin(yaw/2)
            ]
            self.data.qpos[robot.q] = RESET
        mj.mj_forward(self.model, self.data)
        self.capture()

    @property
    def matrices(self):
        return self.data.xmat.reshape(-1, 3, 3)

    def update_velocity(self):
        d, m = self.data, self.model
        self.velocity[:] = d.cvel[:, 3:] + np.cross(
            d.cvel[:, :3], d.xipos - d.subtree_com[m.body_rootid]
        )

    def proprioception(self, index):
        r, d = self.robots[index], self.data
        pos = d.xpos[r.pelvis]
        rotation = self.matrices[r.pelvis]
        yaw, heading = yaw_rotation(rotation)
        lin = self.velocity[r.pelvis] @ rotation
        angular = d.qvel[r.root_vel+3:r.root_vel+6]
        gravity = -rotation[2]
        hands = (d.xpos[r.hands] - pos) @ heading.T
        hands[:, 2] = d.xpos[r.hands, 2]
        return np.r_[pos[:2], yaw, pos[2], lin, angular, gravity, hands.ravel(),
                     d.qpos[r.q], .2*d.qvel[r.v], self.last_action[index]]

    def observation(self, index):
        own, opp = self.robots[index], self.robots[1-index]
        d = self.data
        _, heading = yaw_rotation(self.matrices[own.pelvis])
        torso = self.matrices[own.torso]
        relative = heading @ (d.xpos[opp.pelvis] - d.xpos[own.pelvis])
        hands = (d.xpos[opp.hands] - d.xpos[own.torso]) @ torso
        velocities = (self.velocity[opp.hands] - self.velocity[own.torso]) @ torso
        return np.r_[self.proprioception(index), relative, hands.ravel(), velocities.ravel(),
                     self.proprioception(1-index), self.hp[[index, 1-index]]/HP,
                     max(0., 1 - self.frame/self.limit)]

    def perception(self, index):
        own, opp = self.robots[index], self.robots[1-index]
        d = self.data
        yaw, heading = yaw_rotation(self.matrices[own.pelvis])
        enemy_yaw, _ = yaw_rotation(self.matrices[opp.pelvis])
        rel = heading @ (d.xpos[opp.pelvis] - d.xpos[own.pelvis])
        velocity = heading @ (self.velocity[opp.pelvis] - self.velocity[own.pelvis])
        limb_ids = np.r_[opp.hands, opp.feet]
        limbs = (d.xpos[limb_ids] - d.xpos[own.torso]) @ heading.T
        limb_vel = (self.velocity[limb_ids] - self.velocity[own.torso]) @ heading.T
        own_limbs = (d.xpos[np.r_[own.hands, own.feet]] - d.xpos[own.pelvis]) @ heading.T
        nearest_edge = 5 - float(np.abs(d.xpos[own.pelvis, :2]).max())
        return {
            "t": round(self.frame*DT, 3),
            "distance_m": round(float(np.linalg.norm(rel[:2])), 3),
            "opponent_bearing_deg": round(math.degrees(math.atan2(rel[1], rel[0]))),
            "opponent_facing_error_deg": round(math.degrees(wrap(yaw + math.atan2(rel[1],rel[0]) + np.pi - enemy_yaw))),
            "opponent_relative_pelvis_m": rel.round(3).tolist(),
            "opponent_relative_velocity_mps": velocity.round(2).tolist(),
            "opponent_limbs_relative_to_own_chest_m": limbs.round(2).tolist(),
            "opponent_limbs_relative_velocity_mps": limb_vel.round(2).tolist(),
            "own_limbs_relative_to_own_pelvis_m": own_limbs.round(2).tolist(),
            "own_torso_up": round(float(self.matrices[own.torso, 2, 2]), 2),
            "opponent_torso_up": round(float(self.matrices[opp.torso, 2, 2]), 2),
            "own_pelvis_height_m": round(float(d.xpos[own.pelvis, 2]), 2),
            "opponent_pelvis_height_m": round(float(d.xpos[opp.pelvis, 2]), 2),
            "own_margin_to_edge_m": round(nearest_edge, 2),
            "own_health_pct": round(100*self.hp[index]/HP, 1),
            "own_damage_points": round(float(self.damage[index]), 1),
            "opponent_health_pct": round(100*self.hp[1-index]/HP, 1),
            "opponent_damage_points": round(float(self.damage[1-index]), 1),
            "recent_impacts": [
                {"t": e["t"], "by": "self" if e["attacker"] == index else "opponent",
                 "weapon": e["weapon"], "target": e["target"], "damage_pct": e["damage_pct"]}
                for e in self.events[-8:] if self.frame*DT-e["t"] < 1.5
            ],
        }

    def score_contacts(self, touching):
        d = self.data
        for i, (attacker, defender) in enumerate(zip(self.robots, self.robots[::-1])):
            arms = [np.average(self.velocity[ids], axis=0, weights=weights)
                    for ids, weights in zip(attacker.arms, attacker.arm_weights)]
            strike = np.array([*arms, *self.velocity[attacker.feet], *self.velocity[attacker.knees]])
            for j, weapon in enumerate([*attacker.hands, *attacker.feet, *attacker.knees]):
                for k, target in enumerate((defender.torso, defender.head, *defender.leg_targets)):
                    if (j < 2 and k > 1) or (j > 1 and k > 1 and self.moves[i] not in ("low_kick", "front_kick", "knee", "custom")):
                        continue
                    if j < 2:
                        closing = -(strike[j]-self.velocity[target]) @ self.matrices[target, :, 0]
                    else:
                        direction = d.xpos[target] - d.xpos[weapon]
                        closing = (strike[j]-self.velocity[target]) @ direction / max(.03, np.linalg.norm(direction))
                    speed = min(12., max(closing, self.previous_speed[i, j, k]))
                    self.previous_speed[i, j, k] = max(0., closing)
                    key = (int(weapon), int(target))
                    if speed < (.65 if j > 1 else .35) or key not in touching or self.frame - self.contact_frame[key] < 4:
                        continue
                    force, pos = touching[key]
                    if force < 10:
                        continue
                    damage = speed**2 * 150 * (1.5 if k == 1 else .65 if k > 1 else 1)
                    self.damage[i] += damage
                    self.hp[1-i] = max(0., self.hp[1-i] - damage)
                    self.contact_frame[key] = self.frame
                    self.events.append({"t": round(self.frame*DT, 4), "attacker": i,
                                        "weapon": ("left hand", "right hand", "left foot", "right foot", "left knee", "right knee")[j],
                                        "target": ("body", "head", "left thigh", "left leg", "right thigh", "right leg")[k], "closing_mps": round(float(speed), 2),
                                        "peak_normal_n": round(float(force), 1),
                                        "damage_pct": round(float(damage)/HP*100, 2),
                                        "position": pos.round(4).tolist()})

    def sample_contacts(self, touching):
        d = self.data
        for index in range(d.ncon):
            c = d.contact[index]
            ids = self.model.geom_bodyid[[c.geom1, c.geom2]]
            for a, b in (ids, ids[::-1]):
                if a not in self.weapon_type or b not in self.targets:
                    continue
                if self.weapon_type[a] == self.targets[b]:
                    continue
                force = np.zeros(6)
                mj.mj_contactForce(self.model, d, index, force)
                if (a,b) not in touching or force[0] > touching[a,b][0]:
                    touching[a,b] = (force[0], c.pos.copy())

    def capture(self):
        self.poses.append(self.data.qpos.copy())
        self.camera_state.append([self.frame*DT, *self.hp, *self.damage])
        self.history.append([self.perception(i) for i in range(2)])

    def status(self):
        fallen = (self.fall_frames >= 5).tolist()
        out = [np.abs(self.data.xpos[r.pelvis, :2]).max() > 5 for r in self.robots]
        loss = [fell or edge or hp <= 0 for fell, edge, hp in zip(fallen, out, self.hp)]
        if self.endurance:
            loss = [False, False]
            fallen = out = [False, False]
        if not any(loss) and self.frame < self.limit:
            return None
        winner = ("draw" if all(loss) else FIGHTERS[1-loss.index(True)]) if any(loss) else (
            "draw" if abs(self.damage[0]-self.damage[1]) < 1 else FIGHTERS[int(self.damage[1] > self.damage[0])]
        )
        return {"winner": winner, "reason": ("knockdown" if any(fallen) else "ring-out" if any(out)
                                             else "health depleted" if any(loss) else "time"),
                "seconds": round(self.frame*DT, 3), "health_pct": (100*self.hp/HP).round(2).tolist(),
                "impacts": len(self.events), "damage_points": self.damage.round(1).tolist()}

    def balance_assist(self):
        """Use identical simulated recovery assistance on both fighters."""
        for index, r in enumerate(self.robots):
            other = self.robots[1-index]
            rotation = self.matrices[r.pelvis]
            up = rotation[:, 2]
            z = self.data.xpos[r.pelvis, 2]
            v = self.data.qvel[r.root_vel:r.root_vel+6]
            angular = rotation @ v[3:]
            tipping = np.clip((.90-up[2])/.32, 0., 1.)
            low = np.clip((.66-z)/.22, 0., 1.)
            weight = self.model.body_subtreemass[r.pelvis]*9.81
            force = self.data.xfrc_applied[r.pelvis]
            force[:2] = -35*low*v[:2]
            force[2] = np.clip(2100*(.61-z)-155*v[2], 0, 1.18*weight)*low
            tilt = np.cross(up, [0., 0., 1.])
            force[3:5] = np.clip((115*tilt[:2]-22*angular[:2])*max(tipping, low), -90., 90.)
            xy = self.data.xpos[r.pelvis, :2]
            over = np.clip(np.abs(xy)-3.9, 0, .9)
            force[:2] -= 95 * np.sign(xy) * over
            if not self.assisted_getup:
                continue
            if (self.fall_frames[index] >= 5 or up[2] < .30) and not self.recovery[index]:
                self.recovery[index] = 25
            if not self.recovery[index]:
                continue

            age = 25-self.recovery[index]
            effort = min(1., (age+1)/4, self.recovery[index]/6)
            self.recovery[index] -= 1
            lift = np.clip(weight + 2800*(.74-z)-235*v[2], 0, 2.5*weight)
            force[2] += effort*(lift-force[2])
            # The small fixed tilt term selects a roll direction if fully upside down.
            torque = 315*tilt[:2] + np.array([22., 0.])*(up[2] < -.7) - 51*angular[:2]
            force[3:5] += effort*(np.clip(torque, -170, 170)-force[3:5])
            away = xy-self.data.xpos[other.pelvis, :2]
            distance = np.linalg.norm(away)
            force[:2] += effort*(160*away/max(.1,distance)*np.clip(1-distance/.74, 0, 1)-80*v[:2])
            upright = RESET.copy()
            upright[[0, 1, 9, 10, 13, 14]] = [-.20, -.20, .43, .43, -.23, -.23]
            self.data.ctrl[r.act] += .80*effort*(upright-self.data.ctrl[r.act])

    def advance(self, commands, frames):
        from skills import MotorSkill

        motors = [MotorSkill(self, i, command) for i, command in enumerate(commands)]
        started = [None, None]
        names = [command["move"] for command in commands]
        for tick in range(frames):
            for i, command in enumerate(commands):
                follow = command.get("follow")
                if follow is None or started[i] is not None:
                    continue
                trigger = command.get("trigger", "mid")
                rel = self.data.xpos[self.robots[1-i].pelvis] - self.data.xpos[self.robots[i].pelvis]
                distance = np.linalg.norm(rel[:2])
                if tick >= frames//2 and (trigger == "mid" or
                        trigger == "in_range" and distance < .72 or
                        trigger == "separated" and distance > .68):
                    started[i] = tick
                    motors[i] = MotorSkill(self, i, {"turn": command["turn"]} | follow)
                    names[i] = follow["move"]
            self.moves = tuple(names)
            for i, (robot, motor) in enumerate(zip(self.robots, motors)):
                obs = self.observation(i)
                start = started[i] or 0
                action = motor.act(obs, tick-start, frames-start)
                self.heading_targets[i] = motor.heading_offset
                self.data.ctrl[robot.act] = robot.scale * np.clip(action, -1, 1)
            for i, robot in enumerate(self.robots):
                self.last_action[i] = self.data.ctrl[robot.act] / robot.scale
            touching = {}
            if self.endurance and not self.physics_recovery:
                self.balance_assist()
            for _ in range(DECIMATION):
                if self.endurance and self.physics_recovery:
                    mj.mj_step1(self.model, self.data)
                    self.recovery_forces()
                    mj.mj_step2(self.model, self.data)
                else:
                    mj.mj_step(self.model, self.data)
                self.sample_contacts(touching)
            mj.mj_forward(self.model, self.data)
            self.frame += 1
            self.update_velocity()
            low = np.array([self.data.xpos[r.torso, 2] < .50 for r in self.robots])
            self.fall_frames = np.where(low, self.fall_frames+1, 0)
            self.score_contacts(touching)
            self.capture()
            if self.status():
                break

    def recovery_forces(self):
        """Apply damped recovery using the current orientation at each physics step."""
        for index, r in enumerate(self.robots):
            up = self.matrices[r.pelvis, :, 2]
            x, y, height = self.data.xpos[r.pelvis]
            speed = self.data.qvel[r.root_vel:r.root_vel+3]
            angular = self.data.cvel[r.pelvis, :3]
            tilt = np.cross(up, (0, 0, 1))
            tilt_norm = np.linalg.norm(tilt)
            tilt_angle = np.arctan2(tilt_norm, up[2])
            axis = tilt / max(tilt_norm, .01)
            if tilt_norm < .01 and up[2] < 0:
                axis = np.array([1., 0., 0.])
            weight = self.model.body_subtreemass[r.pelvis] * 9.81
            force = self.data.xfrc_applied[r.pelvis]
            force[:] = 0
            if height < .52 or up[2] < .52:
                self.recovery[index] = 100
            recovering = self.recovery[index] > 0
            if recovering:
                self.recovery[index] -= 1
                force[:2] = -55 * speed[:2]
                force[2] = np.clip(weight + 1500*(.73-height) - 130*speed[2], 0, 1.8*weight)
                force[3:] = np.clip(65*tilt_angle*axis - 18*angular, -90, 90)
                # Tuck the legs to clear the mat, then extend them below the pelvis.
                pose = RESET.copy()
                bend = .55 + .43 * (up[2] < .7)
                pose[[0, 1, 9, 10, 13, 14]] = [-.48*bend, -.48*bend, bend, bend, -.52*bend, -.52*bend]
                self.data.ctrl[r.act] = pose
            else:
                low = np.clip((.65-height)/.18, 0, 1)
                tipping = np.clip((.9-up[2])/.38, 0, 1)
                force[2] = np.clip(1500*(.60-height)-110*speed[2], 0, weight)*low
                force[3:5] = np.clip((85*tilt[:2]-11*angular[:2])*tipping, -55, 55)
            xy = np.array([x, y])
            force[:2] -= 95*np.sign(xy)*np.clip(np.abs(xy)-3.9, 0, .9)
            offset = self.heading_targets[index]
            if offset is not None and not recovering:
                other = self.robots[1-index]
                delta = self.data.xpos[other.pelvis, :2] - xy
                yaw, _ = yaw_rotation(self.matrices[r.pelvis])
                error = wrap(np.arctan2(delta[1], delta[0]) + offset - yaw)
                force[5] = np.clip(17*error - 5*angular[2], -20, 20)

    def dispatch(self, index, turn):
        document = {
            "episode": self.output.name, "turn": turn, "fighter": FIGHTERS[index],
            "observation": self.perception(index),
            "previous_samples": [self.history[n][index] for n in (max(0,self.frame-9), max(0,self.frame-4))
                                 if self.frame and n < self.frame],
            "own_last_move": self.moves[index] if turn else None,
        }
        write_json(self.output / f"observe-{index}.json", document)
        return document

    def save(self):
        np.savez_compressed(self.output / "states.npz", qpos=np.array(self.poses),
                            timeline=np.array(self.camera_state))
        write_json(self.output / "impacts.json", self.events)
        write_json(self.output / "result.json", self.status())
        print(json.dumps(self.status()), flush=True)


def write_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2)+"\n")
    tmp.replace(path)


def validate(command, turn):
    if command.get("turn") != turn or command.get("move") not in MOVES:
        raise ValueError(f"Invalid turn or move in {command}")
    for key, allowed in {
        "side": ("left", "right"), "target": ("body", "head", "lead_leg"),
        "base": SKILLS, "limb": ("hand", "foot", "knee"),
    }.items():
        if key in command and command[key] not in allowed:
            raise ValueError(f"Invalid {key}")
    for key, lo, hi in (("power", .35, 1.), ("arc", -1., 1.), ("delay", 0., .45)):
        if key in command and not (type(command[key]) in (float, int) and lo <= command[key] <= hi):
            raise ValueError(f"Invalid {key}")
    if "track" in command and type(command["track"]) is not bool:
        raise ValueError("track must be a boolean")
    if "follow" in command:
        follow = command["follow"]
        if not isinstance(follow, dict) or "follow" in follow or "turn" in follow:
            raise ValueError("follow must contain a single move without a turn")
        if command.get("trigger", "mid") not in ("mid", "in_range", "separated"):
            raise ValueError("Invalid follow trigger")
        validate({"turn": turn} | follow, turn)
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--opening", type=float, default=1.8)
    parser.add_argument("--window", type=int, default=12)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--agents", type=int, choices=(0, 1, 2), default=2)
    parser.add_argument("--agent-effort", choices=("low", "medium"), default="medium")
    parser.add_argument("--endurance", action="store_true", help="Timed rounds with equal balance and recovery assistance")
    parser.add_argument("--physics-recovery", action="store_true",
                        help="Update balance and recovery forces every physics substep")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--replay", type=Path, help="Use the recorded decisions from a completed bout")
    mode.add_argument("--resume", action="store_true", help="Continue an interrupted live bout")
    parser.add_argument("--pilot", help="Comma-delimited paired moves, e.g. advance/auto,front_kick/auto")
    args = parser.parse_args()
    args.assisted_getup = True
    replay = []
    source = args.output if args.resume else args.replay
    if source:
        settings = json.loads((source / "settings.json").read_text())
        for setting in ("opening", "seed", "window", "seconds", "agents"):
            setattr(args, setting, settings[setting])
        args.endurance = settings.get("endurance", False)
        args.assisted_getup = settings.get("assisted_getup", True)
        args.physics_recovery = settings.get("physics_recovery", False)
        args.agent_effort = settings.get("agent_effort", "medium")
        replay = [json.loads(line) for line in (source / "decisions.jsonl").read_text().splitlines()]
    if args.resume:
        if (args.output / "result.json").exists() or settings.get("replay"):
            parser.error("--resume requires an interrupted live bout")
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        write_json(args.output / "settings.json", vars(args) | {
            "output": str(args.output), "replay": str(args.replay) if args.replay else None,
        })
    bout = Bout(args.seed, args.opening, args.seconds, args.output, args.endurance,
                args.assisted_getup, args.physics_recovery)
    pilot = [pair.split("/") for pair in args.pilot.split(",")] if args.pilot else []
    turn = 0
    if args.resume:
        for row in replay:
            if row["turn"] != turn or any(
                bout.perception(i) != obs["observation"] for i, obs in enumerate(row["observations"])
            ):
                raise RuntimeError(f"Reconstructed state differs at turn {turn}")
            bout.advance([validate(command, turn) for command in row["commands"]], args.window)
            turn += 1
        replay = []
    with (args.output / "decisions.jsonl").open("a" if args.resume else "w", buffering=1) as decisions:
        while not bout.status():
            obs = [bout.dispatch(i, turn) for i in range(2)]
            if pilot and turn < len(pilot):
                commands = [{"turn": turn, "move": move, "side": "left"} for move in pilot[turn]]
            else:
                commands = [{"turn": turn, "move": "auto"} for _ in range(2)]
            if replay:
                commands = replay[turn]["commands"]
            for i in range(0 if replay else args.agents):
                path = args.output / f"action-{i}-{turn:03d}.json"
                while not path.exists():
                    time.sleep(.08)
                commands[i] = json.loads(path.read_text())
            commands = [validate(command, turn) for command in commands]
            decisions.write(json.dumps({"turn": turn, "observations": obs, "commands": commands,
                                        "policy": [f"gpt-6-astra/{args.agent_effort}" if i < args.agents else
                                                   "GGSD" if command["move"] == "auto" else "pilot"
                                                   for i, command in enumerate(commands)]})+"\n")
            bout.advance(commands, args.window)
            turn += 1
    bout.save()


if __name__ == "__main__":
    main()
