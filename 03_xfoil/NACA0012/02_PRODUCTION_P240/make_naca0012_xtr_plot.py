from pathlib import Path
import matplotlib.pyplot as plt

POLAR = Path("NACA0012_SHARP_TE_V9_Re1e6_Ncrit9_P240.pol")

THESIS_DIR = (
    Path.home()
    / "Desktop/Final_stretch/08_THESIS_REPORT/bilder/thesis"
)

OVERLEAF_DIR = (
    Path.home()
    / "Desktop/Final_stretch/08_OVERLEAF_SOURCE/bilder/thesis"
)

OUT_PDF = "NACA0012_XFOIL_transition_location_vs_AoA.pdf"
OUT_PNG = "NACA0012_XFOIL_transition_location_vs_AoA.png"

aoa = []
top_xtr = []
bot_xtr = []

with POLAR.open() as f:
    lines = f.readlines()

for line in lines:
    s = line.strip()

    if not s:
        continue
    if s.startswith("XFOIL"):
        continue
    if s.startswith("Calculated polar"):
        continue
    if s.startswith("1 1 Reynolds"):
        continue
    if s.startswith("xtrf"):
        continue
    if s.startswith("Mach"):
        continue
    if "alpha" in s and "Top_Xtr" in s:
        continue
    if set(s.replace(" ", "")) == {"-"}:
        continue

    parts = s.split()
    if len(parts) < 7:
        continue

    try:
        a = float(parts[0])
        tx = float(parts[5])
        bx = float(parts[6])
    except ValueError:
        continue

    if a <= 14.5:
        aoa.append(a)
        top_xtr.append(tx)
        bot_xtr.append(bx)

if len(aoa) == 0:
    raise RuntimeError("No valid XFOIL rows were read from the polar file.")

fig, ax = plt.subplots(figsize=(7.2, 4.8))

ax.plot(
    aoa,
    top_xtr,
    marker="o",
    linewidth=1.8,
    label="Upper surface transition, $x_{tr}/c$",
)

ax.plot(
    aoa,
    bot_xtr,
    marker="s",
    linewidth=1.8,
    label="Lower surface transition, $x_{tr}/c$",
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel(r"Transition location, $x_{tr}/c$")
ax.set_xlim(0, 14.5)
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")

THESIS_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_DIR.mkdir(parents=True, exist_ok=True)

(THESIS_DIR / OUT_PDF).write_bytes(Path(OUT_PDF).read_bytes())
(THESIS_DIR / OUT_PNG).write_bytes(Path(OUT_PNG).read_bytes())

(OVERLEAF_DIR / OUT_PDF).write_bytes(Path(OUT_PDF).read_bytes())
(OVERLEAF_DIR / OUT_PNG).write_bytes(Path(OUT_PNG).read_bytes())

print("=" * 60)
print("NACA0012 XFOIL TRANSITION PLOT COMPLETE")
print("=" * 60)
print("Rows used:")
for a, tx, bx in zip(aoa, top_xtr, bot_xtr):
    print(f"AoA={a:4.1f}  Top_Xtr={tx:.4f}  Bot_Xtr={bx:.4f}")
print()
print("Created locally:")
print(Path(OUT_PDF).resolve())
print(Path(OUT_PNG).resolve())
print()
print("Copied to:")
print(THESIS_DIR / OUT_PDF)
print(THESIS_DIR / OUT_PNG)
print(OVERLEAF_DIR / OUT_PDF)
print(OVERLEAF_DIR / OUT_PNG)
