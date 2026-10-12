"""Redraw the report's emission and land-cover results as figures.

Reads the CSVs in viz/data/ (values copied from the report's tables) and writes
PNG figures to images/. Run: python viz/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA, OUT = HERE / "data", HERE.parent / "images"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200, "savefig.bbox": "tight",
    "figure.facecolor": "white",
})
# Okabe-Ito colour-blind-safe palette
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "red": "#D55E00", "purple": "#CC79A7", "grey": "#999999", "black": "#000000"}


def note(fig, text, y=-0.02):
    fig.text(0.01, y, text, fontsize=7, color="#555555", ha="left", va="top")


ward = pd.read_csv(DATA / "emissions_by_ward_landuse.csv", comment="#")
road = pd.read_csv(DATA / "road_emissions.csv", comment="#")
cover = pd.read_csv(DATA / "land_cover_2019_2022.csv", comment="#")

# ---------------------------------------------------------------- Figure 1
res = ward["residential_production"].sum() + ward["residential_operation"].sum()
com = ward["commercial"].sum()
rd = road["total_carbon"].sum()
tot = res + com + rd
lu = pd.DataFrame({"land_use": ["Road circulation", "Residential", "Commercial"],
                   "share": [rd / tot * 100, res / tot * 100, com / tot * 100]})

fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 2.6), gridspec_kw={"width_ratios": [1.15, 1]})
cols = [OI["grey"], OI["blue"], OI["orange"]]
a.barh(lu["land_use"][::-1], lu["share"][::-1], color=cols[::-1], height=0.6)
for y, v in enumerate(lu["share"][::-1]):
    a.text(v + 1.5, y, f"{v:.2f}%" if v < 1 else f"{v:.1f}%", va="center", fontsize=8)
a.set_xlim(0, 100)
a.set_xlabel("Share of total carbon emission (%)")
a.set_title("(a) By major land use")

rshare = road["total_carbon"] / road["total_carbon"].sum() * 100
b.barh(road["material"][::-1], rshare[::-1], color=[OI["green"], OI["sky"], OI["red"]], height=0.6)
for y, v in enumerate(rshare[::-1]):
    b.text(v + 1.5, y, f"{v:.1f}%", va="center", fontsize=8)
b.set_xlim(0, 100)
b.set_xlabel("Share of road-circulation emission (%)")
b.set_title("(b) Roads, by surface material")
fig.suptitle("Carbon emission in Wards 17, 18 and 19, Khulna", fontweight="bold", y=1.04)
note(fig, "Source: report Tables 14, 16 and 17 and the summary calculation. Road emission is "
          f"{rd / res:.2f}× residential and {rd / com:,.0f}× commercial.", y=-0.10)
fig.savefig(OUT / "carbon-emission-share-by-landuse.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 2
groups = {
    "Residential,\nproduction phase": ward["residential_production"],
    "Residential,\noperation phase": ward["residential_operation"],
    "Commercial": ward["commercial"],
}
x = np.arange(len(groups))
w = 0.25
wcol = {17: OI["red"], 18: OI["sky"], 19: OI["orange"]}
fig, ax = plt.subplots(figsize=(6.4, 3.0))
for i, wd in enumerate(ward["ward"]):
    vals = [s.iloc[i] / s.sum() * 100 for s in groups.values()]
    bars = ax.bar(x + (i - 1) * w, vals, w, label=f"Ward {wd}", color=wcol[wd])
    for bx, v in zip(bars, vals):
        ax.text(bx.get_x() + bx.get_width() / 2, v + 1, f"{v:.1f}", ha="center", fontsize=7)
ax.set_xticks(x, list(groups))
ax.set_ylabel("Share of the category's emission (%)")
ax.set_ylim(0, 70)
ax.set_title("Share of each emission category by ward")
ax.legend(frameon=False, ncol=3, loc="upper left")
note(fig, "Source: report Tables 14, 15 and 16. The production phase is 99.99% of residential emission in every ward.")
fig.savefig(OUT / "ward-share-of-emissions.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 3
order = ["Built-up", "Barren land", "Grass land", "Sparse vegetation", "Waterbody", "Unclassified"]
ccol = {"Built-up": OI["red"], "Barren land": OI["yellow"], "Grass land": OI["green"],
        "Sparse vegetation": "#7FC97F", "Waterbody": OI["blue"], "Unclassified": OI["grey"]}
pv = cover.pivot_table(index="year", columns="class", values="area_sq_km", aggfunc="sum").fillna(0)
pct = pv.div(pv.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(6.4, 2.8))
left = np.zeros(len(pct))
years = [str(y) for y in pct.index]
for cls in order:
    if cls not in pct:
        continue
    v = pct[cls].values
    ax.barh(years, v, left=left, color=ccol[cls], label=cls, height=0.6, edgecolor="white", linewidth=0.5)
    for yi, (l, vv) in enumerate(zip(left, v)):
        if vv >= 5:
            ax.text(l + vv / 2, yi, f"{vv:.1f}%", ha="center", va="center", fontsize=7,
                    color="white" if cls == "Built-up" else "black")
    left += v
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("Share of study area (%)  ·  total 25.416 km² each year")
ax.set_title("Land cover in the study area, 2019–2022")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.28), fontsize=8)
note(fig, "Source: report Tables 18–21 (satellite classification). The report notes the images were low resolution, "
          "so year-to-year differences should be read with caution.")
fig.texts[-1].set_y(-0.30)
fig.savefig(OUT / "land-cover-change-2019-2022.png")
plt.close(fig)
print("Figures written to", OUT)
