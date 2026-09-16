from pathlib import Path

in_msh = Path("naca0012_cgrid_v9_interface_transition.msh")
out_msh = Path("naca0012_cgrid_v9_interface_transition_3d_for_openfoam.msh")

z_front = -0.005
z_back = 0.005

nodes = {}
elements = []
physical_names = []

with in_msh.open("r") as f:
    lines = [line.rstrip("\n") for line in f]

i = 0
while i < len(lines):
    if lines[i].strip() == "$PhysicalNames":
        n = int(lines[i + 1].strip())
        physical_names = lines[i + 2:i + 2 + n]
        i += n + 3

    elif lines[i].strip() == "$Nodes":
        n = int(lines[i + 1].strip())
        for j in range(n):
            parts = lines[i + 2 + j].split()
            nid = int(parts[0])
            x, y = float(parts[1]), float(parts[2])
            nodes[nid] = (x, y)
        i += n + 3

    elif lines[i].strip() == "$Elements":
        n = int(lines[i + 1].strip())
        for j in range(n):
            parts = lines[i + 2 + j].split()
            eid = int(parts[0])
            etype = int(parts[1])
            ntags = int(parts[2])
            tags = list(map(int, parts[3:3 + ntags]))
            conn = list(map(int, parts[3 + ntags:]))
            elements.append((eid, etype, tags, conn))
        i += n + 3

    else:
        i += 1

line_elements = [e for e in elements if e[1] == 1]
quad_elements = [e for e in elements if e[1] == 3]

old_ids = sorted(nodes.keys())
n_old = len(old_ids)

front_id = {nid: idx + 1 for idx, nid in enumerate(old_ids)}
back_id = {nid: idx + 1 + n_old for idx, nid in enumerate(old_ids)}

new_nodes = []

for nid in old_ids:
    x, y = nodes[nid]
    new_nodes.append((front_id[nid], x, y, z_front))

for nid in old_ids:
    x, y = nodes[nid]
    new_nodes.append((back_id[nid], x, y, z_back))

new_elements = []
eid = 1

TAG_FRONT_AND_BACK = 6
TAG_FLUID = 7

# Side boundary faces from 2D line elements
for _, etype, tags, conn in line_elements:
    phys = tags[0] if tags else 0
    n1, n2 = conn

    # quad face: front n1-n2, back n2-n1
    new_elements.append((
        eid,
        3,
        [phys, phys],
        [front_id[n1], front_id[n2], back_id[n2], back_id[n1]]
    ))
    eid += 1

# Front and back empty faces from all 2D quads
for _, etype, tags, conn in quad_elements:
    n1, n2, n3, n4 = conn

    # front face
    new_elements.append((
        eid,
        3,
        [TAG_FRONT_AND_BACK, TAG_FRONT_AND_BACK],
        [front_id[n1], front_id[n2], front_id[n3], front_id[n4]]
    ))
    eid += 1

    # back face, reversed orientation
    new_elements.append((
        eid,
        3,
        [TAG_FRONT_AND_BACK, TAG_FRONT_AND_BACK],
        [back_id[n4], back_id[n3], back_id[n2], back_id[n1]]
    ))
    eid += 1

# Hex volume cells from 2D quads
for _, etype, tags, conn in quad_elements:
    n1, n2, n3, n4 = conn

    new_elements.append((
        eid,
        5,
        [TAG_FLUID, TAG_FLUID],
        [
            front_id[n1], front_id[n2], front_id[n3], front_id[n4],
            back_id[n1], back_id[n2], back_id[n3], back_id[n4],
        ]
    ))
    eid += 1

with out_msh.open("w") as f:
    f.write("$MeshFormat\n")
    f.write("2.2 0 8\n")
    f.write("$EndMeshFormat\n")

    f.write("$PhysicalNames\n")
    f.write("7\n")
    f.write('2 1 "airfoil"\n')
    f.write('2 2 "top"\n')
    f.write('2 3 "inlet"\n')
    f.write('2 4 "bottom"\n')
    f.write('2 5 "outlet"\n')
    f.write('2 6 "frontAndBack"\n')
    f.write('3 7 "fluid"\n')
    f.write("$EndPhysicalNames\n")

    f.write("$Nodes\n")
    f.write(f"{len(new_nodes)}\n")
    for nid, x, y, z in new_nodes:
        f.write(f"{nid} {x:.16e} {y:.16e} {z:.16e}\n")
    f.write("$EndNodes\n")

    f.write("$Elements\n")
    f.write(f"{len(new_elements)}\n")
    for eid, etype, tags, conn in new_elements:
        tag_str = " ".join(str(t) for t in tags)
        conn_str = " ".join(str(n) for n in conn)
        f.write(f"{eid} {etype} {len(tags)} {tag_str} {conn_str}\n")
    f.write("$EndElements\n")

print("2D input:", in_msh)
print("3D output:", out_msh)
print("2D nodes:", len(nodes))
print("3D nodes:", len(new_nodes))
print("2D line elements:", len(line_elements))
print("2D quad elements:", len(quad_elements))
print("3D side boundary faces:", len(line_elements))
print("3D front/back faces:", 2 * len(quad_elements))
print("3D hex cells:", len(quad_elements))
