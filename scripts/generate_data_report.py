#!/usr/bin/env python3
"""
Genera un informe HTML legible sobre los datasets de gold (IA + master).

Salida por defecto: reports/informe_datos_gold.html
"""

from __future__ import annotations

import base64
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATASET_IA = BASE_DIR / "data" / "gold" / "dataset_final_ia.csv"
MASTER_FILE = BASE_DIR / "data" / "gold" / "master_dataset.csv"
OUT_HTML = BASE_DIR / "reports" / "informe_datos_gold.html"


def df_to_html_table(df: pd.DataFrame, float_format: str = "{:.4f}".format) -> str:
    return df.to_html(
        classes="dataframe",
        border=0,
        float_format=lambda x: float_format(x) if pd.notna(x) else "",
        escape=True,
    )


def fig_to_base64(fig) -> str:
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.standard_b64encode(buf.read()).decode("ascii")


def build_html(
    df_ia: pd.DataFrame,
    df_master: pd.DataFrame | None,
    generated_at: str,
) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # --- Figuras ---
    fig1, ax = plt.subplots(figsize=(6, 3.5))
    tgt = df_ia["target_derroche_next_hour"].value_counts().sort_index()
    ax.bar(tgt.index.astype(str), tgt.values, color=["#2ecc71", "#e74c3c"])
    ax.set_xlabel("target_derroche_next_hour")
    ax.set_ylabel("Filas")
    ax.set_title("Distribución del target (dataset IA)")
    fig1.tight_layout()
    b64_target = fig_to_base64(fig1)

    miss = df_ia.isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    b64_miss = ""
    if len(miss) > 0:
        fig2, ax2 = plt.subplots(figsize=(7, 3.5))
        miss.plot(kind="barh", ax=ax2, color="#3498db")
        ax2.set_xlabel("Celdas vacías")
        ax2.set_title("Valores faltantes por columna (dataset IA)")
        fig2.tight_layout()
        b64_miss = fig_to_base64(fig2)

    desc = df_ia.describe(include="all").T
    desc = desc.round(4)

    missing_tbl = (
        pd.DataFrame({"columna": df_ia.columns, "vacíos": df_ia.isna().sum().values})
        .sort_values("vacíos", ascending=False)
        .reset_index(drop=True)
    )

    master_block = ""
    if df_master is not None and len(df_master) > 0:
        if "datetime" in df_master.columns:
            dt = pd.to_datetime(df_master["datetime"], errors="coerce")
            master_block = f"""
        <h2>Master dataset (referencia)</h2>
        <p class="meta">Filas: <strong>{len(df_master):,}</strong>
        &nbsp;· Rango temporal: <strong>{dt.min()}</strong> → <strong>{dt.max()}</strong></p>
        """
        else:
            master_block = f"<h2>Master dataset</h2><p class=\"meta\">Filas: <strong>{len(df_master):,}</strong></p>"
        if "calefaccion_on_normas_history" in df_master.columns:
            c = df_master["calefaccion_on_normas_history"].value_counts(dropna=False)
            master_block += "<h3>Calefacción (normas History)</h3>" + df_to_html_table(
                c.rename("filas").to_frame()
            )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Informe datos Gold — Domótica</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --card: #fff;
      --text: #1a1d23;
      --muted: #5c6370;
      --border: #e2e5eb;
      --accent: #2563eb;
    }}
    body {{
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      margin: 0;
      padding: 2rem 1.5rem 4rem;
    }}
    .wrap {{ max-width: 960px; margin: 0 auto; }}
    h1 {{ font-size: 1.65rem; font-weight: 650; margin: 0 0 0.25rem; }}
    .sub {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }}
    h2 {{ font-size: 1.2rem; margin: 2rem 0 0.75rem; border-bottom: 2px solid var(--border); padding-bottom: 0.35rem; }}
    h3 {{ font-size: 1rem; margin: 1.25rem 0 0.5rem; color: var(--muted); font-weight: 600; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,.06);
    }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin: 0.5rem 0 1rem; }}
    table.dataframe {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    table.dataframe th, table.dataframe td {{
      border: 1px solid var(--border);
      padding: 0.45rem 0.65rem;
      text-align: left;
    }}
    table.dataframe th {{ background: #f0f2f6; font-weight: 600; }}
    table.dataframe tr:nth-child(even) {{ background: #fafbfc; }}
    .fig {{ margin: 1rem 0; text-align: center; }}
    .fig img {{ max-width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border); }}
    ul.kpis {{ list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; }}
    ul.kpis li {{
      background: linear-gradient(135deg, #eff6ff 0%, #fff 100%);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
    }}
    ul.kpis strong {{ display: block; font-size: 1.35rem; color: var(--accent); }}
    ul.kpis span {{ font-size: 0.8rem; color: var(--muted); }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Informe de datos (capa Gold)</h1>
    <p class="sub">Generado: {generated_at} · Proyecto Domótica</p>

    <div class="card">
      <h2>Dataset final IA</h2>
      <p class="meta">Archivo: <code>data/gold/dataset_final_ia.csv</code></p>
      <ul class="kpis">
        <li><strong>{len(df_ia):,}</strong><span>filas</span></li>
        <li><strong>{df_ia.shape[1]}</strong><span>columnas</span></li>
        <li><strong>{int(df_ia["target_derroche_next_hour"].sum())}</strong><span>positivos (derroche=1)</span></li>
        <li><strong>{(df_ia.isna().any(axis=1)).sum():,}</strong><span>filas con algún valor faltante</span></li>
      </ul>
      <div class="fig"><img src="data:image/png;base64,{b64_target}" alt="Target"/></div>
      <h3>Estadísticos (numéricos)</h3>
      {df_to_html_table(desc)}
      <h3>Valores faltantes por columna</h3>
      {df_to_html_table(missing_tbl)}
      {f'<div class="fig"><img src="data:image/png;base64,{b64_miss}" alt="Faltantes"/></div>' if b64_miss else '<p class="meta">Sin valores faltantes.</p>'}
    </div>

    <div class="card">
      {master_block if master_block.strip() else '<p class="meta">No se encontró master_dataset.csv o está vacío.</p>'}
    </div>

    <p class="meta">Para regenerar: <code>python scripts/generate_data_report.py</code></p>
  </div>
</body>
</html>
"""


def main() -> None:
    if not DATASET_IA.exists():
        raise FileNotFoundError(f"No existe {DATASET_IA}. Ejecuta antes el export / pipeline.")

    df_ia = pd.read_csv(DATASET_IA)
    for col in df_ia.columns:
        if col != "target_derroche_next_hour":
            df_ia[col] = pd.to_numeric(df_ia[col], errors="coerce")

    df_master = None
    if MASTER_FILE.exists():
        df_master = pd.read_csv(MASTER_FILE)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = build_html(df_ia, df_master, generated_at)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"OK informe: {OUT_HTML}")
    print(f"   Abre el archivo en el navegador (doble clic o arrastrar a Chrome/Edge).")


if __name__ == "__main__":
    main()
