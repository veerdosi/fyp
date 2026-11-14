"""Task-space attacks and defenses layered over GGSD's feedback motor policy."""
import mujoco as mj
import numpy as np

from fight import SKILLS, yaw_rotation

ARM = ([11, 15, 19, 21], [12, 16, 20, 22])
LEG = ([0, 3, 6, 9, 13, 17], [1, 4, 7, 10, 14, 18])


def smooth(x):
    x = np.clip(x, 0., 1.)
    return x*x*(3-2*x)


def pulse(phase, start, peak, end):
    return float(smooth((phase-start)/(peak-start)) * smooth((end-phase)/(end-peak)))


class MotorSkill:
    def __init__(self, bout, index, command):
        self.bout, self.index, self.command = bout, index, command
        self.robot, self.opponent = bout.robots[index], bout.robots[1-index]
        self.policy = bout.policies[index]
        self.move = command["move"]
        self.base = command.get("base", {
            "jab": "punch", "cross": "power", "hook": "punch",
            "slip_left": "turn_left", "slip_right": "turn_right",
            "low_kick": "pull", "front_kick": "pull", "knee": "power",
            "push": "punch", "cover": "pull", "feint": "punch",
        }.get(self.move, "punch"))
        self.hand = int(command.get("side", "right" if self.move == "cross" else "left") == "right")
        self.power = command.get("power", .8)
        self.arc = command.get("arc", .8 if self.move == "hook" else 0.)
        self.limb = command.get("limb", {"low_kick": "foot", "front_kick": "foot",
                                        "knee": "knee"}.get(self.move, "hand"))
        self.target = command.get("target", "lead_leg" if self.move == "low_kick" else "body")
        self.kick_origin = None
        self.base_skill = None
        self.jacobian = np.zeros((3, bout.model.nv))
        self.foot_site = np.array([.075, 0., -.02])
        self.heading_offset = {
            "close": 0., "angle_left": .38, "angle_right": -.38,
        }.get(self.move, 0. if command.get("track", False) else None)

    def solve(self, goal, body, point, joint_subset, targets, blend, correction):
        d, m, r = self.bout.data, self.bout.model, self.robot
        mj.mj_jac(m, d, self.jacobian, None, point, body)
        local = self.jacobian[:, r.v[joint_subset]]
        delta = local.T @ np.linalg.solve(local @ local.T + .011*np.eye(3),
                                           np.clip(goal-point, -.40, .40))
        measured = d.qpos[r.q[joint_subset]]
        ik = measured + np.clip(correction*delta, -.90, .90)
        bounded = np.clip(ik, r.limits[joint_subset, 0]+.04, r.limits[joint_subset, 1]-.04)
        targets[joint_subset] = (1-blend)*targets[joint_subset] + blend*bounded

    def aim(self, heading):
        d, o = self.bout.data, self.opponent
        if self.target == "lead_leg":
            pelvis = d.xpos[self.robot.pelvis]
            nearest = int(np.argmin(np.linalg.norm(d.xpos[o.feet]-pelvis, axis=1)))
            ankle = d.xpos[o.feet[nearest]]
            target = .52*d.xpos[o.pelvis] + .48*ankle
            return target + .05 * self.bout.velocity[o.feet[nearest]]
        body = o.head if self.target == "head" else o.torso
        offset = np.array([.045, 0., .025 if self.target == "head" else .14])
        return d.xpos[body] + self.bout.matrices[body] @ offset + .055*self.bout.velocity[body]

    def boxing(self, targets, phase, heading):
        d, r = self.bout.data, self.robot
        strike = pulse(phase, .02, .55, .99)
        if self.move == "feint":
            strike = .38*pulse(phase, .02, .28, .69)
        if self.move == "cover":
            strike = pulse(phase, 0, .34, 1.05)
        base = d.xpos[r.pelvis]
        sign = 1 if self.hand == 0 else -1
        for hand in ([0, 1] if self.move in ("push", "cover") else [self.hand]):
            weapon = r.hands[hand]
            hand_sign = 1 if hand == 0 else -1
            point = d.xpos[weapon] + self.bout.matrices[weapon] @ np.array([.095, -.01*hand_sign, 0])
            guard = base + heading.T @ np.array([.26, .16*hand_sign, .33])
            aim = self.aim(heading)
            if self.move == "cover":
                aim = base + heading.T @ np.array([.23, .10*hand_sign, .41])
            elif self.move == "push":
                aim += heading.T @ np.array([0., .10*hand_sign, -.06])
            elif self.arc:
                aim += heading.T @ np.array([0, sign*.23*self.arc*(1-phase), .035*self.arc])
            desired = (1-strike)*guard + strike*aim
            blend = min(.95, (.50+.37*self.power)*pulse(phase, 0, .50, 1.04))
            self.solve(desired, weapon, point, ARM[hand], targets, blend, 1.65)
        if self.move != "cover":
            targets[2] += sign * (.20 + .22*abs(self.arc)) * strike
            targets[8] += .10 * strike * self.power

    def kick(self, targets, phase, heading):
        r, d = self.robot, self.bout.data
        side = 1 if self.hand == 0 else -1
        other = 1-self.hand
        foot = r.feet[self.hand]
        point = d.xpos[foot] + self.bout.matrices[foot] @ self.foot_site
        if self.kick_origin is None:
            self.kick_origin = point.copy()
        goal = self.aim(heading)
        pelvis = d.xpos[r.pelvis]
        local = heading @ (goal - pelvis)
        cap = .51 if self.move == "low_kick" else .48
        local[0] = np.clip(local[0], .18, cap + .06*self.power)
        local[1] = np.clip(local[1], -.28, .28)
        local[2] = np.clip(local[2], -.61, .06)
        chamber = pelvis + heading.T @ np.array([.15, .095*side, -.42])
        strike = pelvis + heading.T @ local
        if self.move == "low_kick":
            chamber += heading.T @ np.array([-.02, .09*side, -.03])
            strike += heading.T @ np.array([0, .05*self.arc, 0])
        load = pulse(phase, .01, .28, .95)
        extension = pulse(phase, .27, .58, .86)
        return_to_floor = smooth((phase-.71)/.29)
        desired = (1-extension)*chamber + extension*strike
        desired = desired*(1-return_to_floor) + return_to_floor*self.kick_origin
        blend = (.65 + .20*self.power)*pulse(phase, .07, .53, 1.05)
        if self.limb == "knee":
            knee = r.knees[self.hand]
            knee_point = d.xpos[knee]
            knee_goal = pelvis + heading.T @ np.array([.25, .08*side, -.08])
            self.solve(knee_goal, knee, knee_point, LEG[self.hand], targets, blend, 2.1)
            targets[9+self.hand] += 1.0*blend
        else:
            self.solve(desired, foot, point, LEG[self.hand], targets, blend, 1.9)
            targets[9+self.hand] += .26*load*(1-extension)
        # Joint targets bias the hips onto the stance foot. Its learned feedback
        # remains active throughout the strike and both feet remain collision bodies.
        targets[3+other] += .16*side*load
        targets[17+other] -= .12*side*load
        targets[5] += .21*side*load
        targets[8] -= .22*load
        targets[2] += .23*side*extension*self.arc

    def act(self, obs, tick, frames):
        if self.move == "auto":
            if tick % 10 == 0:
                logits = self.policy.predict(obs, "hl")
                probabilities = np.exp(logits - logits.max())
                self.base_skill = self.bout.rng.choice(6, p=probabilities/probabilities.sum())
            return self.policy.action(obs, self.policy.codes[self.base_skill])
        if self.move in ("close", "angle_left", "angle_right"):
            distance = np.linalg.norm(obs[88:90])
            # Blend the walking and leaning-back policies so pursuit stops in striking range.
            gait = smooth((distance-.46)/.42)
            code = gait*self.policy.codes[1] + (1-gait)*self.policy.codes[5]
            return self.policy.action(obs, code)
        if self.move in SKILLS:
            return self.policy.action(obs, self.policy.codes[SKILLS.index(self.move)])

        code = self.policy.codes[SKILLS.index(self.base)]
        action = self.policy.action(obs, code)
        delay = self.command.get("delay", 0.)
        phase = (tick/max(1,frames-1)-delay)/(1-delay)
        if phase <= 0:
            return action
        targets = action*self.robot.scale
        _, heading = yaw_rotation(self.bout.matrices[self.robot.pelvis])
        if self.move in ("slip_left", "slip_right"):
            sign = 1 if self.move == "slip_left" else -1
            bend = pulse(phase, 0, .43, 1.07)
            targets[5] += sign * .29*bend
            targets[8] += .18*bend
            targets[[9, 10]] += .22*bend
            targets[[0, 1]] -= .11*bend
        elif self.limb in ("foot", "knee"):
            self.kick(targets, phase, heading)
        else:
            self.boxing(targets, phase, heading)
        return targets/self.robot.scale
