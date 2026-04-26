import pandas as pd
import plotly.graph_objects as go

DELAY_CSV = "delay.csv"
CDA_CSV = "cda.csv"

def load_csvs():
    delay_df = pd.read_csv(DELAY_CSV)

    delay_df.columns = delay_df.columns.str.strip()

    print("Delay columns:", delay_df.columns.tolist())
    
    return delay_df


def plot_interactive_pt(delay_df, pt_col, valve_cols):
    delay_df["time_s"] = delay_df["time_s"] - delay_df["time_s"].iloc[0]
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=delay_df["time_s"],
        y=delay_df[pt_col],
        mode="lines+markers",
        name=pt_col,
        hovertemplate=
            "time: %{x:.6f}s<br>" +
            "pressure: %{y:.3f}<br>" +
            "<extra></extra>"
    ))

    # Add valve state change vertical lines
    for valve_col in valve_cols:
        prev_state = None

        for _, row in delay_df.iterrows():
            state = row[valve_col]

            if pd.isna(state) or state == "":
                continue

            if state != prev_state:
                fig.add_vline(
                    x=row["time_s"],
                    line_dash="dash",
                    annotation_text=f"{valve_col}: {state}",
                    annotation_position="top"
                )
                prev_state = state

    fig.update_layout(
        title=f"{pt_col} Over Time With Valve Changes",
        xaxis_title="Time (seconds)",
        yaxis_title="Pressure",
        hovermode="closest",
        template="plotly_white"
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=0.5,
        nticks=6,
        tickfont=dict(size=10),
        linewidth=1,
    )

    # normalize time

    fig.update_xaxes(
        nticks=20,
        tickformat=".3f",
        tickfont=dict(size=10)
    )

    fig.show()


def main():
    delay_df = load_csvs()

    pt_col = "pt NITROGEN_TANK_PT value"
    valve_cols = ["valve_0"]

    plot_interactive_pt(delay_df, pt_col, valve_cols)


if __name__ == "__main__":
    main()