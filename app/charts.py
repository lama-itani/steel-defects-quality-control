import json

import altair as alt
import pandas as pd

import ui


def _style(chart):
    return (
        chart.configure(background="transparent", font=ui.FONT)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=ui.MUTED, gridColor=ui.LINE, domainColor=ui.LINE,
            tickColor=ui.LINE, labelFontSize=12,
        )
        .configure_legend(
            labelColor=ui.INK, labelFontSize=12, symbolType="square",
        )
    )


def pareto_chart(rows):
    """rows: list of {"Class", "Images"} in the order to display."""
    df = pd.DataFrame(rows)
    base = alt.Chart(df).encode(
        x=alt.X(
            "Class:N", sort=None,
            axis=alt.Axis(title=None, labelAngle=0, labelLimit=110, grid=False),
        ),
        y=alt.Y(
            "Images:Q",
            axis=alt.Axis(title=None, tickMinStep=1, format="d", grid=True),
        ),
    )
    bars = base.mark_bar(
        color=ui.NAVY, size=32, cornerRadiusTopLeft=3, cornerRadiusTopRight=3,
    ).encode(tooltip=["Class:N", "Images:Q"])
    labels = base.mark_text(
        dy=-6, color=ui.INK, fontSize=12, fontWeight="bold",
    ).encode(text=alt.Text("Images:Q", format="d"))
    return _style((bars + labels).properties(height=240))


def stacked_hbar(rows, domain, colors, labels, text_colors=None, height=230):
    """rows: list of {"Class", <one count per name in domain>}."""
    text_colors = text_colors or ["#ffffff"] * len(domain)
    classes = [r["Class"] for r in rows]
    df = pd.DataFrame(rows).melt(
        id_vars="Class", value_vars=domain, var_name="Series", value_name="Count"
    )
    df["Order"] = df["Series"].map({k: i for i, k in enumerate(domain)})
    df["TextColor"] = df["Order"].map(dict(enumerate(text_colors)))
    df["Class"] = pd.Categorical(df["Class"], categories=classes, ordered=True)
    df = df.sort_values(["Class", "Order"]).reset_index(drop=True)
    df["End"] = df.groupby("Class", observed=True)["Count"].cumsum()
    df["Start"] = df["End"] - df["Count"]
    df["Mid"] = df["Start"] + df["Count"] / 2
    df["Class"] = df["Class"].astype(str)

    y = alt.Y(
        "Class:N", sort=classes,
        axis=alt.Axis(title=None, labelLimit=150, labelAngle=0),
    )
    legend_labels = f"{json.dumps(labels)}[datum.label]"
    bars = alt.Chart(df).mark_bar(size=22).encode(
        y=y,
        x=alt.X(
            "Start:Q",
            axis=alt.Axis(title=None, tickMinStep=1, format="d", grid=True),
        ),
        x2="End:Q",
        color=alt.Color(
            "Series:N",
            scale=alt.Scale(domain=domain, range=colors),
            legend=alt.Legend(
                orient="top", direction="horizontal", title=None,
                labelExpr=legend_labels,
            ),
        ),
        order=alt.Order("Order:Q"),
        tooltip=["Class:N", "Series:N", "Count:Q"],
    )
    text = alt.Chart(df[df["Count"] > 0]).mark_text(
        fontSize=12, fontWeight="bold",
    ).encode(
        y=y,
        x=alt.X("Mid:Q"),
        text=alt.Text("Count:Q", format="d"),
        color=alt.Color("TextColor:N", scale=None, legend=None),
    )
    chart = alt.layer(bars, text).resolve_scale(color="independent")
    return _style(chart.properties(height=height))
