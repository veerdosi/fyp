"""Live exchange commands for the MuJoCo G1 kickboxing controller."""
import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import time

import numpy as np

from fight import Bout, DT, write_json
from kickboxing import DURATIONS, KICKS, PUNCHES, Fighter, ImpactMeter, initialize_bout, physics_step
from skills import smooth


@dataclass(frozen=True)
class Move:
    move: str = "guard"
    side: int = 0
    target: str = "body"
    pace: float = 1.
    delay: float = 0.
    power: float = .85
    travel: float = 1.


SIDE = {"left": 0, "right": 1}
TRIGGERS = {"always", "close", "kick_range", "incoming", "landed", "blocked", "missed"}
PUNCH_SHAPES = {
    "jab": (.08, .24, .41, .42),
    "cross": (.12, .29, .52, .43),
    "hook": (.18, .26, .50, .43),
    "uppercut": (.19, .27, .48, .42),
    "overhand": (.22, .29, .57, .38),
    "feint": (.08, .24, .33, .37),
}


def parse_move(value):
    if not isinstance(value, dict) or not isinstance(value.get("move"),str) or value["move"] not in DURATIONS:
        raise ValueError("Choose a move from the supported list")
    side = value.get("side", "left")
    target = value.get("target", "lead_leg" if value["move"] == "low_kick" else "body")
    if not isinstance(side,str) or not isinstance(target,str) or side not in SIDE or target not in {"head", "body", "lead_leg"}:
        raise ValueError("Invalid side or target")
    defaults = {"pace": (1., .72, 1.32), "power": (.85, .45, 1.15),
                "delay": (0., 0., .26), "travel": (1., 0., 1.35)}
    params = {}
    for key, (default, low, high) in defaults.items():
        number = value.get(key, default)
        if type(number) not in (int, float) or not low <= number <= high:
            raise ValueError(f"{key} must be within {low}–{high}")
        params[key] = number
    return Move(value["move"], SIDE[side], target, **params)


def parse_exchange(value, turn):
    if not isinstance(value, dict) or type(value.get("turn")) is not int or value["turn"] != turn:
        raise ValueError("Turn does not match the observation")
    opening = parse_move(value)
    follow_up = value.get("follow")
    trigger = value.get("when", "always")
    if not isinstance(trigger,str) or trigger not in TRIGGERS:
        raise ValueError("Invalid follow-up trigger")
    return opening, parse_move(follow_up) if follow_up is not None else None, trigger


class ExchangeFighter(Fighter):
    def __init__(self, bout, index):
        super().__init__(bout, index, "extended")
        self.tactic = Move()
        self.follow = None
        self.trigger = "always"
        self.opened_at = 0
        self.has_choice = False
        self.sequence = []
        self.recoil_until = 0

    def duration(self, tactic):
        return round(DURATIONS[tactic.move]*tactic.pace + tactic.delay/DT)

    def begin(self, command):
        opening, self.follow, self.trigger = command
        self.opened_at = self.b.frame
        self.queue(opening, "opening")
        self.has_choice = True

    def queue(self, move, source):
        self.queued = move
        self.next_choice = self.b.frame
        self.sequence.append({"t":round(self.b.frame*DT,3), "source":source, **asdict(move)})

    def choose(self, distance, bearing):
        return self.queued

    def attack_phase(self, phase):
        delay = self.tactic.delay/(self.move_frames*DT)
        return float(np.clip((phase-delay)/(1-delay),0.,1.))

    def attack_envelope(self, phase):
        p = self.attack_phase(phase)
        move = self.tactic.move
        onset, rise, peak, recoil = PUNCH_SHAPES.get(move, (.08,.32,.53,.38))
        return float(smooth((p-onset)/rise)*(1-smooth((p-peak)/recoil)))

    def motion(self, move, side, phase, distance, basis):
        forward, left = basis[:2,:2].T
        sign = 1 if side == 0 else -1
        travel = self.tactic.travel
        if move == "advance":
            return forward*np.clip((distance-(.49 if self.i == 0 else .56))*3.5, 0,.96)*travel
        if move == "reset":
            return (-forward*np.clip((1.02-distance)*2.8,.08,.84) + left*.20*sign)*travel
        if move == "angle":
            return (left*.66*sign + forward*np.clip((distance-.66)*1.3,-.16,.28))*travel
        if move == "pull":
            return -forward*.54*math.sin(math.pi*phase)*travel
        if move == "slip":
            return (left*.55*sign + forward*.15)*math.sin(math.pi*phase)*travel
        if move in PUNCHES:
            speed = np.clip((distance-.38)*3.4,-.26,.87)
            if self.tactic.target == "head":
                speed = np.clip((distance-.34)*4.1,-.24,.98)
            pivot = .17*sign if move in {"hook","overhand"} else 0.
            return (forward*speed + left*pivot)*math.sin(math.pi*min(self.attack_phase(phase)+.24,.99))**2*travel
        if move in KICKS:
            range_target = .86 if move in {"front_kick","side_kick"} else .73
            speed = np.clip((distance-range_target)*2.45,-.48,.49)
            pivot = -.19*sign if move in {"low_kick","round_kick"} else .03*sign
            return (forward*speed + left*pivot*math.sin(math.pi*self.attack_phase(phase)))*travel
        if move == "feint":
            return forward*.33*self.attack_envelope(phase)*travel
        return super().motion(move, side, phase, distance, basis)

    def base_height(self, move, phase):
        if move in {"slip","uppercut"} and phase < .5:
            return .789-.064*math.sin(2*math.pi*phase)**2
        return super().base_height(move, phase)

    def ik_root(self, qpos, angle):
        root = self.r.root
        measured = qpos[root+3:root+7].copy()
        height = qpos[root+2]
        super().ik_root(qpos,angle)
        nominal = qpos[root+3:root+7]
        if np.dot(measured,nominal) < 0:
            measured = -measured
        nominal[:] = .53*nominal + .47*measured
        nominal[:] /= np.linalg.norm(nominal)
        qpos[root+2] = self.height + .50*np.clip(height-self.height,-.10,.10)

    def waist(self, move, side, phase):
        phase = self.attack_phase(phase)
        sign = 1 if side == 0 else -1
        pulse = math.sin(math.pi*phase)**2
        power = self.tactic.power
        if move in PUNCHES:
            yaw, pitch = {"jab": (.08,.12), "cross": (.29,.17), "hook": (.45,.11),
                          "uppercut": (.22,-.13), "overhand": (.34,.31)}[move]
            if self.tactic.target == "head" and move != "uppercut":
                pitch += .065
            windup = math.sin(math.pi*min(phase/.37,1.))**2
            return -sign*(yaw*pulse-.12*windup)*power, sign*.11*pulse, pitch*pulse*power
        if move in KICKS:
            yaw = -.53*sign*pulse if move in {"round_kick","low_kick","side_kick"} else 0.
            return yaw, -.18*sign*pulse, -.14*pulse
        if move == "pull":
            return 0., 0., -.28*pulse
        if move == "slip":
            return -.15*sign*pulse, -.36*sign*pulse, .10*pulse
        if move == "feint":
            return -.23*sign*pulse, 0., .18*pulse
        return super().waist(move,side,phase)

    def hand_goals(self, move, side, phase, pos, basis):
        goals = super().hand_goals("cover" if move=="cover" else "guard",side,phase,pos,basis)
        if move not in PUNCHES and move != "feint":
            return goals
        sign = 1 if side == 0 else -1
        reach = self.attack_envelope(phase)
        power = self.tactic.power
        target_body = self.o.head if self.tactic.target=="head" else self.o.torso
        target = self.b.data.xpos[target_body].copy()
        z = -.035 if self.tactic.target=="head" else .12
        target += basis @ np.array([.075, .006*sign,z])
        target += .045*self.b.velocity[target_body]
        if move in {"hook","overhand","uppercut"}:
            windup = math.sin(math.pi*min(self.attack_phase(phase)/.40,1.))**2
            if move == "hook":
                goals[side] += basis@np.array([-.10,.21*sign,.015])*windup
                lateral = .055 if self.tactic.target == "head" else -.042
                target += basis @ np.array([0., sign*(.34*(1-reach)+lateral),0.])
            elif move == "overhand":
                goals[side] += basis@np.array([-.07,.16*sign,.14])*windup
                target += basis @ np.array([0.,sign*(.095*(1-reach)+.048),.23*(1-reach)])
            else:
                dip = -.13 if self.tactic.target == "head" else -.19
                goals[side] += basis@np.array([.04,.01*sign,dip])*windup
                target += basis @ np.array([0.,0.,-.23*(1-reach)])
        if move == "feint":
            reach *= .52
        local = basis.T@(target-pos)
        local[0] = np.clip(local[0],.11,.63)
        goals[side] += min(1.18,reach*(.78+.28*power))*(pos+basis@local-goals[side])
        return goals

    def kick(self, goals, foot_yaws, side, phase, pos, basis):
        move = self.tactic.move
        phase = self.attack_phase(phase)
        sign = 1 if side == 0 else -1
        if self.committed_target is None:
            self.committed_target = self.b.data.xpos[self.r.feet[side]].copy()
        extend = smooth((phase-.25)/.22)*(1-smooth((phase-.60)/.24))
        chamber = np.array([.27,.18*sign,-.25])
        if move in {"round_kick","low_kick"}:
            chamber = np.array([.10,.43*sign,-.27])
        elif move == "side_kick":
            chamber = np.array([.24,.27*sign,-.19])

        target = self.b.data.xpos[self.o.pelvis].copy()
        if move == "low_kick" or self.tactic.target == "lead_leg":
            legs = self.b.data.xpos[self.o.leg_targets].reshape(2,2,3)
            lead = int(np.argmin(np.linalg.norm(legs[:,1,:2]-pos[:2],axis=1)))
            target = .56*legs[lead,0]+.44*legs[lead,1]
        else:
            target[2] += .20 if move in {"front_kick","side_kick"} else .17
            if self.tactic.target == "head":
                target[2] = min(self.b.data.xpos[self.o.head,2]-.11,pos[2]+.32)
        reach = basis.T@(target-pos)
        reach[0] = np.clip(reach[0]+.075,.52,.738)
        reach[1] += sign*((.24*(1-extend)-.061) if move in {"round_kick","low_kick"} else .025)
        reach[2] = np.clip(reach[2],-.31,.32)
        chamber_world = pos+basis@chamber
        strike_goal = pos+basis@reach
        goal = self.committed_target + smooth(phase/.31)*(chamber_world-self.committed_target)
        goal += extend*(.79+.21*self.tactic.power)*(strike_goal-chamber_world)
        landing = pos+basis@np.array([.069,.144*sign,0.])
        landing[2] = .037
        goal += smooth((phase-.74)/.24)*(landing-goal)
        if phase >= .93:
            self.foot[side] = landing
        goals[side] = goal
        if move in {"round_kick","low_kick","side_kick"}:
            foot_yaws[1-side] -= sign*.52*extend

    def assist(self):
        super().assist()
        force = self.b.data.xfrc_applied[self.r.pelvis]
        # Let a hard hit displace the defender before the balance servo recovers.
        recoiling = self.b.frame < self.recoil_until
        force[:2] *= .54 if recoiling else .73
        force[3:5] *= .73 if recoiling else .83
        force[5] *= .72

    def imminent_threat(self):
        d = self.b.data
        center = d.xpos[self.r.torso].copy() + np.array([0.,0.,.16])
        limbs = np.r_[self.o.hands,self.o.feet]
        rel = center-d.xpos[limbs]
        speed = self.b.velocity[limbs]-self.b.velocity[self.r.torso]
        planar_gap = np.linalg.norm(rel[:,:2],axis=1)
        closing = np.sum(rel[:,:2]*speed[:,:2],axis=1)/np.maximum(planar_gap,.04)
        return bool(np.any((planar_gap < .56)&(closing > 1.15)&(np.abs(rel[:,2])<.48)))

    def outcome(self, meter):
        start = round(self.opened_at*DT,4)
        own_hits = [e for e in self.b.events if e["attacker"] == self.i and e["t"] >= start]
        in_hits = [e for e in self.b.events if e["attacker"] != self.i and e["t"] >= start]
        blocked = [e for e in meter.guards if e["attacker"] == self.i and e["t"] >= start]
        return {"landed":own_hits,"incoming_hits":in_hits,"guard_contacts":blocked}

    def advance_exchange(self, meter):
        if not self.has_choice or self.b.frame < self.next_choice:
            return
        if self.follow is None:
            self.has_choice = False
            return
        _, distance, _, _, _ = self.frame()
        outcome = self.outcome(meter)
        landed, blocked = outcome["landed"], outcome["guard_contacts"]
        conditions = {"always":True, "close":distance<.69, "kick_range":.59<distance<1.0,
                      "incoming":self.imminent_threat(), "landed":bool(landed),
                      "blocked":bool(blocked), "missed":not (landed or blocked)}
        follow, self.follow = self.follow, None
        if conditions[self.trigger]:
            self.queue(follow, "follow:"+self.trigger)
        else:
            self.has_choice = False

    def observation(self, turn, meter):
        obs = self.b.perception(self.i)
        distance = obs["distance_m"]
        old = [s[self.i] for s in self.b.history[-12::5]]
        return {"turn":turn,"remaining_s":round((self.b.limit-self.b.frame)*DT,2),
                "state":obs,"incoming_limb":self.imminent_threat(), "own_last_exchange":self.sequence[-2:],
                "outcome":self.outcome(meter),
                "recent_range":[[s["t"],s["distance_m"],s["opponent_bearing_deg"]] for s in old],
                "ranges":{"punch":[.36,.69],"kick":[.61,1.0],"distance":distance}}


def ask(bridge, fighters, turns, meter, log):
    pending = {}
    for fighter in fighters:
        index = fighter.i
        obs = fighter.observation(turns[index],meter)
        write_json(bridge/f"observe-{index}.json",obs)
        pending[index] = (fighter,obs)
    deadline = time.monotonic()+240
    while pending:
        for i,(fighter,obs) in tuple(pending.items()):
            path = bridge/f"action-{i}-{obs['turn']:03}.json"
            if not path.is_file():
                continue
            try:
                raw = json.loads(path.read_text())
                command = parse_exchange(raw,obs["turn"])
            except ValueError as error:
                write_json(bridge/f"error-{i}.json",{"turn":obs["turn"],"error":str(error)})
                path.unlink()
                continue
            fighter.begin(command)
            log.write(json.dumps({"fighter":i,"frame":fighter.b.frame,"observation":obs,"command":raw})+"\n")
            log.flush()
            turns[i] += 1
            del pending[i]
        if pending:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{bridge}: waiting for actions from fighters {list(pending)}")
            time.sleep(.12)


def run(args):
    args.output.mkdir(parents=True)
    args.bridge.mkdir(parents=True)
    bout = Bout(args.seed,args.opening,args.seconds,args.output,endurance=True,load_policy=False)
    bout.kickboxers = [ExchangeFighter(bout,i) for i in range(2)]
    meter = ImpactMeter(bout,detailed=True)
    initialize_bout(bout)
    write_json(args.output/"settings.json", {"seconds":args.seconds,"agents":0,"endurance":True,
               "controllers":["Pressure","Counter"],"seed":args.seed,"tactical_model":args.model_name,
               "direct_exchange":True})
    turns = [0,0]
    seen_impacts = 0
    with (args.output/"commands.jsonl").open("w") as commands, (args.output/"decisions.jsonl").open("w") as moves:
        while not bout.status():
            for fighter in bout.kickboxers:
                fighter.advance_exchange(meter)
            request = [fighter for fighter in bout.kickboxers if not fighter.has_choice]
            if request:
                ask(args.bridge,request,turns,meter,commands)
            for fighter in bout.kickboxers:
                move = fighter.step()
                if move:
                    move["command"] = asdict(fighter.tactic)
                    moves.write(json.dumps(move)+"\n")
            physics_step(bout,meter)
            for impact in bout.events[seen_impacts:]:
                if impact["impulse_ns"] >= 4.:
                    bout.kickboxers[1-impact["attacker"]].recoil_until = bout.frame+5
            seen_impacts = len(bout.events)
    bout.save()
    write_json(args.output/"guard-contacts.json",meter.guards)
    write_json(args.bridge/"complete.json",{"turns":turns})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("bridge",type=Path)
    parser.add_argument("--seed",type=int,default=23)
    parser.add_argument("--seconds",type=float,default=27.)
    parser.add_argument("--opening",type=float,default=1.15)
    parser.add_argument("--model-name",default="external")
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds < DT:
        parser.error("Round must last at least one control step")
    run(args)


if __name__ == "__main__":
    main()
