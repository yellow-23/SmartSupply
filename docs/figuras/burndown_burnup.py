# Burn-down y burn-up del Product Backlog (puntos de historia por sprint, Tabla Product Backlog)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pts = [11, 18, 18, 27, 21, 13]  # Sprints 1..6
total = sum(pts)
x = list(range(0, 7))
done = [0]
for p in pts:
    done.append(done[-1] + p)
remaining = [total - d for d in done]
ideal = [total - total * i / 6 for i in x]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2))
a.plot(x, ideal, "--", color="gray", label="Ideal")
a.plot(x, remaining, "-o", color="black", label="Real")
for i, r in zip(x, remaining):
    a.annotate(str(r), (i, r), textcoords="offset points", xytext=(6, 4), fontsize=8)
a.set_title("Burn-down del Product Backlog")
a.set_xlabel("Fin del sprint")
a.set_ylabel("Puntos de historia restantes")
a.set_xticks(x, ["Inicio"] + [f"S{i}" for i in range(1, 7)])
a.set_ylim(0, total + 10)
a.grid(alpha=0.3)
a.legend()

b.plot(x, [total] * 7, "--", color="gray", label=f"Alcance total ({total} pts)")
b.plot(x, done, "-o", color="black", label="Completado acumulado")
for i, d in zip(x, done):
    b.annotate(str(d), (i, d), textcoords="offset points", xytext=(-14, 6), fontsize=8)
b.set_title("Burn-up del proyecto")
b.set_xlabel("Fin del sprint")
b.set_ylabel("Puntos de historia completados")
b.set_xticks(x, ["Inicio"] + [f"S{i}" for i in range(1, 7)])
b.set_ylim(0, total + 10)
b.grid(alpha=0.3)
b.legend(loc="lower right")

fig.tight_layout()
fig.savefig("burndown_burnup.png", dpi=200)
