"""Render recorded MuJoCo poses as a side-on fight broadcast with contact audio."""
import argparse
from bisect import bisect_right
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import wave

import mujoco as mj
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from arena import make_arena
from fight import HP, SIDES

BLUE = (60, 206, 229)
ORANGE = (255, 129, 64)
WHITE = (231, 238, 247)
MUTED = (154, 172, 192)
FONTS = Path("/System/Library/Fonts/Supplemental")
SANS = ("DIN Alternate Bold.ttf", "Arial Bold.ttf")
MONO = ("Andale Mono.ttf",)


@lru_cache
def font(families, size):
    for family in families:
        for path in (FONTS / family, Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
            if path.exists():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def blend(value, target, rate):
    return value + (target-value)*rate


class RingsideCamera:
    def __init__(self, model, mirror=False, elevation=11.):
        self.camera = mj.MjvCamera()
        self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.pelvis = [model.body(f"{side}_pelvis").id for side in SIDES]
        self.heading = None
        self.focus = None
        self.distance = 3.5
        self.mirror = mirror
        self.elevation = elevation

    def update(self, data, elapsed, terminal=False):
        a, b = data.xpos[self.pelvis]
        delta = b - a
        line_angle = math.degrees(math.atan2(delta[1], delta[0]))
        target_heading = line_angle + (-90 if self.mirror else 90)
        target_heading += 12*math.sin(elapsed*.55 + .35)
        midpoint = (a+b)/2
        midpoint[2] = .68 if not terminal else .59
        spread = np.linalg.norm(delta[:2])
        distance = max(2.75, 2.48 + spread*.64)
        if self.focus is None:
            self.heading = target_heading
            self.focus = midpoint
            self.distance = distance
        difference = (target_heading-self.heading+180) % 360 - 180
        self.heading += np.clip(difference, -24, 24)*.047
        self.focus = blend(self.focus, midpoint, .065)
        self.distance = blend(self.distance, distance, .07)
        self.camera.lookat = self.focus
        self.camera.distance = self.distance
        self.camera.azimuth = self.heading
        self.camera.elevation = -self.elevation - 2.5*math.sin(elapsed*.75)
        return self.camera


def overlay(rgb, elapsed, health, damage, result, limit, bout_name,
            intro=False, agents=2, endurance=False, impact=None, controllers=None,
            tactical_model=None):
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    scale = h / 1080

    def text(x, y, value, size, color=WHITE, anchor="lt", family=SANS):
        draw.text((round(x), round(y)), value, fill=color,
                  font=font(family, max(10, round(size*scale))), anchor=anchor)

    def box(coords, color):
        draw.rectangle(tuple(round(c) for c in coords), fill=color)

    if intro:
        box((0, 0, w, h), (6, 11, 21, 164))
        box((w/2-52*scale, h*.318, w/2-3*scale, h*.322), (*BLUE, 255))
        box((w/2+3*scale, h*.318, w/2+52*scale, h*.322), (*ORANGE, 255))
        text(w/2, h*.38, "UNITREE G1", 99, anchor="mt")
        matchup = ("GGSD  /  GGSD", "ASTRA  /  GGSD", "ASTRA  /  ASTRA")[agents]
        if controllers:
            matchup = "  /  ".join(name.upper() for name in controllers)
        text(w/2, h*.51, matchup, 33, anchor="mt")
        text(w/2, h*.585, "LIVE CONTROL IN MUJOCO", 16, MUTED, "mt", MONO)
        return image

    top = 40*scale
    gutter = 53*scale
    bar = w*.285
    box((gutter-13*scale, top-11*scale, w-gutter+13*scale, top+65*scale), (7, 13, 22, 160))
    for index, (name, color) in enumerate((("TEAL", BLUE), ("AMBER", ORANGE))):
        edge = gutter if index == 0 else w-gutter
        direction = 1 if index == 0 else -1
        end = edge + direction*bar
        anchor = "lt" if index == 0 else "rt"
        text(edge, top, name, 26, color, anchor)
        label = f"{damage[index]/1000:.1f}K PTS" if endurance else f"{health[index]/HP*100:.0f}"
        text(end, top+4*scale, label, 18, WHITE,
             "rt" if index == 0 else "lt", MONO)
        y = top + 35*scale
        box((min(edge,end), y, max(edge,end), y+6*scale), (68, 87, 105, 210))
        progress = min(1., damage[index]/HP) if endurance else max(0., health[index]/HP)
        filled = edge + direction*bar*progress
        box((min(edge,filled), y, max(edge,filled), y+6*scale), (*color, 255))
        policy = controllers[index].upper() if controllers else ("GPT-6 ASTRA" if index < agents else "GGSD")
        text(edge, y+15*scale, policy, 12, MUTED, anchor, MONO)
    text(w/2, top+4*scale, bout_name, 14, MUTED, "mt", MONO)
    remain = max(0, limit-elapsed)
    text(w/2, top+26*scale, f"{remain:04.1f}", 34, WHITE, "mt", MONO)
    if tactical_model and tactical_model.startswith("gpt-6.1-sol"):
        text(w/2, top+79*scale, "SOL VS SOL  /  LIVE TACTICS", 12, MUTED, "mt", MONO)

    if impact and not result:
        i = impact["attacker"]
        color = (BLUE, ORANGE)[i]
        label = impact["weapon"].upper() + "  /  " + impact["target"].upper()
        x = gutter if i == 0 else w-gutter
        y = h - 63*scale
        box((x if i == 0 else x-4*scale, y, x+4*scale if i == 0 else x, y+25*scale),
            (*color, 255))
        text(x + (13 if i == 0 else -13)*scale, y+2*scale, label, 15, WHITE,
             "lt" if i == 0 else "rt", MONO)

    if result:
        winner = result["winner"]
        color = {"teal": BLUE, "amber": ORANGE, "draw": WHITE}[winner]
        y = h*.81
        box((w*.344, y-18*scale, w*.656, y+79*scale), (7, 13, 22, 224))
        line = "DRAW" if winner == "draw" else winner.upper() + " WINS"
        text(w/2, y, line, 41, color, "mt")
        method = "DECISION" if result["reason"] == "time" else result["reason"].upper()
        text(w/2, y+49*scale, method, 15, WHITE, "mt", MONO)
    return image


def broadcast(rgb, elapsed, damage, result, limit, bout_name, intro, commands,
              events, round_wins, match_final, hit_flash):
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    s = h/1080
    if hit_flash:
        image = Image.blend(image,Image.new("RGB",image.size,(225,239,246)),hit_flash)
        draw = ImageDraw.Draw(image,"RGBA")

    def txt(x,y,value,px,color=WHITE,anchor="lt",family=SANS):
        draw.text((round(x),round(y)),str(value),fill=color,anchor=anchor,
                  font=font(family,max(10,round(px*s))))

    def panel(x,y,ww,hh,color,radius=12):
        draw.rounded_rectangle((round(x),round(y),round(x+ww),round(y+hh)),
                               radius=max(1,round(radius*s)),fill=color)

    dark = (8,17,28,235)
    if intro:
        draw.rectangle((0,0,w,h),fill=(2,8,16,174))
        y = h*.34
        txt(w/2,y,"MUJOCO KICKBOXING  /  V3",20,MUTED,"mt",MONO)
        txt(w/2,y+41*s,"UNITREE G1",105,WHITE,"mt")
        txt(w/2-30*s,y+199*s,"TEAL",33,BLUE,"rt")
        txt(w/2,y+202*s,"VS",20,WHITE,"mt",MONO)
        txt(w/2+30*s,y+199*s,"AMBER",33,ORANGE,"lt")
        txt(w/2,y+254*s,"GPT-6.1 SOL ON BOTH SIDES",17,MUTED,"mt",MONO)
        return image

    top = 32*s
    margin = 47*s
    width = .289*w
    remaining = max(0.,limit-elapsed)
    panel(w/2-110*s,top,220*s,105*s,dark)
    txt(w/2,top+12*s,bout_name,17,MUTED,"mt",MONO)
    txt(w/2,top+41*s,f"{remaining:04.1f}",42,WHITE,"mt")
    for i,(name,color) in enumerate((("TEAL",BLUE),("AMBER",ORANGE))):
        x = margin if i == 0 else w-margin-width
        left = x+20*s
        right = x+width-20*s
        event = events[i]
        panel(x,top,width,105*s,dark)
        accent_x = x if i == 0 else x+width-5*s
        panel(accent_x,top+10*s,5*s,85*s,(*color,255),2)
        txt(left,top+10*s,name,34,color)
        txt(left,top+52*s,commands[i] if commands else "GUARD",17,WHITE,"lt",MONO)
        txt(right,top+15*s,f"{damage[i]:,.0f}",31,WHITE,"rt")
        txt(right,top+54*s,"CONTACT PTS",13,MUTED,"rt",MONO)
        txt(left,top+79*s,f"ROUNDS WON  {round_wins[i]}",12,MUTED,"lt",MONO)
        if event and not result:
            by = h-105*s
            panel(x,by,width,66*s,dark)
            panel(accent_x,by+8*s,5*s,50*s,(*color,255),2)
            txt(left,by+11*s,event["move"].replace("_"," ").upper(),20,color)
            txt(left,by+37*s,event["target"].upper(),14,WHITE,"lt",MONO)
            txt(right,by+15*s,f"+{event['points']:,.0f}",31,color,"rt")

    if result:
        winner = result["winner"]
        color = {"teal":BLUE,"amber":ORANGE,"draw":WHITE}[winner]
        score = list(round_wins)
        if winner != "draw":
            score[0 if winner=="teal" else 1] += 1
        y = h*.725
        panel(w/2-287*s,y,574*s,199*s,(8,17,28,246),18)
        txt(w/2,y+19*s,"FINAL ROUND" if match_final else "ROUND COMPLETE",15,MUTED,"mt",MONO)
        headline = "ROUND DRAW" if winner=="draw" else winner.upper()+" TAKES THE ROUND"
        txt(w/2,y+47*s,headline,36,color,"mt")
        txt(w/2,y+94*s,f"{damage[0]:,.0f}  /  {damage[1]:,.0f} CONTACT PTS",19,WHITE,"mt",MONO)
        caption = "MATCH DRAW" if score[0]==score[1] else ("TEAL WINS MATCH" if score[0]>score[1] else "AMBER WINS MATCH")
        if not match_final:
            caption = "ROUNDS WON"
        txt(w/2,y+143*s,f"{caption}   {score[0]}–{score[1]}",18,MUTED,"mt",MONO)
    return image


def pose_at(qpos, frame, roots):
    k = min(int(frame), len(qpos)-1)
    if k == len(qpos)-1:
        return qpos[k]
    fraction = frame-k
    a, b = qpos[k], qpos[k+1]
    q = a + fraction*(b-a)
    for root in roots:
        sl = slice(root+3, root+7)
        if np.dot(a[sl], b[sl]) < 0:
            q[sl] = a[sl] - fraction*(b[sl]+a[sl])
        q[sl] /= np.linalg.norm(q[sl])
    return q


def footfalls(qpos, model):
    data = mj.MjData(model)
    feet = [model.body(f"{side}_{leg}_ankle_roll_link").id
            for side in SIDES for leg in ("left", "right")]
    heights = []
    for pose in qpos:
        data.qpos[:] = pose
        mj.mj_kinematics(model, data)
        heights.append(data.xpos[feet, 2].copy())
    heights = np.asarray(heights)
    events = []
    for foot in range(4):
        last = -10
        for k in range(3, len(heights)):
            approach = heights[k-2, foot] - heights[k, foot]
            if heights[k, foot] < .065 and approach > .04 and k-last > 7:
                events.append((k/30, min(.1, .035+approach*.20), -.26 if foot < 2 else .26))
                last = k
    return events


def sound(path, length, impacts, steps, intro, speed):
    sample_rate = 48000
    rng = np.random.default_rng(24)
    samples = np.arange(round(length*sample_rate))/sample_rate
    stereo = np.zeros((len(samples), 2), dtype=np.float32)

    def add(start, duration, synth, level, pan=0.):
        offset = round(start*sample_rate)
        count = min(round(duration*sample_rate), len(samples)-offset)
        if count < 1:
            return
        t = samples[:count]
        signal = level*synth(t)
        stereo[offset:offset+count, 0] += signal * math.sqrt(.5*(1-pan))
        stereo[offset:offset+count, 1] += signal * math.sqrt(.5*(1+pan))

    hum = (.016*np.sin(2*np.pi*53*samples) + .008*np.sin(2*np.pi*81*samples))
    hum *= np.minimum(1., samples*2) * np.minimum(1., np.maximum(0, length-samples)*1.5)
    stereo += hum[:, None]
    add(max(0., intro-.14), .65, lambda t: np.sin(2*np.pi*565*t)*np.exp(-t*11)
        + .34*np.sin(2*np.pi*913*t)*np.exp(-t*23), .13)

    for t, strength, pan in steps:
        add(intro+t/speed, .085,
            lambda x: np.exp(-52*x)*np.sin(2*np.pi*92*x)
            + .30*np.exp(-115*x)*rng.standard_normal(len(x)), strength, pan)

    for event in impacts:
        level = min(.60, .125+.0022*event["peak_normal_n"])
        pan = -.28 if event["attacker"] == 0 else .28
        pitch = 76 if event["target"] == "head" else 49
        add(intro + event["t"]/speed, .26,
            lambda t: np.exp(-22*t)*np.sin(2*np.pi*(pitch*t + 5*(1-np.exp(-15*t))))
            + .47*np.exp(-65*t)*rng.standard_normal(len(t)), level, pan)
    with wave.open(str(path), "wb") as file:
        file.setparams((2, 2, sample_rate, 0, "NONE", "not compressed"))
        file.writeframes((np.tanh(stereo*1.45)*32767).astype("<i2").tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--speed", type=float, default=.78)
    parser.add_argument("--poster", type=float)
    parser.add_argument("--round-wins", nargs=2, type=int, default=(0,0), metavar=("TEAL","AMBER"))
    parser.add_argument("--match-final", action="store_true")
    parser.add_argument("--intro", type=float, default=1.15)
    parser.add_argument("--outro", type=float, default=1.6)
    parser.add_argument("--bout-name", default="ROUND 01")
    parser.add_argument("--mirror", action="store_true")
    parser.add_argument("--elevation", type=float, default=11.)
    parser.add_argument("--hardware", action="store_true", help="Use the macOS H.264 encoder")
    args = parser.parse_args()

    with np.load(args.run / "states.npz") as data:
        qpos, timeline = data["qpos"], data["timeline"]
    settings = json.loads((args.run / "settings.json").read_text())
    result = json.loads((args.run / "result.json").read_text())
    impacts = json.loads((args.run / "impacts.json").read_text())
    direct_exchange = settings.get("direct_exchange", False)
    commands = [[], []]
    if direct_exchange:
        with (args.run / "decisions.jsonl").open() as log:
            for line in log:
                record = json.loads(line)
                commands[record["fighter"]].append(record)
    command_frames = [[record["turn"] for record in rows] for rows in commands]
    model = mj.MjModel.from_xml_string(make_arena())
    state = mj.MjData(model)
    roots = [int(model.joint(f"{side}_root").qposadr[0]) for side in SIDES]
    camera = RingsideCamera(model, args.mirror, args.elevation)
    option = mj.MjvOption()
    option.geomgroup[4] = False
    end = float(timeline[-1, 0])
    visible_impacts = [e for e in impacts if e.get("impulse_ns", 0) >= 2.4 or e["damage_pct"] >= 1.5
                       or e["weapon"].endswith(("foot", "knee")) and e["damage_pct"] >= .6]
    damage = timeline[:, 3:5] if timeline.shape[1] >= 5 else HP - timeline[:, 1:3][:, ::-1]
    if direct_exchange:
        # Recover the exact awarded values from the score timeline, including older V3 logs.
        for e in impacts:
            if "points" in e:
                continue
            frame = round(e["t"]*30)
            same_frame = [other for other in impacts
                          if other["t"]==e["t"] and other["attacker"]==e["attacker"]]
            total = damage[frame,e["attacker"]]-damage[max(0,frame-1),e["attacker"]]
            if len(same_frame) == 1:
                e["points"] = total
            else:
                recorded = sum(hit["damage_pct"] for hit in same_frame)
                e["points"] = total * e["damage_pct"]/recorded if recorded else total/len(same_frame)
    duration = args.intro + end/args.speed + args.outro
    duration = math.ceil(duration*args.fps)/args.fps

    with mj.Renderer(model, height=args.height, width=args.width) as renderer:
        def frame_at(t, title=False, terminal=False):
            frame = min(len(qpos)-1, t*30)
            state.qpos[:] = pose_at(qpos, frame, roots)
            mj.mj_forward(model, state)
            renderer.update_scene(state, camera=camera.update(state, t, terminal),
                                  scene_option=option)
            impact = next((e for e in reversed(visible_impacts) if 0 <= t-e["t"] < .44), None)
            active_commands = None
            if direct_exchange:
                active_commands = []
                for rows, frames in zip(commands, command_frames):
                    index = max(0, bisect_right(frames, frame+1e-6)-1)
                    active_commands.append(rows[index]["move"].replace("_", " ").upper() if rows else "GUARD")
                events = [next((e for e in reversed(impacts)
                                if e["attacker"]==i and -1e-4 <= t-e["t"] < .68),None) for i in (0,1)]
                flash = max((.035*(1-(t-e["t"])/.065) for e in events
                             if e and e["peak_normal_n"] >= 450 and t-e["t"] < .065), default=0.)
                return broadcast(renderer.render(),t,damage[int(frame+1e-6)],result if terminal else None,
                                 settings["seconds"],args.bout_name,title,active_commands,events,
                                 args.round_wins,args.match_final,flash)
            return overlay(renderer.render(), t, timeline[round(frame), 1:3], damage[round(frame)],
                           result if terminal else None, settings["seconds"], args.bout_name, title,
                           settings["agents"], settings.get("endurance", False), impact,
                           settings.get("controllers"), settings.get("tactical_model"))

        if args.poster is not None:
            frame_at(min(args.poster, end)).save(args.output)
            return
        audio = args.run / "soundtrack.wav"
        sound(audio, duration, impacts, footfalls(qpos, model), args.intro, args.speed)
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{args.width}x{args.height}", "-r", str(args.fps), "-i", "-",
            "-i", str(audio),
            *(
                ["-c:v", "h264_videotoolbox", "-profile:v", "high", "-b:v", "14M"]
                if args.hardware else
                ["-c:v", "libx264", "-preset", "fast", "-crf", "17"]
            ),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(args.output),
        ]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            try:
                for i in range(round(duration*args.fps)):
                    video_time = i/args.fps
                    t = min(end, max(0., (video_time-args.intro)*args.speed))
                    image = frame_at(t, title=video_time < args.intro,
                                     terminal=video_time > args.intro + end/args.speed + .16)
                    encoder.stdin.write(image.tobytes())
            finally:
                encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("ffmpeg failed")


if __name__ == "__main__":
    main()
