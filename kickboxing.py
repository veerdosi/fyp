"""Reactive kickboxing with task-space joint targets and simulated balance assistance."""
from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
import time

import mujoco as mj
import numpy as np

from fight import Bout, DECIMATION, DT, HP, RESET, write_json, wrap, yaw_rotation
from skills import ARM, LEG, smooth


@dataclass
class Tactic:
    move: str
    side: int = 0


class Fighter:
    def __init__(self, bout, index, kick_profile):
        self.b = bout
        self.i = index
        self.extended_kick = kick_profile == "extended"
        self.rng = np.random.default_rng(bout.rng.integers(2**32))
        self.r, self.o = bout.robots[index], bout.robots[1-index]
        self.tactic = Tactic("guard")
        self.age = 0
        self.next_choice = 0
        self.move_frames = DURATIONS["guard"]
        self.foot = np.zeros((2, 3))
        self.swing = None
        self.step_side = 0
        self.foot_from = None
        self.foot_to = None
        self.step_age = 0
        self.jac = np.zeros((3, bout.model.nv))
        self.scratch = mj.MjData(bout.model)
        self.face = index * math.pi
        self.target_velocity = np.zeros(2)
        self.height = .773
        self.committed_target = None
        self.exchange = 0
        self.stance = .51 if index == 0 else .56
        self.ready = False
        self.plan = {"pressure": .65 if index == 0 else .52,
                     "kick": .70 if index == 0 else .28,
                     "defense": .25 if index == 0 else .58,
                     "target": "auto", "lead": "auto"}

    def frame(self):
        d = self.b.data
        own = d.xpos[self.r.pelvis]
        rel = d.xpos[self.o.pelvis] - own
        yaw, _ = yaw_rotation(self.b.matrices[self.r.pelvis])
        angle = math.atan2(rel[1], rel[0])
        c, s = math.cos(angle), math.sin(angle)
        basis = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        return own, float(np.linalg.norm(rel[:2])), angle, wrap(angle-yaw), basis

    def choose(self, distance, bearing):
        b = self.b
        towards_me = (b.data.xpos[self.r.pelvis] - b.data.xpos[self.o.pelvis])[:2] / max(distance,.1)
        advancing = b.velocity[self.o.pelvis,:2] @ towards_me
        fists = b.velocity[self.o.hands,:2] @ towards_me
        feet = b.data.xpos[self.o.feet,2]
        threat = distance < .86 and (max(fists) > 1.05 or max(feet) > .31)
        rng = self.rng
        side = int(rng.integers(2))
        if self.plan["lead"] != "auto" and rng.random() < .66:
            side = int(self.plan["lead"] == "right")
        aggression, kicks, defense = (self.plan[x] for x in ("pressure","kick","defense"))
        if distance > .97:
            self.exchange = 0
        if distance > 1.14 or abs(bearing) > .64:
            return Tactic("advance" if self.i == 0 or advancing < .18 else "guard")
        if distance < .36 or (distance < .67 and self.exchange >= (4 if self.i == 0 else 3)):
            self.exchange = 0
            return Tactic("reset", side)
        if self.i == 0:
            if .69 < distance < .92 and rng.random() < .24+.62*kicks:
                return Tactic("front_kick" if rng.random() < .72 else "round_kick", side)
            if distance > .60:
                return Tactic("advance")
            cover = .04+.20*defense
            weights = [.39-cover/2,.44-cover/2,.17,cover] if self.extended_kick else [.35,.39,.17,.09]
            return Tactic(rng.choice(["jab", "cross", "hook", "cover"], p=weights), side)
        if self.tactic.move in ("slip","angle","cover") and distance < .78:
            return Tactic("hook" if distance < .60 else "cross", side)
        if threat and rng.random() < .22+.62*defense:
            return Tactic("slip" if rng.random() < .64 else "angle", side)
        if .69 < distance < .84 and rng.random() < .10+.50*kicks:
            return Tactic("round_kick", side)
        if distance > .58+.12*aggression:
            return Tactic("advance")
        return Tactic(rng.choice(["cross","hook","angle","cover"], p=[.29,.42,.20,.09]), side)

    def duration(self, tactic):
        return DURATIONS[tactic.move]

    def attack_envelope(self, phase):
        return float(smooth((phase-.08)/.32)*(1-smooth((phase-.53)/.38)))

    def attack_phase(self, phase):
        return phase

    def motion(self, move, side, phase, distance, basis):
        forward, left = basis[:2,:2].T
        if move == "advance":
            desired = self.stance - .14*(self.plan["pressure"]-.5)
            return forward*np.clip((distance-desired)*2.65, 0,.82)
        if move == "reset":
            return -forward*np.clip((1.03-distance)*2.5, .10, .87) + left*(.25 if side==0 else -.25)
        if move == "angle":
            return left*(.63 if side==0 else -.63) + forward*np.clip((distance-.58)*1.5,-.20,.32)
        if move in PUNCHES:
            push = .72 if self.i == 0 else .91
            return forward * np.clip((distance-.41)*3.2,-.18,push) * math.sin(math.pi*min(phase+.30,.99))**2
        if move in KICKS:
            return forward * (np.clip((distance-.86)*2.05,-.48,.25) if self.extended_kick
                              else np.clip((distance-.80)*1.8,-.39,.32))
        if move == "slip":
            return (left*(.39 if side==0 else -.39) + forward*.23)*math.sin(math.pi*phase)
        return np.zeros(2)

    def waist(self, move, side, phase):
        strike = math.sin(math.pi*phase)**1.5
        roll = (1 if side==0 else -1)*.30*math.sin(math.pi*phase)**2 if move == "slip" else 0.
        if move in PUNCHES:
            yaw = (1 if side else -1) * (.11 if move=="jab" else .22) * strike
            return yaw, roll, (.15 if self.i == 0 else .21) * strike
        if move in KICKS:
            yaw = (1 if side else -1) * .42 * strike if move == "round_kick" else 0.
            return yaw, roll, -.16 * strike
        return 0., roll, -.025

    def base_height(self, move, phase):
        return .765 if move in KICKS else .789

    def ik_root(self, qpos, angle):
        qpos[self.r.root+2] = self.height
        qpos[self.r.root+3:self.r.root+7] = [math.cos(angle/2),0,0,math.sin(angle/2)]

    def initialize(self):
        d = self.b.data
        self.foot[:] = d.xpos[self.r.feet]
        self.foot[:, 2] = .037

    def solve(self, body, subset, goal, pose, point_offset=None, orientation=None):
        d, m, r = self.scratch, self.b.model, self.r
        self.jac.fill(0)
        rotational = np.zeros_like(self.jac) if orientation is not None else None
        matrix = d.xmat[body].reshape(3,3)
        point = d.xpos[body] if point_offset is None else d.xpos[body] + matrix@point_offset
        mj.mj_jac(m, d, self.jac, rotational, point, body)
        joints = r.v[subset]
        jac = self.jac[:,joints]
        error = goal-point
        if orientation is not None:
            # World rotation vector from the foot's local axes to the requested axes.
            orient = .5*sum(np.cross(matrix[:,j],orientation[:,j]) for j in range(3))
            jac = np.vstack((jac, .27*rotational[:,joints]))
            error = np.r_[error, .27*orient]
        delta = jac.T @ np.linalg.solve(jac@jac.T+.012*np.eye(len(error)),error)
        pose[subset] = np.clip(pose[subset]+np.clip(delta,-.21,.21),
                               r.limits[subset,0]+.025,r.limits[subset,1]-.025)

    def step(self):
        b, d, r = self.b, self.b.data, self.r
        pos, distance, angle, bearing, basis = self.frame()
        if self.ready and b.frame >= self.next_choice:
            tactic = self.choose(distance, bearing)
            self.tactic = tactic
            if tactic.move in ("jab","cross","hook"):
                self.exchange += 1
            self.age = 0
            self.move_frames = self.duration(tactic)
            self.next_choice = b.frame + self.move_frames
            if tactic.move in KICKS:
                self.swing = None
                self.committed_target = None
            return_value = {"turn":b.frame, "fighter":self.i, "move":tactic.move,
                            "side":tactic.side, "plan":self.plan.copy(),
                            "observation":b.perception(self.i)}
        else:
            return_value = None

        move, side = self.tactic.move, self.tactic.side
        phase = self.age / self.move_frames
        self.age += 1
        self.face = angle
        planar = self.motion(move, side, phase, distance, basis)
        self.target_velocity += np.clip(planar-self.target_velocity,-.115,.115)

        foot_goals = self.foot.copy()
        foot_yaws = [angle, angle]
        if move in KICKS:
            self.kick(foot_goals, foot_yaws, side, phase, pos, basis)
        else:
            self.walk(foot_goals, pos, basis)
        planted = self.foot[1-side,:2] if move in KICKS else self.foot[:,:2].mean(axis=0)
        if move in KICKS:
            shift = min(1., math.sin(math.pi*phase)*1.65)
            self.support_correction = (planted-pos[:2])*.82*shift
        else:
            self.support_correction = np.clip((planted-pos[:2])*.70, -.12,.12)

        pose = RESET.copy()
        pose[[0,1,9,10,13,14]] = [-.17,-.17,.36,.36,-.19,-.19]
        self.height = self.base_height(move, phase)
        pose[[2,5,8]] = self.waist(move, side, phase)
        for i in range(2):
            sign = 1 if i == 0 else -1
            pose[ARM[i]] = [-.37 if self.i == 0 else -.60, .51*sign, -.05*sign, -.64]
            if move in PUNCHES and i == side:
                reach = self.attack_envelope(phase)
                pose[ARM[i]] += reach*np.array([-.83,-.22*sign,-.32*sign,1.22])
        hands = self.hand_goals(move, side, phase, pos, basis)
        scratch = self.scratch
        scratch.qpos[:] = d.qpos
        scratch.qpos[r.q] = pose
        self.ik_root(scratch.qpos,angle)
        for _ in range(12):
            mj.mj_kinematics(b.model, scratch)
            mj.mj_comPos(b.model, scratch)
            for i in range(2):
                a = foot_yaws[i]
                co, si = math.cos(a), math.sin(a)
                orientation = np.array([[co,-si,0],[si,co,0],[0,0,1.]])
                striking = move in KICKS and i==side
                self.solve(r.feet[i],LEG[i],foot_goals[i],pose,
                           orientation=None if striking else orientation)
                self.solve(r.hands[i],ARM[i],hands[i],pose,np.array([.095,0,0]))
            scratch.qpos[r.q] = pose
        d.ctrl[r.act] = pose
        return return_value

    def walk(self, goals, pos, basis):
        drift = self.foot[:,:2] - pos[:2]
        travel = np.linalg.norm(self.target_velocity)
        if self.swing is None and (travel > .09 or np.max(np.linalg.norm(drift,axis=1)) > .27):
            if travel > .09:
                self.step_side = int(np.argmin(drift @ self.target_velocity))
            else:
                self.step_side = int(np.argmax(np.linalg.norm(drift,axis=1)))
            side = self.step_side
            center = pos + basis @ np.array([.005 if side==0 else -.045, .142 if side==0 else -.142,0])
            center[:2] += .33*self.target_velocity
            self.foot_from = self.foot[side].copy()
            self.foot_to = np.r_[center[:2], .037]
            self.step_age = 0
            self.swing = side
        if self.swing is not None:
            side = self.swing
            fraction = min(1., self.step_age/9)
            goals[side] = self.foot_from + smooth(fraction)*(self.foot_to-self.foot_from)
            goals[side,2] += .092*math.sin(math.pi*fraction)
            self.step_age += 1
            if fraction == 1.:
                self.foot[side] = self.foot_to
                self.swing = None

    def kick(self, goals, foot_yaws, side, phase, pos, basis):
        move = self.tactic.move
        sign = 1 if side==0 else -1
        if self.committed_target is None:
            self.committed_target = self.foot[side].copy()
        opponent = self.b.data.xpos[self.o.pelvis]
        chamber = pos+basis@np.array([.27,.19*sign,-.24])
        if move == "round_kick":
            chamber = pos+basis@np.array([.16,.37*sign,-.27])
        if self.extended_kick:
            target = opponent + basis@np.array([.065,.025*sign,.22 if move=="front_kick" else .035])
        else:
            target = opponent + basis@np.array([-.035,.02*sign,.23 if move=="front_kick" else -.04])
        rel = basis.T@(target-pos)
        rel[0] = np.clip(rel[0],.66,.735) if self.extended_kick else np.clip(rel[0],.57,.72)
        rel[2] = np.clip(rel[2],-.24,.22)
        target = pos+basis@rel
        lift = float(smooth(phase/.32))
        extend = (smooth((phase-.26)/.21)*(1-smooth((phase-.69)/.16)) if self.extended_kick
                  else smooth((phase-.22)/.24)*(1-smooth((phase-.65)/.18)))
        lower = float(smooth((phase-.75)/.24))
        goal = self.committed_target + lift*(chamber-self.committed_target)
        goal += extend*(target-chamber)
        landing = pos+basis@np.array([.07,.145*sign,0])
        landing[2] = .037
        goal += lower*(landing-goal)
        goals[side] = goal
        if move == "round_kick":
            foot_yaws[side] += -sign*.72*extend
        if phase >= .94:
            self.foot[side] = landing

    def hand_goals(self, move, side, phase, pos, basis):
        goals = np.array([pos+basis@np.array([.24, .113,.32]),
                          pos+basis@np.array([.20,-.113,.31])])
        if self.i == 1:
            goals += basis@np.array([-.015,0,.055])
        if move == "cover":
            goals += basis @ np.array([.015,0,.065])
        if move in ("jab","cross","hook"):
            extend = float(smooth((phase-.08)/.32)*(1-smooth((phase-.53)/.38)))
            r = self.o
            d = self.b.data
            head = self.plan["target"] == "head" or self.plan["target"] == "auto" and move == "jab"
            target = d.xpos[r.head if head else r.torso].copy()
            target[2] += -.056 if head else .105
            target += basis @ np.array([.05,0,0])
            if move == "hook":
                target += basis @ np.array([0,(1 if side==0 else -1)*(.22-.21*extend),0])
            local = basis.T @ (target-pos)
            local[0] = np.clip(local[0],.12,.57)
            target = pos + basis@local
            goals[side] += extend*(target-goals[side])
        return goals

    def assist(self):
        b, r, d = self.b, self.r, self.b.data
        z = d.xpos[r.pelvis,2]
        up = b.matrices[r.pelvis,:,2]
        yaw, _ = yaw_rotation(b.matrices[r.pelvis])
        velocity = d.qvel[r.root_vel:r.root_vel+3]
        angular = d.cvel[r.pelvis,:3]
        force = d.xfrc_applied[r.pelvis]
        weight = b.model.body_subtreemass[r.pelvis]*9.81
        wanted = self.target_velocity+self.support_correction
        force[:2] = np.clip(125*(wanted-velocity[:2]),-100,100)
        force[2] = np.clip(.58*weight+5500*(self.height-z)-300*velocity[2], -80, 1.85*weight)
        up_target = np.array([.015*self.target_velocity[0],.015*self.target_velocity[1],1.])
        force[3:5] = np.clip(470*np.cross(up,up_target)[:2]-42*angular[:2],-160,160)
        force[5] = np.clip(100*wrap(self.face-yaw)-20*angular[2],-85,85)


DURATIONS = {"guard":13,"advance":13,"angle":16,"cover":13,"slip":11,"reset":21,
             "jab":15,"cross":17,"hook":17,"front_kick":27,"round_kick":28,
             "uppercut":16,"overhand":19,"low_kick":24,"side_kick":27,"pull":13,"feint":12}
KICKS = ("front_kick","round_kick","low_kick","side_kick")
PUNCHES = ("jab","cross","hook","uppercut","overhand")


class ImpactMeter:
    """Measure normal impulse from actual MuJoCo contacts during active strikes."""
    def __init__(self, bout, detailed=False):
        self.b = bout
        self.last = {}
        self.geoms = {}
        self.detailed = detailed
        self.guards = []
        for gi in range(bout.model.ngeom):
            name = bout.model.geom(gi).name
            if not name.endswith(("_collision", "_collision_back")):
                continue
            side, label = name.removesuffix("_back").removesuffix("_collision").split("_", 1)
            if label in ("torso", "head"):
                label = "body" if label == "torso" else label
            elif label.endswith("_hand"):
                label = label.replace("_", " ")
            elif "_foot" in label:
                label = label.split("_")[0] + " foot"
            elif detailed and any(part in label for part in ("elbow", "wrist")):
                label = "guard"
            elif detailed and any(part in label for part in ("thigh", "shin")):
                label = label.split("_")[0] + (" thigh" if "thigh" in label else " leg")
            else:
                bi = bout.model.geom_bodyid[gi]
                if bi not in bout.targets or "hip" not in label and "knee" not in label:
                    continue
                label = label.split("_")[0] + (" thigh" if "hip" in label else " leg")
            self.geoms[gi] = (int(side == "foe"), label)

    def sample(self, impacts):
        b = self.b
        for ci in range(b.data.ncon):
            c = b.data.contact[ci]
            pair = [self.geoms.get(c.geom1), self.geoms.get(c.geom2)]
            if None in pair or pair[0][0] == pair[1][0]:
                continue
            force = np.zeros(6)
            mj.mj_contactForce(b.model, b.data, ci, force)
            if force[0] <= 1:
                continue
            for (i, weapon), (_, target) in (pair, pair[::-1]):
                fighter = b.kickboxers[i]
                move = fighter.tactic.move
                kind = "hand" if move in PUNCHES else "foot" if move in KICKS else None
                side = "left" if fighter.tactic.side == 0 else "right"
                phase = fighter.attack_phase((fighter.age-1)/fighter.move_frames)
                if kind is None or weapon != f"{side} {kind}" or not .16 < phase < .80:
                    continue
                guard = self.detailed and (target.endswith(" hand") or target == "guard")
                if target not in ("body", "head") and not guard and (kind == "hand" or not target.endswith((" thigh"," leg"))):
                    continue
                key = (i, weapon, target)
                total, peak, pos = impacts.get(key, (0.,0.,None))
                impacts[key] = (total+force[0]*b.model.opt.timestep,max(peak,force[0]),
                                c.pos.copy() if force[0] > peak else pos)

    def score(self, impacts):
        b = self.b
        for key, (impulse, force, pos) in impacts.items():
            i, weapon, target = key
            action = (i, b.kickboxers[i].next_choice)
            if impulse < 1.25 or force < 60. or action in self.last:
                continue
            if target.endswith(" hand") or target == "guard":
                if not self.guards or self.guards[-1]["attacker"] != i or b.frame/30-self.guards[-1]["t"] > .20:
                    self.guards.append({"t":round(b.frame*DT,4),"attacker":i,"move":b.kickboxers[i].tactic.move})
                continue
            self.last = {k:v for k,v in self.last.items() if b.frame-v < 45}
            self.last[action] = b.frame
            damage = min(950, impulse * 102) * (1.2 if target == "head" else .75 if " " in target else 1.)
            b.damage[i] += damage
            b.hp[1-i] = max(0., b.hp[1-i]-damage)
            event = {"t": round(b.frame*DT,4), "attacker": i, "weapon": weapon, "target": target,
                     "move": b.kickboxers[i].tactic.move, "impulse_ns": round(float(impulse),2),
                     "peak_normal_n": round(float(force),1), "damage_pct": round(damage/HP*100,2),
                     "position": pos.round(4).tolist()}
            if self.detailed:
                event["points"] = round(float(damage),2)
            b.events.append(event)


PLAN_FIELDS = {"pressure", "kick", "defense", "target", "lead"}


def live_plans(b, bridge, turn, log):
    observations = []
    for i, fighter in enumerate(b.kickboxers):
        own = [entry[i] for entry in b.history[-30::7]]
        observations.append({"turn":turn, "t_end":b.limit*DT,
                   "current_plan":fighter.plan, "own_move":fighter.tactic.move,
                   "observation":b.perception(i), "recent_samples":own})
        write_json(bridge/f"observe-{i}.json", observations[-1])
    pending = set(range(2))
    limit = time.monotonic()+180
    while pending:
        for i in tuple(pending):
            path = bridge/f"action-{i}-{turn:03}.json"
            if not path.is_file():
                continue
            plan = json.loads(path.read_text())
            if plan.get("turn") != turn or not PLAN_FIELDS <= set(plan):
                raise ValueError(f"Invalid plan {path}")
            if any(type(plan[k]) not in (int,float) or not 0 <= plan[k] <= 1
                   for k in ("pressure","kick","defense")) or plan["target"] not in ("auto","body","head") or plan["lead"] not in ("auto","left","right"):
                raise ValueError(f"Invalid plan values in {path}")
            b.kickboxers[i].plan = {k:plan[k] for k in sorted(PLAN_FIELDS)}
            pending.remove(i)
        if pending:
            if time.monotonic() >= limit:
                raise TimeoutError(f"Missing live plans for {pending} on turn {turn}")
            time.sleep(.20)
    log.write(json.dumps({"turn":turn, "observations":observations,
                         "plans":[f.plan for f in b.kickboxers]})+"\n")
    log.flush()


def initialize_bout(b):
    for fighter in b.kickboxers:
        r = fighter.r
        # Tune the position servos for these Cartesian targets.
        gain = b.model.actuator_gainprm[r.act,0] * 2.7
        gain[[2,5,8]] *= 2.5
        gain[np.r_[ARM[0],ARM[1]]] *= 2.5
        b.model.actuator_gainprm[r.act,0] = gain
        b.model.actuator_biasprm[r.act,1] = -gain
        b.model.actuator_biasprm[r.act,2] *= 2.1
        b.model.actuator_biasprm[r.act[np.r_[ARM[0],ARM[1]]],2] *= 1.6
        b.data.qpos[r.root+2] = .789
        b.data.qpos[r.q[[0,1,9,10,13,14]]] = [-.15,-.15,.31,.31,-.16,-.16]
    mj.mj_forward(b.model,b.data)
    for fighter in b.kickboxers:
        fighter.initialize()
        fighter.step()
        r = fighter.r
        b.data.qpos[r.q[np.r_[ARM[0],ARM[1]]]] = b.data.ctrl[r.act[np.r_[ARM[0],ARM[1]]]]
        fighter.ready = True
        fighter.next_choice = 0
        fighter.age = 0
    mj.mj_forward(b.model,b.data)
    b.poses.clear()
    b.camera_state.clear()
    b.history.clear()
    b.capture()


def physics_step(b, meter):
    b.moves = tuple(f.tactic.move for f in b.kickboxers)
    touching = {}
    for _ in range(DECIMATION):
        mj.mj_step1(b.model,b.data)
        for fighter in b.kickboxers:
            fighter.assist()
        mj.mj_step2(b.model,b.data)
        meter.sample(touching)
    mj.mj_forward(b.model,b.data)
    b.frame += 1
    if not np.isfinite(b.data.qpos).all() or abs(b.data.time-b.frame*DT) > .02:
        raise RuntimeError(f"Unstable simulation at frame {b.frame}")
    b.update_velocity()
    meter.score(touching)
    b.capture()


def run(output, seed, seconds, bridge=None, interval=3., model_name=None, kick_profile="extended"):
    output.mkdir(parents=True, exist_ok=False)
    b = Bout(seed, 1.24, seconds, output, endurance=True, load_policy=False)
    b.kickboxers = [Fighter(b, i, kick_profile) for i in range(2)]
    meter = ImpactMeter(b)
    initialize_bout(b)
    write_json(output/"settings.json", {"seconds":seconds,"agents":0,"endurance":True,
                                       "controllers":["Pressure","Counter"],"seed":seed,
                                       "kick_profile":kick_profile,"plan_interval":interval if bridge else None,
                                       "tactical_model":(model_name or "external") if bridge else "local feedback"})
    every = round(interval/DT)
    with (output/"decisions.jsonl").open("w") as log, (output/"plans.jsonl").open("w") as plan_log:
        while not b.status():
            if bridge and b.frame % every == 0:
                live_plans(b,bridge,b.frame//every,plan_log)
            for fighter in b.kickboxers:
                decision = fighter.step()
                if decision is not None:
                    log.write(json.dumps(decision)+"\n")
            physics_step(b, meter)
    b.save()
    if bridge:
        write_json(bridge/"complete.json", b.status())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--seed",type=int,default=23)
    parser.add_argument("--seconds",type=float,default=27)
    parser.add_argument("--bridge",type=Path)
    parser.add_argument("--interval",type=float,default=3.)
    parser.add_argument("--model-name", help="Record the external tactical model in the run metadata")
    parser.add_argument("--kick-profile", choices=("extended","compact"), default="extended")
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not math.isfinite(args.interval) or min(args.seconds,args.interval) < DT:
        parser.error("Seconds and interval must be at least one control step (1/30 s)")
    if args.bridge:
        args.bridge.mkdir(parents=True, exist_ok=False)
    run(args.output,args.seed,args.seconds,args.bridge,args.interval,args.model_name,args.kick_profile)
