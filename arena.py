"""A presentation layer over the GGSD G1 MJCF. Added ring geometry is visual."""
import math
from xml.etree import ElementTree as ET

from fetch_assets import ROOT, SCENE

TEAL = "0.05 0.53 0.68"
AMBER = "0.96 0.32 0.06"
RING = 5.0


def geom(parent, name, kind, **attributes):
    return ET.SubElement(parent, "geom", name=name, type=kind,
                         contype="0", conaffinity="0", **attributes)


def make_arena():
    root = ET.parse(ROOT / SCENE).getroot()
    root.find("compiler").set("meshdir", str(ROOT / "exports/g1/meshes"))
    root.find("visual/global").attrib.update(offwidth="1920", offheight="1080", fovy="38")
    root.find("visual/headlight").attrib.update(
        active="1", ambient=".23 .25 .30", diffuse=".14 .16 .20", specular=".08 .08 .10"
    )
    root.find("visual/map").attrib.update(fogstart="0.65", fogend="2.9", shadowclip="1.5")
    root.find("visual/rgba").attrib.update(fog=".016 .022 .034 1", haze=".016 .022 .034 1")
    asset = root.find("asset")
    sky = asset.find("texture")
    sky.attrib.update(builtin="gradient", rgb1=".019 .028 .046", rgb2=".006 .009 .016",
                      width="128", height="256")
    ET.SubElement(asset, "texture", name="mat_weave", type="2d", builtin="checker",
                  rgb1=".154 .186 .216", rgb2=".149 .181 .210", width="256", height="256")
    ET.SubElement(asset, "material", name="canvas", texture="mat_weave", texrepeat="9 9",
                  texuniform="true", specular=".10", shininess=".15")
    for name, rgba, specular, shine, emission in (
        ("steel", ".73 .78 .84 1", ".64", ".64", "0"),
        ("carbon", ".105 .137 .167 1", ".42", ".55", "0"),
        ("teal", TEAL + " 1", ".52", ".61", ".10"),
        ("amber", AMBER + " 1", ".50", ".55", ".08"),
        ("black", ".029 .042 .059 1", ".10", ".25", "0"),
        ("edge", ".21 .30 .39 1", ".27", ".40", "0"),
        ("mark", ".34 .45 .55 1", "0", "0", ".04"),
        ("strip", ".31 .69 .84 1", ".2", ".5", ".45"),
    ):
        ET.SubElement(asset, "material", name=name, rgba=rgba, specular=specular,
                      shininess=shine, emission=emission)
    world = root.find("worldbody")
    floor = world.find("geom[@name='floor']")
    floor.attrib.update(material="black")
    for element in list(world):
        if element.get("name", "").startswith(("wall_", "post_")):
            world.remove(element)
    world.find("light").attrib.update(dir=".36 .44 -.82", diffuse=".94 .91 .83",
                                      specular=".75 .70 .60")
    for name, direction, diffuse in (
        ("blue_rim", "-.45 -.55 -.55", ".31 .56 .79"),
        ("warm_rim", ".85 -.13 -.53", ".55 .35 .23"),
    ):
        ET.SubElement(world, "light", name=name, directional="true", dir=direction,
                      diffuse=diffuse, specular=diffuse, castshadow="false")
    geom(world, "platform", "box", pos="0 0 -.21", size="5.06 5.06 .20", material="black")
    geom(world, "surface", "box", pos="0 0 -.013", size="5 5 .015", material="canvas")
    # The original collision plane stays at z=0. Put its visible surface under the platform.
    floor.attrib.update(group="4")
    for axis in range(2):
        for sign in (-1, 1):
            pos = [0., 0., .002]
            size = [4.77, 4.77, .002]
            pos[axis] = 4.77 * sign
            size[axis] = .012
            geom(world, f"boundary_{axis}_{sign}", "box", pos=" ".join(map(str, pos)),
                 size=" ".join(map(str, size)), material="mark")
    for z in (.28, .55, .83):
        for axis in range(2):
            for sign in (-1, 1):
                a = [0., 0., z]
                b = [0., 0., z]
                a[axis] = b[axis] = sign * RING
                a[1-axis], b[1-axis] = -RING, RING
                geom(world, f"rope_{axis}_{sign}_{z}", "capsule",
                     fromto=" ".join(map(str, a+b)), size=".016", material="edge")
    for x in (-1, 1):
        for y in (-1, 1):
            color = "teal" if x < 0 else "amber"
            geom(world, f"post_{x}_{y}", "box", pos=f"{x*5} {y*5} .45",
                 size=".074 .074 .48", material="black")
            geom(world, f"post_pad_{x}_{y}", "box", pos=f"{x*5} {y*5} .64",
                 size=".10 .10 .23", material=color)
    for axis in range(2):
        for edge_sign in (-1, 1):
            for position in (-6.8, -3.45, 0, 3.45, 6.8):
                center = [0., 0., .92]
                center[axis] = edge_sign*7.5
                center[1-axis] = position
                geom(world, f"stand_{axis}_{edge_sign}_{position}", "box",
                     pos=" ".join(map(str, center)), size=".065 .065 .92", material="black")
                center[2] = 1.82
                strip_size = [.012, .012, .014]
                strip_size[1-axis] = .68
                geom(world, f"strip_{axis}_{edge_sign}_{position}", "box",
                     pos=" ".join(map(str, center)), size=" ".join(map(str, strip_size)),
                     material="strip", rgba=".5 .5 .5 1")
    for index in range(64):
        angle = index * math.tau / 64
        next_angle = (index + .78) * math.tau / 64
        points = [(2.12 * math.cos(a), 2.12 * math.sin(a), .002)
                  for a in (angle, next_angle)]
        geom(world, f"center_mark_{index}", "capsule", size=".005", material="mark",
             fromto=" ".join(str(c) for p in points for c in p))
    for side, color in (("me", "teal"), ("foe", "amber")):
        fighter = world.find(f"body[@name='{side}_pelvis']")
        for body in fighter.iter("body"):
            name = body.get("name")
            for part in body.findall("geom"):
                mesh = part.get("mesh", "")
                if mesh:
                    material = "steel"
                    if any(token in mesh for token in ("roll", "yaw", "elbow", "support")):
                        material = "carbon"
                    if mesh in ("torso_link", "pelvis_contour_link") or "wrist_yaw" in mesh:
                        material = color
                    part.set("rgba", ".5 .5 .5 1")
                    part.set("material", material)
                if name.endswith("_wrist_yaw_link") and part.get("type") == "sphere":
                    part.set("rgba", "0 0 0 0")
                    geom(body, f"{name}_glove_shell", "ellipsoid", pos=part.get("pos", "0 0 0"),
                         size=".070 .065 .068", material=color, rgba=".5 .5 .5 1",
                         group="2", mass="0")
    return ET.tostring(root, encoding="unicode")
