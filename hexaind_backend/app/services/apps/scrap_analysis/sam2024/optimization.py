import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from matplotlib import pyplot as plt
from ortools.linear_solver import pywraplp


def prime_bars_interactive(
    filenames, scenario_names, furnace_names, units, plot1_path, plot2_path
):
    furnace_prime_list = []
    furnace_prime_frac_list = []

    for file in filenames:
        for furnace in furnace_names:
            df = pd.read_excel(file, index_col="Metal")
            furnace_prime_list.append(
                df.T.loc[:, f"Total prime content for {furnace}"].iloc[0]
            )
            furnace_prime_frac_list.append(
                df.T.loc[:, f"Total prime content for {furnace}"].iloc[0]
                / df.iloc[:-10].sum().sum()
            )

    total_prime_list = [sum(furnace_prime_list)]
    total_prime_frac_list = [sum(furnace_prime_frac_list)]

    prime_df = pd.DataFrame(
        {"Scenario": scenario_names, "Total Prime": total_prime_list}
    )

    prime_frac_df = pd.DataFrame(
        {
            "Scenario": scenario_names,
            "Total Prime (%)": np.array(total_prime_frac_list) * 100,
        }
    )

    # Colors
    alloy_color = "rgba(143,170,220,1)"  # Alloy prime color
    osw_color = "rgba(165,165,165,1)"  # Furnace prime color

    ## Plot 1: Prime Consumption (%) ##
    fig1 = go.Figure()

    fig1.add_trace(
        go.Bar(
            y=prime_frac_df["Scenario"],
            x=prime_frac_df["Total Prime (%)"],
            orientation="h",
            marker_color=osw_color,
            text=[f"{round(x, 1)}%" for x in prime_frac_df["Total Prime (%)"]],
            textposition="inside",
            hovertemplate="%{x:.1f}%",
            name="Total Prime (%)",  # Legend label
            showlegend=True,
        )
    )

    fig1.update_layout(
        title="Total Prime Consumption",
        xaxis_title="Primary Aluminum Usage (% of BOM)",
        yaxis_title="",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="lightgray"),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    ## Plot 2: Prime Consumption (units) ##
    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            y=prime_df["Scenario"],
            x=prime_df["Total Prime"],
            orientation="h",
            marker_color=alloy_color,
            text=[
                f"{format(int(x), ',')} ({round(total_prime_frac_list[0] * 100, 1)}%)"
                for x in prime_df["Total Prime"]
            ],
            textposition="inside",
            hovertemplate="%{x:,.0f}",
            name="Total Prime (units)",  # Legend label
            showlegend=True,
        )
    )

    fig2.update_layout(
        title="Total Prime Consumption",
        xaxis_title=f"Simulation Time Period Primary Aluminum Usage ({units})",
        yaxis_title="",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="lightgray", tickformat=","),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig1.write_html(plot1_path)
    plot1_path = plot1_path.replace(".html", ".json")
    fig1.write_json(plot1_path)
    plot1_path = plot1_path.replace(".json", ".png")
    fig1.write_image(plot1_path)
    fig2.write_html(plot2_path)
    plot2_path = plot2_path.replace(".html", ".json")
    fig2.write_json(plot2_path)
    plot2_path = plot2_path.replace(".json", ".png")
    fig2.write_image(plot2_path)


def alloy_bars_interactive(
    alloy_name: str,
    filenames: list[str],
    scenario_names: list[str],
    plot1_path: str,
    plot2_path: str,
    units: str = "lbs",
) -> None:
    # df = pd.DataFrame()
    # for i, file in enumerate(filenames):
    #     try:
    #         df[scenario_names[i]] = pd.read_excel(file, index_col='Metal', skipfooter=10).loc[:, alloy_name]
    #     except:
    #         print(f" \n Demand Alloy {alloy_name} not found in {file} \n")
    #         return
    # df = df.T

    df = pd.DataFrame()
    keywords = [
        "Required Supply",
        "Required Cast",
    ]  # Keywords indicating the start of unwanted rows
    for i, file in enumerate(filenames):
        df_temp = pd.read_excel(file)  # Read without forcing dtype

        # Find the first occurrence of unwanted rows
        drop_index = df_temp[
            df_temp.apply(
                lambda row: row.astype(str)
                .str.contains("|".join(keywords), na=False)
                .any(),
                axis=1,
            )
        ].index

        # If an unwanted row is found, trim data above the first occurrence
        if not drop_index.empty:
            df_temp = df_temp.loc[
                : drop_index[0] - 1
            ]  # Keep rows above the first match
        else:
            # Default case: Skip the last 14 rows if no match is found
            df_temp = pd.read_excel(file, index_col="Metal", skipfooter=14)

        # Ensure 'Metal' is set as the index
        df_temp = df_temp.set_index("Metal", drop=True)

        # Convert numeric columns back to proper data types
        df_temp = df_temp.apply(pd.to_numeric, errors="ignore")

        # Add data to the main DataFrame
        df[scenario_names[i]] = df_temp.loc[:, alloy_name]

    df = df.T

    # Extract column metadata
    column_alloy = np.empty_like(df.columns.to_numpy())
    column_source = np.empty_like(df.columns.to_numpy())

    for i, scrap in enumerate(np.char.split(df.columns.to_numpy(str), " - ")):
        column_alloy[i] = scrap[0]
        try:
            column_source[i] = scrap[1]
        except:
            column_source[i] = "PRIME"

    df.columns = pd.MultiIndex.from_tuples(zip(column_source, column_alloy))
    unique_sources = sorted(set(column_source))  # Get all unique sources

    # Source Grouping and Ordering Logic
    source_list = np.unique([col[0] for col in df.columns.to_numpy()])

    # Define masks
    prime_mask = np.array(["prime" in source.lower() for source in source_list])
    purchase_mask = np.array(
        [
            "purchase" in source.lower() or "third" in source.lower()
            for source in source_list
        ]
    ) * np.logical_not(prime_mask)
    rar_mask = np.array(
        ["rar" in source.lower() for source in source_list]
    ) * np.logical_not(prime_mask + purchase_mask)
    recycling_mask = np.array(
        [
            "clr" in source.lower() or "recycl" in source.lower()
            for source in source_list
        ]
    ) * np.logical_not(prime_mask + purchase_mask + rar_mask)
    other_mask = np.logical_not(prime_mask + rar_mask + purchase_mask + recycling_mask)

    # Sort sources
    source_list_sorted = np.concatenate(
        (
            source_list[prime_mask],
            source_list[rar_mask],
            source_list[other_mask],
            source_list[recycling_mask],
            source_list[purchase_mask],
        )
    )

    df = df[source_list_sorted]
    # Reorder masks for sorted list
    prime_mask = np.array(["prime" in source.lower() for source in source_list_sorted])
    purchase_mask = np.array(
        [
            "purchase" in source.lower() or "third" in source.lower()
            for source in source_list_sorted
        ]
    ) * np.logical_not(prime_mask)
    rar_mask = np.array(
        ["rar" in source.lower() for source in source_list_sorted]
    ) * np.logical_not(prime_mask + purchase_mask)
    recycling_mask = np.array(
        [
            "clr" in source.lower() or "recycl" in source.lower()
            for source in source_list_sorted
        ]
    ) * np.logical_not(prime_mask + purchase_mask + rar_mask)
    other_mask = np.logical_not(prime_mask + rar_mask + purchase_mask + recycling_mask)

    # Color Definitions
    prime_reds = np.divide(
        np.linspace([202, 22, 38, 255], [129, 14, 24, 255], sum(prime_mask)), 255
    )
    rar_blues = np.divide(
        np.linspace([12, 38, 90, 255], [0, 117, 255, 255], sum(rar_mask)), 255
    )
    other_greys = np.divide(
        np.linspace([89, 89, 89, 255], [191, 197, 197, 255], sum(other_mask)), 255
    )
    recycle_greens = np.divide(
        np.linspace([0, 61, 31, 255], [55, 184, 92, 255], sum(recycling_mask)), 255
    )
    purchase_limes = np.divide(
        np.linspace([161, 221, 0, 255], [186, 238, 46, 255], sum(purchase_mask)), 255
    )

    color_list = np.concatenate(
        (prime_reds, rar_blues, other_greys, recycle_greens, purchase_limes)
    )

    def default_color_assign(df):
        full_color_list = np.empty_like(
            df.columns.to_numpy(), dtype=object
        )  # Changed to dtype=object to hold arrays
        column_source = np.array([cols[0] for cols in df.columns])

        for i, source in enumerate(column_source):
            if any(np.isin(source_list_sorted[prime_mask], source)):
                full_color_list[i] = prime_reds[
                    np.argwhere(source == source_list_sorted[prime_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[rar_mask], source)):
                full_color_list[i] = rar_blues[
                    np.argwhere(source == source_list_sorted[rar_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[recycling_mask], source)):
                full_color_list[i] = recycle_greens[
                    np.argwhere(source == source_list_sorted[recycling_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[purchase_mask], source)):
                full_color_list[i] = purchase_limes[
                    np.argwhere(source == source_list_sorted[purchase_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[other_mask], source)):
                full_color_list[i] = other_greys[
                    np.argwhere(source == source_list_sorted[other_mask])
                ].flatten()
            else:
                full_color_list[i] = np.array([0.5, 0.5, 0.5, 1])
                print("Unknown Source Encountered")
        return full_color_list

    colors = default_color_assign(df)

    # Normalize data for percentage plot
    percent_df = 100 * df.divide(df.sum(1).to_numpy(), axis=0)

    # 📊 Create figure for percentage plot
    fig_percent = go.Figure()
    added_sources = set()  # Track which sources are added to the legend

    for i, (source, alloy) in enumerate(df.columns):
        show_legend = source not in added_sources  # Show legend only once per source
        added_sources.add(source)

        fig_percent.add_trace(
            go.Bar(
                y=percent_df.index,
                x=percent_df[(source, alloy)],
                name=source,  # Only source name in legend.
                hovertemplate=f"Alloy: {alloy}<br>% of Recipe: %{{x:.1f}} <br>Source: {source} <extra></extra>",
                orientation="h",
                text=[
                    f"<b>{alloy}</b>\n{v:.1f}%" if v > 1 else ""
                    for v in percent_df[(source, alloy)]
                ],
                textposition="inside",
                marker_color=f"rgba({colors[i][0]*255},{colors[i][1]*255},{colors[i][2]*255},{colors[i][3]})",  # Use assigned color
                showlegend=show_legend,  # Show legend only once per source
            )
        )

    fig_percent.update_layout(
        title=dict(
            text=f"<b>{alloy_name} Fractional BOM</b>",  # Bold title
            x=0.5,  # Centered title
            xanchor="center",
        ),
        barmode="stack",
        xaxis=dict(
            title="Alloy Inputs (% of Recipe)",
            linecolor="black",
            linewidth=1,
            mirror=True,
            dtick=10,
        ),
        yaxis_title="",
        legend_title="<b>Source</b>",  # Bold legend title
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            traceorder="normal",
        ),
        margin=dict(l=50, r=50, t=50, b=100),  # Proper margins
        plot_bgcolor="white",  # White background
        paper_bgcolor="white",  # White outer background
        yaxis=dict(linecolor="black", linewidth=1, mirror=True),  # Box border on Y-axis
    )

    # 📊 Create figure for weight plot
    fig_weight = go.Figure()
    added_sources.clear()  # Reset for second plot
    for i, (source, alloy) in enumerate(df.columns):
        show_legend = source not in added_sources  # Show legend only once per source
        added_sources.add(source)

        fig_weight.add_trace(
            go.Bar(
                y=df.index,
                x=df[(source, alloy)],
                name=source,  # Only source name in legend
                hovertemplate=f"Alloy: {alloy}<br>Weight: %{{x:,}} {units}<br>Source: {source} <extra></extra>",
                orientation="h",
                text=[
                    f"<b>{alloy}</b>\n{int(v):,}" if v > 1 else ""
                    for v in df[(source, alloy)]
                ],
                textposition="inside",
                marker_color=f"rgba({colors[i][0]*255},{colors[i][1]*255},{colors[i][2]*255},{colors[i][3]})",  # Use assigned color
                showlegend=show_legend,  # Show legend only once per source
            )
        )

    fig_weight.update_layout(
        title=dict(
            text=f"<b>{alloy_name} BOM (Weight)</b>",  # Bold title
            x=0.5,  # Centered title
            xanchor="center",
        ),
        barmode="stack",
        xaxis=dict(
            title=f"Alloy Inputs ({units})", linecolor="black", linewidth=1, mirror=True
        ),
        yaxis_title="",
        legend_title="<b>Source</b>",  # Bold legend title
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            traceorder="normal",
        ),
        margin=dict(l=50, r=50, t=50, b=100),  # Proper margins
        plot_bgcolor="white",  # White background
        paper_bgcolor="white",  # White outer background
        yaxis=dict(linecolor="black", linewidth=1, mirror=True),  # Box border on Y-axis
    )

    fig_percent.write_html(plot1_path)
    plot1_path = plot1_path.replace(".html", ".json")
    fig_percent.write_json(plot1_path)
    plot1_path = plot1_path.replace(".json", ".png")
    fig_percent.write_image(plot1_path)
    fig_weight.write_html(plot2_path)
    plot2_path = plot2_path.replace(".html", ".json")
    fig_weight.write_json(plot2_path)
    plot2_path = plot2_path.replace(".json", ".png")
    fig_weight.write_image(plot2_path)


def alloy_bars(
    alloy_name: str,
    filenames: list[str],
    scenario_names: list[str],
    plot1_path: str,
    plot2_path: str,
    units: str = "lbs",
) -> None:
    """
    Generates and saves two bar plots for alloy composition:
    1. Fractional BOM (percentage-based composition)
    2. BOM (weight-based composition)

    Args:
        alloy_name (str): Name of the alloy to analyze.
        filenames (list[str]): List of Excel file paths containing alloy data.
        scenario_names (list[str]): List of scenario names corresponding to the files.
        plot1_path (str): File path to save the fractional BOM plot.
        plot2_path (str): File path to save the weight BOM plot.
        units (str, optional): Units for weight representation. Defaults to 'lbs'.

    Returns:
        None
    """
    df = pd.DataFrame()
    for i, file in enumerate(filenames):
        df[scenario_names[i]] = pd.read_excel(
            file, index_col="Metal", skipfooter=10
        ).loc[:, alloy_name]
    df = df.T

    column_alloy = np.empty_like(df.columns.to_numpy())
    column_source = np.empty_like(df.columns.to_numpy())
    for i, scrap in enumerate(np.char.split(df.columns.to_numpy(str), " - ")):
        column_alloy[i] = scrap[0]
        try:
            column_source[i] = scrap[1]
        except:
            column_source[i] = "PRIME"

    multi_columns = [column_source, column_alloy]
    df.columns = multi_columns

    # 1D list of all sources in df
    source_list = np.unique([col[0] for col in df.columns.to_numpy()])

    # Masks for different categories
    prime_mask = np.array(["prime" in source.lower() for source in source_list])
    purchase_mask = (
        np.array(["purchase" in source.lower() for source in source_list])
        | np.array(["third" in source.lower() for source in source_list]) & ~prime_mask
    )
    rar_mask = np.array(["rar" in source.lower() for source in source_list]) & ~(
        prime_mask | purchase_mask
    )
    recycling_mask = np.array(
        ["clr" in source.lower() for source in source_list]
    ) | np.array(["recycl" in source.lower() for source in source_list]) & ~(
        prime_mask | purchase_mask | rar_mask
    )
    other_mask = ~(prime_mask | rar_mask | purchase_mask | recycling_mask)

    # Sorted order for plotting
    source_list_sorted = np.concatenate(
        (
            source_list[prime_mask],
            source_list[rar_mask],
            source_list[other_mask],
            source_list[recycling_mask],
            source_list[purchase_mask],
        )
    )

    df = df[source_list_sorted]
    alloy_labels = np.array([cols[1] for cols in df.columns])

    # Defining colors
    prime_reds = np.divide(
        np.linspace([202, 22, 38, 255], [129, 14, 24, 255], sum(prime_mask)), 255
    )
    rar_blues = np.divide(
        np.linspace([12, 38, 90, 255], [0, 117, 255, 255], sum(rar_mask)), 255
    )
    other_greys = np.divide(
        np.linspace([89, 89, 89, 255], [191, 197, 197, 255], sum(other_mask)), 255
    )
    recycle_greens = np.divide(
        np.linspace([0, 61, 31, 255], [55, 184, 92, 255], sum(recycling_mask)), 255
    )
    purchase_limes = np.divide(
        np.linspace([161, 221, 0, 255], [186, 238, 46, 255], sum(purchase_mask)), 255
    )

    color_list = np.concatenate(
        (prime_reds, rar_blues, other_greys, recycle_greens, purchase_limes)
    )

    def default_color_assign(df):
        full_color_list = np.empty_like(df.columns.to_numpy(), dtype=object)
        column_source = np.array([cols[0] for cols in df.columns])

        for i, source in enumerate(column_source):
            if any(np.isin(source_list_sorted[prime_mask], source)):
                full_color_list[i] = prime_reds[
                    np.argwhere(source == source_list_sorted[prime_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[rar_mask], source)):
                full_color_list[i] = rar_blues[
                    np.argwhere(source == source_list_sorted[rar_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[recycling_mask], source)):
                full_color_list[i] = recycle_greens[
                    np.argwhere(source == source_list_sorted[recycling_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[purchase_mask], source)):
                full_color_list[i] = purchase_limes[
                    np.argwhere(source == source_list_sorted[purchase_mask])
                ].flatten()
            elif any(np.isin(source_list_sorted[other_mask], source)):
                full_color_list[i] = other_greys[
                    np.argwhere(source == source_list_sorted[other_mask])
                ].flatten()
            else:
                full_color_list[i] = np.array([0.5, 0.5, 0.5, 1])
                print("Unknown Source Encountered")
        return full_color_list

    colors = default_color_assign(df)
    percent_df = 100 * df.divide(df.sum(1).to_numpy(), axis=0)
    custom_lines = [Line2D([0], [0], color=c, lw=4) for c in color_list]

    # Percentage Plot
    _, ax = plt.subplots(figsize=(18, 6))
    plot = percent_df.loc[percent_df.sum(axis=1) > 0].plot.barh(
        stacked=True,
        color=colors,
        ax=ax,
        xlabel="Alloy Inputs (% of Recipe)",
        ylabel="",
        legend=None,
        edgecolor="white",
    )

    for i, c in enumerate(plot.containers):
        labels = [
            (
                f"{alloy_labels[i]}\n{np.round(v.get_width(),1)}%"
                if v.get_width() > 1
                else ""
            )
            for v in c
        ]
        plot.bar_label(c, labels=labels, label_type="center", color="white")

    ax.set_title(f"{alloy_name} Fractional BOM")
    ax.set_yticklabels(percent_df.index)
    ax.legend(custom_lines, source_list_sorted)
    plt.savefig(plot1_path, bbox_inches="tight", dpi=300)
    plt.close()

    # Weight Plot
    _, ax = plt.subplots(figsize=(18, 6))
    plot = df.loc[df.sum(axis=1) > 0].plot.barh(
        stacked=True,
        color=colors,
        ax=ax,
        xlabel=f"Alloy Inputs ({units})",
        ylabel="",
        legend=None,
        edgecolor="white",
    )

    total_weights = df.loc[df.sum(axis=1) > 0].sum(axis=1).to_numpy()
    for i, c in enumerate(plot.containers):
        labels = [
            (
                "%s\n%s" % (alloy_labels[i], format(int(v.get_width()), ","))
                if 100 * v.get_width() / total_weights[j] > 1
                else ""
            )
            for j, v in enumerate(c)
        ]
        plot.bar_label(c, labels=labels, label_type="center", color="white")
    ax.set_title(f"{alloy_name} BOM (Weight)")
    ax.set_yticklabels(df.index)
    ax.legend(custom_lines, source_list_sorted)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: format(int(x), ",")))
    plt.savefig(plot2_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Plots saved:\n - {plot1_path}\n - {plot2_path}")


def solve(
    scrap_flow_dict,
    plant_dict,
    transportation_dict,
    limits_df,
    furnace,
    logger,
    optimize_cost=False,
    input_filename=None,
    MG_BURNOFF=None,
    EXTERNAL_SCRAP_SOURCES=None,
    OPTIMIZE_CASTING=None,
    MOLTEN_MINIMUM=None,
):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver_parameters = pywraplp.MPSolverParameters()
    solver_parameters.SetDoubleParam(
        pywraplp.MPSolverParameters.PRIMAL_TOLERANCE, 0.001
    )

    if not solver:
        logger.critical("No solver found")
        raise Exception("No solver found")
        # exit(1)

    # ----------------------- Decision variables ---------------------------

    supplier_list = []
    for lst in scrap_flow_dict.values():
        for sp in lst:
            if sp not in supplier_list:
                supplier_list.append(sp)
    destination_list = list(scrap_flow_dict.keys())

    x = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for i in range(len(scrap_flow_dict[destination])):
            supplier = scrap_flow_dict[destination][i]
            material_list = plant_dict.get(supplier).list_material_supply
            for m in range(len(material_list)):
                for a in range(len(alloy_list)):
                    varname = f"x[{supplier}][{destination}][{material_list[m]}][{alloy_list[a]}]"
                    x[(i, j, m, a)] = solver.NumVar(0, solver.Infinity(), varname)

    prime = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            varname = f"prime[{destination}][{alloy_list[a]}]"
            prime[(j, a)] = solver.NumVar(0, solver.Infinity(), varname)

    y = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        form_list = plant_dict.get(destination).list_form
        for f in range(len(form_list)):
            varname = f"y[{destination}][{form_list[f]}]"
            y[(j, f)] = solver.NumVar(0, solver.Infinity(), varname)

    z = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            varname = f"z[{destination}][{alloy_list[a]}]"
            z[(j, a)] = solver.NumVar(0, solver.Infinity(), varname)

    b = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for i in range(len(scrap_flow_dict[destination])):
            supplier = scrap_flow_dict[destination][i]
            material_list = plant_dict.get(supplier).list_material_supply
            for m in range(len(material_list)):
                for a in range(len(alloy_list)):
                    varname = f"b[{supplier}][{destination}][{material_list[m]}][{alloy_list[a]}]"
                    b[(i, j, m, a)] = solver.IntVar(0, 1, varname)

    target_alloy_amount = {}
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            alloy = alloy_list[a]
            varname = f"target_alloy_amount[{destination}][{alloy}]"
            target_alloy_amount[(j, a)] = solver.NumVar(0, solver.Infinity(), varname)

            scrap_rate = float(plant_dict.get(destination).dict_scrap_rate.get(alloy))
            supply = float(
                plant_dict.get(destination).dict_supply.get(alloy) / (1 - scrap_rate)
            )

    # ----------------------- Constraints ----------------------------------

    # Auxiliary constraint: link decision variables z with x
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            ct = solver.Constraint(
                0, 0, f"auxlink_z_to_x_{destination}_{alloy_list[a]}"
            )
            ct.SetCoefficient(z[(j, a)], -1)
            for i in range(len(scrap_flow_dict[destination])):
                plant = plant_dict.get(scrap_flow_dict[destination][i])
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    ct.SetCoefficient(x[(i, j, m, a)], 1)

    # Auxiliary constraint: link decision variables y with x
    for j in range(len(destination_list)):
        destination = destination_list[j]
        form_list = plant_dict.get(destination).list_form
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for f in range(len(form_list)):
            ct = solver.Constraint(0, 0, f"auxlink_y_to_x_{destination}_{form_list[f]}")
            ct.SetCoefficient(y[(j, f)], -1)
            for i in range(len(scrap_flow_dict[destination])):
                plant = plant_dict.get(scrap_flow_dict[destination][i])
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    if (
                        plant.dict_material_supply.get(material_list[m]).form
                        == form_list[f]
                    ):
                        for a in range(len(alloy_list)):
                            ct.SetCoefficient(x[(i, j, m, a)], 1)

    # Enforce maximum percent of each scrap allowed in alloy
    if limits_df is not None:
        for j in range(len(destination_list)):
            destination = destination_list[j]
            alloy_list = plant_dict.get(destination).list_alloys_demand
            for a in range(len(alloy_list)):
                # add constraint for individual scraps
                for i in range(len(scrap_flow_dict[destination])):
                    plant = plant_dict.get(scrap_flow_dict[destination][i])
                    material_list = plant.list_material_supply
                    for m in range(len(material_list)):
                        material = material_list[m]
                        try:  # try to parse alloy column as string first
                            limit = limits_df[
                                (limits_df["Plant"] == scrap_flow_dict[destination][i])
                                & (limits_df["Alloy"].astype(str) == str(material))
                            ][str(alloy_list[a])].iloc[0]
                        except KeyError:  # if that fails, parse it as an int
                            limit = limits_df[
                                (limits_df["Plant"] == scrap_flow_dict[destination][i])
                                & (limits_df["Alloy"].astype(str) == str(material))
                            ][int(alloy_list[a])].iloc[0]
                        if limit < 1:
                            max_amt = float(
                                plant_dict.get(destination).dict_supply[alloy_list[a]]
                            )
                            solver.Add(x[(i, j, m, a)] <= max_amt * limit)
                # add constraint for prime usage
                if len(limits_df[limits_df["Alloy"] == "Prime"]) > 0:
                    try:  # try to parse alloy column as string first
                        limit = limits_df[(limits_df["Alloy"].astype(str) == "Prime")][
                            str(alloy_list[a])
                        ].iloc[0]
                    except KeyError:  # if that fails, parse it as an int
                        limit = limits_df[(limits_df["Alloy"].astype(str) == "Prime")][
                            int(alloy_list[a])
                        ].iloc[0]
                    if limit < 1:
                        max_amt = float(
                            plant_dict.get(destination).dict_supply[alloy_list[a]]
                        )
                        solver.Add(prime[(j, a)] <= max_amt * limit)

    # Link target alloy amount decision variable to input
    if OPTIMIZE_CASTING:
        for j in range(len(destination_list)):
            destination = destination_list[j]
            alloy_list = plant_dict.get(destination).list_alloys_demand
            total_supply = 0
            for a in range(len(alloy_list)):
                alloy = alloy_list[a]
                scrap_rate = float(
                    plant_dict.get(destination).dict_scrap_rate.get(alloy)
                )
                supply = float(
                    plant_dict.get(destination).dict_supply.get(alloy)
                    / (1 - scrap_rate)
                )
                total_supply += supply
                # minimum and maximum constraint
                try:
                    minimum = float(
                        plant_dict.get(destination).dict_supply_minimum.get(alloy)
                        / (1 - scrap_rate)
                    )
                except TypeError:
                    minimum = 0
                if (minimum > supply) or (np.isnan(minimum)):
                    minimum = 0
                try:
                    maximum = float(
                        plant_dict.get(destination).dict_supply_maximum.get(alloy)
                        / (1 - scrap_rate)
                    )
                except TypeError:
                    maximum = solver.Infinity()
                if np.isnan(maximum):
                    maximum = solver.Infinity()
                ct = solver.Constraint(
                    minimum, maximum, f"target_alloy_amount_{destination}_{alloy}"
                )
                ct.SetCoefficient(target_alloy_amount[(j, a)], 1)
            ct = solver.Constraint(
                total_supply, total_supply, f"total_target_alloy_amount_{destination}"
            )
            for a in range(len(alloy_list)):
                alloy = alloy_list[a]
                scrap_rate = float(
                    plant_dict.get(destination).dict_scrap_rate.get(alloy)
                )
                ct.SetCoefficient(target_alloy_amount[(j, a)], 1)
    else:
        for j in range(len(destination_list)):
            destination = destination_list[j]
            alloy_list = plant_dict.get(destination).list_alloys_demand
            for a in range(len(alloy_list)):
                alloy = alloy_list[a]
                scrap_rate = float(
                    plant_dict.get(destination).dict_scrap_rate.get(alloy)
                )
                supply = float(
                    plant_dict.get(destination).dict_supply.get(alloy)
                    / (1 - scrap_rate)
                )
                ct = solver.Constraint(
                    supply, supply, f"target_alloy_amount_{destination}_{alloy}"
                )
                ct.SetCoefficient(target_alloy_amount[(j, a)], 1)

    # Mass balance system - this makes sure you cast the right amount of the target alloys
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            alloy = alloy_list[a]
            ct = solver.Constraint(0, 0, f"mass_bal_sys_{destination}_{alloy}")
            ct.SetCoefficient(target_alloy_amount[(j, a)], -1)
            ct.SetCoefficient(
                prime[(j, a)], float(plant_dict.get(destination).prime.recovery)
            )
            for i in range(len(scrap_flow_dict[destination])):
                plant = plant_dict.get(scrap_flow_dict[destination][i])
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    recovery = float(
                        plant.dict_material_supply.get(material_list[m]).recovery
                    )
                    ct.SetCoefficient(x[(i, j, m, a)], recovery)

    # Recycle capacity
    for j in range(len(destination_list)):
        destination = destination_list[j]
        plant = plant_dict.get(destination)
        form_list = plant.list_form
        for f in range(len(form_list)):
            form = form_list[f]
            minimum = plant.dict_form_capacity.get(form)[0]
            capacity = plant.dict_form_capacity.get(form)[1]
            if capacity is not None:
                ct_name = f"capacity_{destination}_{form}"
                ct = solver.Constraint(float(minimum), float(capacity), ct_name)
                ct.SetCoefficient(y[(j, f)], 1)

    # At most one recycle alloy per cast alloy
    # Somewhat unnecessary right now, effectively replaced by the maximum percentage constraint
    # Original purpose was to avoid cases where a small amount of one recycled input was used (not reasonable to transport )

    ############## --- Commented out for Nachterstedt
    # for j in range(len(destination_list)):
    #    destination = destination_list[j]
    #    alloy_list = plant_dict.get(destination).list_alloys_demand
    #    form_list = plant_dict.get(destination).list_form
    #    if len(form_list) > 0:
    #        for i in range(len(scrap_flow_dict[destination])):
    #            plant = plant_dict.get(scrap_flow_dict[destination][i])
    #            material_list = [m for m in plant.list_material_supply
    #                             if plant.dict_material_supply.get(m).form in form_list]
    #            if len(material_list) > 0:
    #                for a in range(len(alloy_list)):
    #                    solver.Add(solver.Sum(b[(i, j, m, a)] for m in range(len(material_list))) <= 1)
    #                    for m in range(len(material_list)):
    #                        material = material_list[m]
    #                        max_amt = float(plant.dict_material_supply.get(material).amount_available)
    #                        solver.Add(x[(i, j, m, a)] <= max_amt * b[(i, j, m, a)])
    ################## -------------

    # Mass balance stream - this makes sure you don't use more than the available supply
    for i in range(len(supplier_list)):
        supplier = supplier_list[i]
        plant = plant_dict.get(supplier)
        material_list = plant.list_material_supply
        for m in range(len(material_list)):
            material = material_list[m]
            min_amt = float(plant.dict_material_supply.get(material).min_amount)
            max_amt = float(plant.dict_material_supply.get(material).amount_available)
            ct = solver.Constraint(
                min_amt, max_amt, f"mass_bal_strm_{supplier}_{material}"
            )
            for j in range(len(destination_list)):
                destination = destination_list[j]
                if supplier in scrap_flow_dict[destination]:
                    alloy_list = plant_dict.get(destination).list_alloys_demand
                    i = scrap_flow_dict[destination].index(supplier)
                    for a in range(len(alloy_list)):
                        ct.SetCoefficient(x[(i, j, m, a)], 1)

    # Chemical concentration
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            alloy = plant_dict.get(destination).dict_alloys_demand.get(alloy_list[a])
            chem_list = alloy.list_elements
            for c in range(len(chem_list)):
                elem = chem_list[c]
                max_amt = alloy.dict_chemistry.get(elem)
                prime_coef = plant_dict.get(destination).prime.dict_chemistry.get(elem)
                ct_name = f"chem_{destination}_{alloy_list[a]}_{elem}"
                ct = solver.Constraint(0, solver.Infinity(), ct_name)
                ct.SetCoefficient(z[(j, a)], max_amt)
                ct.SetCoefficient(prime[(j, a)], max_amt - prime_coef)
                for i in range(len(scrap_flow_dict[destination])):
                    plant = plant_dict.get(scrap_flow_dict[destination][i])
                    material_list = plant.list_material_supply
                    for m in range(len(material_list)):
                        material = material_list[m]
                        x_coef = plant.dict_material_supply.get(
                            material
                        ).dict_chemistry.get(elem)
                        if elem == "Mg":
                            x_coef *= 1 - MG_BURNOFF
                        ct.SetCoefficient(x[(i, j, m, a)], -1 * x_coef)

    # Molten Metal Minimum
    for j in range(len(destination_list)):
        destination = destination_list[j]
        if "Recycle" in scrap_flow_dict[destination]:
            supplier = "Recycle"
            alloy_list = plant_dict.get(destination).list_alloys_demand
            material_list = plant_dict.get(supplier).list_material_supply
            for a in range(len(alloy_list)):
                alloy_name = alloy_list[a]
                # print(plant_dict.get(destination).dict_alloys_demand.get(alloy_name))
                ct_name = f"molten_minimum_{destination}_{alloy_name}"
                ct = solver.Constraint(0, solver.Infinity(), ct_name)
                # TODO - find the demand for this alloy
                ct.SetCoefficient(z[(j, a)], -MOLTEN_MINIMUM)
                for m in range(len(material_list)):
                    # varname = f"x[{supplier}][{destination}][{material_list[m]}][{alloy_list[a]}]"
                    ct.SetCoefficient(x[(i, j, m, a)], 1)

    # ----------------------- Objective function ---------------------------

    obj = solver.Objective()
    # Transportation cost
    for i in range(len(supplier_list)):
        supplier = supplier_list[i]
        material_list = plant_dict.get(supplier).list_material_supply
        for j in range(len(destination_list)):
            destination = destination_list[j]
            if supplier in scrap_flow_dict[destination]:
                plant_pair_str = f"{supplier}-{destination}"
                if transportation_dict.get(plant_pair_str) is None:
                    continue
                cost = float(transportation_dict.get(plant_pair_str))
                alloy_list = plant_dict.get(destination).list_alloys_demand
                i = scrap_flow_dict[destination].index(supplier)
                for m in range(len(material_list)):
                    for a in range(len(alloy_list)):
                        obj.SetCoefficient(x[(i, j, m, a)], cost)

    if optimize_cost:
        cost_optimized = True
        try:
            ct = 0
            failed = 0
            # Cost minimization for scrap
            for j in range(len(destination_list)):
                destination = destination_list[j]
                alloy_list = plant_dict.get(destination).list_alloys_demand
                for i in range(len(scrap_flow_dict[destination])):
                    supplier = scrap_flow_dict[destination][i]
                    material_list = plant_dict.get(supplier).list_material_supply
                    for m in range(len(material_list)):
                        plant = plant_dict.get(scrap_flow_dict[destination][i])
                        material = material_list[m]
                        ct += 1
                        if plant.dict_material_supply.get(material) is None:
                            material_cost = 100
                            failed += 1
                        else:
                            material_cost = float(
                                plant.dict_material_supply.get(material).cost
                            )
                        for a in range(len(alloy_list)):
                            obj.SetCoefficient(x[(i, j, m, a)], material_cost)
            # Cost minimization for prime
            for j in range(len(destination_list)):
                alloy_list = plant_dict.get(destination_list[j]).list_alloys_demand
                prime_cost = plant_dict.get(destination_list[j]).prime.cost
                if prime_cost is None:
                    prime_cost = 1
                if np.isnan(prime_cost):
                    prime_cost = 1
                for a in range(len(alloy_list)):
                    obj.SetCoefficient(prime[(j, a)], prime_cost)
            if failed > 0:
                print(
                    f"{failed} / {ct} of scrap material costs failed to be read, set to 100 cost"
                )
        except TypeError:
            obj.Clear()
            print("Missing cost data, optimizing prime usage instead")
            cost_optimized = False
    if (not optimize_cost) or (not cost_optimized):
        # Prime minimization
        for j in range(len(destination_list)):
            alloy_list = plant_dict.get(destination_list[j]).list_alloys_demand
            for a in range(len(alloy_list)):
                obj.SetCoefficient(prime[(j, a)], 1)

    obj.SetMinimization()

    status = solver.Solve(solver_parameters)
    # print(status)
    # print(pywraplp.Solver.INFEASIBLE)
    # print(solver.VerifySolution(0.001, True))
    if status == pywraplp.Solver.OPTIMAL:
        logger.info(f"Optimal solution for {furnace}: {obj.Value()}")
        logger.info(f"Solution time: {solver.wall_time() / 1000} seconds")
        output_filename = write_output(
            scrap_flow_dict,
            destination_list,
            supplier_list,
            plant_dict,
            x,
            prime,
            z,
            target_alloy_amount,
            furnace,
            input_filename,
            EXTERNAL_SCRAP_SOURCES=EXTERNAL_SCRAP_SOURCES,
        )
        return output_filename
    else:
        logger.critical(f"No optimal solution found for {furnace}")
        raise Exception(f"No optimal solution found for {furnace}")
        # exit(1)


def write_output(
    scrap_flow_dict,
    destination_list,
    supplier_list,
    plant_dict,
    x,
    prime,
    z,
    target_alloy_amount,
    furnace,
    input_filename=None,
    EXTERNAL_SCRAP_SOURCES=None,
):
    if input_filename:
        filename = input_filename[:-5] + "_output.xlsx"
    else:
        filename = "JanuaryThruApril2024_Output_Actuals_modified"

    # Initialize logging with handlers for output txt file and console
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(message)s",
    #     handlers=[
    #         logging.FileHandler(f"{filename}.txt", mode='a'),
    #         logging.StreamHandler(sys.stdout)
    #     ]
    # )

    tot_prime = np.zeros(len(destination_list))
    tot_ext = np.zeros(len(destination_list))
    tot_melt = np.zeros(len(destination_list))
    for j in range(len(destination_list)):
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            prime_sol = abs(prime[(j, a)].solution_value())
            scrap_rate = plant_dict.get(destination).dict_scrap_rate.get(alloy_list[a])
            tot_prime[j] += prime_sol
            tot_melt[j] += prime_sol * (1 - scrap_rate)
            for i in range(len(scrap_flow_dict[destination])):
                supplier = scrap_flow_dict[destination][i]
                plant = plant_dict.get(supplier)
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    material = material_list[m]
                    x_sol = x[(i, j, m, a)].solution_value()
                    if x_sol > 0:
                        recovery = plant.dict_material_supply.get(material).recovery
                        tot_melt[j] += x_sol * recovery * (1 - scrap_rate)
                        if supplier in EXTERNAL_SCRAP_SOURCES:
                            tot_ext[j] += x_sol * recovery

    chem_output_dict = dict()
    bom_dict = dict()
    bom_info_dict = dict()
    plant_info_dict = dict()
    tot_cost = np.zeros(len(destination_list))
    for j in range(len(destination_list)):
        destination = destination_list[j]
        # logging.info(f"\nOutput for plant {destination}\n")
        alloy_list = plant_dict.get(destination).list_alloys_demand
        rc = np.zeros(len(alloy_list))
        for a in range(len(alloy_list)):
            alloy_nm = alloy_list[a]
            supply = plant_dict.get(destination).dict_supply.get(alloy_nm)
            scrap_rate = plant_dict.get(destination).dict_scrap_rate.get(alloy_nm)
            amt = (
                plant_dict.get(destination)
                .dict_material_supply.get(alloy_nm)
                .amount_available
            )
            tot_cast = supply + amt
            prime_sol = abs(prime[(j, a)].solution_value())
            # logging.info(str(alloy_nm))
            tot_sent = z[(j, a)].solution_value() + prime_sol
            tot_cast = target_alloy_amount[(j, a)].solution_value()
            # logging.info(f"Required Supply: {round(supply)}")
            # logging.info(f"Required Cast: {round(tot_cast)}")
            bom_info_dict[alloy_nm] = {
                "Required Supply": round(tot_sent),
                "Required Cast": round(tot_cast),
            }
            alloy = plant_dict.get(destination).dict_alloys_demand.get(alloy_nm)
            chem_list = alloy.list_elements
            els = {}
            for c in range(len(chem_list)):
                elem = chem_list[c]
                chem = plant_dict.get(destination).prime.dict_chemistry.get(elem)
                els.update({elem: prime_sol * chem})
            for i in range(len(scrap_flow_dict[destination])):
                supplier = scrap_flow_dict[destination][i]
                plant = plant_dict.get(supplier)
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    material = material_list[m]
                    x_sol = x[(i, j, m, a)].solution_value()
                    for c in range(len(chem_list)):
                        elem = chem_list[c]
                        chem = plant.dict_material_supply.get(
                            material
                        ).dict_chemistry.get(elem)
                        els.update({elem: els.get(elem) + x_sol * chem})
            # logging.info(f"\n{destination} Limit")
            # logging.info("\t".join(chem_list).expandtabs(10))
            # logging.info("\t".join("%.4f" % alloy.dict_chemistry.get(elem) for elem in chem_list).expandtabs(10))
            chem_output_dict[(alloy_nm, "Limit")] = {
                elem: round(alloy.dict_chemistry.get(elem), 4) for elem in chem_list
            }
            # logging.info("Remelt")
            # logging.info("\t".join(chem_list).expandtabs(10))
            # logging.info("\t".join("%.4f" % (els.get(elem) / tot_sent) for elem in chem_list).expandtabs(10))
            chem_output_dict[(alloy_nm, "Remelt")] = {
                elem: 0 if (tot_sent == 0) else round(els.get(elem) / tot_sent, 4)
                for elem in chem_list
            }
            # logging.info("\nMetal Source")
            # logging.info("PRIME:   %.0f %s  (%.1f%%)"
            #              % (prime_sol, UNIT, prime_sol / tot_sent * 100))
            bom_dict[alloy_nm] = {"PRIME": round(prime_sol)}
            bom_info_dict[alloy_nm]["Sum Cost"] = 0
            for i in range(len(scrap_flow_dict[destination])):
                supplier = scrap_flow_dict[destination][i]
                plant = plant_dict.get(supplier)
                material_list = plant.list_material_supply
                for m in range(len(material_list)):
                    material = material_list[m]
                    x_sol = round(x[(i, j, m, a)].solution_value())
                    bom_dict[alloy_nm][f"{material} - {supplier}"] = x_sol
                    if plant.dict_material_supply.get(material) is None:
                        material_cost = 100
                        failed += 1
                    else:
                        material_cost = float(
                            plant.dict_material_supply.get(material).cost
                        )
                    bom_info_dict[alloy_nm]["Sum Cost"] += x_sol * material_cost
                    tot_cost[j] += x_sol * material_cost
                    if x_sol > 0:
                        # logging.info("%s - %s:   %.0f %s  (%.1f%%)"
                        #              % (material, supplier, x_sol, UNIT, x_sol / tot_sent * 100))
                        if supplier in EXTERNAL_SCRAP_SOURCES:
                            rc[a] += (
                                x_sol
                                * plant.dict_material_supply.get(material).recovery
                            )
            # logging.info("\nRecovery: %.0f%%" % ((1 - scrap_rate) * 100))
            # logging.info("Recycled Content of %s: %.0f%%"
            #              % (alloy_nm, rc[a] * 100 / (tot_cast * (1 - scrap_rate))))
            # logging.info("Recycled Content of %s: %.0f%%\n"
            #              % (destination, tot_ext[j] / tot_melt[j] * 100))
            # logging.info(f"Prime Content of %s: %.0f %s" % (destination, tot_prime[j], UNIT))
            # logging.info("++++++++++++++++++++++++++++++++++++++++++++\n")
            # bom_info_dict[alloy_nm]['Recovery'] = f"{round((1 - scrap_rate)) * 100}%"
            if tot_sent < 0.01:
                bom_info_dict[alloy_nm]["Recovery"] = "0%"
                bom_info_dict[alloy_nm]["Recycled Content"] = "0%"
                bom_info_dict[alloy_nm]["Prime Usage"] = "0%"
            else:
                bom_info_dict[alloy_nm][
                    "Recovery"
                ] = f"{round((tot_cast / tot_sent) * 100)}%"
                bom_info_dict[alloy_nm][
                    "Recycled Content"
                ] = f"{round(rc[a] * 100 / (tot_cast * (1 - scrap_rate)))}%"
                bom_info_dict[alloy_nm][
                    "Prime Usage"
                ] = f"{round(prime_sol * 100 / (tot_cast * (1 - scrap_rate)))}%"
            plant_info_dict[f"Total recycled content for {destination}"] = (
                f"{0 if (tot_melt[j] == 0) else round(tot_ext[j] / tot_melt[j] * 100)}%"
            )
            plant_info_dict[f"Total cost for {destination}"] = round(tot_cost[j])
            plant_info_dict[f"Total prime content for {destination}"] = round(
                tot_prime[j]
            )

    # logging.info("******************************")
    # logging.info("******************************")
    # logging.info("OVERALL SCRAP CONSUMPTION DATA")
    # logging.info("******************************")
    # logging.info("******************************")

    scrap_used_list = list()

    for i in range(len(supplier_list)):
        tot_scrap = 0
        tot_amount = 0
        supplier = supplier_list[i]
        plant = plant_dict.get(supplier)
        material_list = plant.list_material_supply
        # logging.info(f"\n{supplier}")
        # logging.info("\nScrap      Available       Used")
        # logging.info("-------------------------------------")
        for m in range(len(material_list)):
            material_used = 0
            material_tot_cost = 0
            material = material_list[m]
            amount_available = plant.dict_material_supply.get(material).amount_available
            tot_amount += amount_available
            for j in range(len(destination_list)):
                destination = destination_list[j]
                if supplier in scrap_flow_dict[destination]:
                    form = plant.dict_material_supply.get(material).form
                    if form in plant_dict.get(destination).list_form:
                        tot_amount = plant_dict.get(destination).dict_form_capacity.get(
                            form
                        )[1]
                    alloy_list = plant_dict.get(destination).list_alloys_demand
                    i = scrap_flow_dict[destination].index(supplier)
                    for a in range(len(alloy_list)):
                        x_sol = x[(i, j, m, a)].solution_value()
                        material_used += x_sol
                        tot_scrap += x_sol
            if plant.dict_material_supply.get(material) is None:
                material_cost = 100
                failed += 1
            else:
                material_cost = float(plant.dict_material_supply.get(material).cost)
            material_tot_cost = material_cost * material_used
            # logging.info("%s \t %.0f %s \t %.0f %s"
            #              % (material, amount_available, UNIT, material_used, UNIT))
            scrap_used_list.append(
                [supplier, material, amount_available, material_used, material_tot_cost]
            )
        # logging.info("-------------------------------------")
        # logging.info("Sum \t %.0f %s \t %0.0f %s \n" % (tot_amount, UNIT, tot_scrap, UNIT))

    for j in range(len(destination_list)):
        tot_cast = 0
        tot_supply = 0
        destination = destination_list[j]
        alloy_list = plant_dict.get(destination).list_alloys_demand
        for a in range(len(alloy_list)):
            alloy = alloy_list[a]
            supply = plant_dict.get(destination).dict_supply.get(alloy)
            tot_supply += supply
            amt = (
                plant_dict.get(destination)
                .dict_material_supply.get(alloy)
                .amount_available
            )
            tot_cast += supply + amt
        # logging.info("%.0f %s of casting is required for %.0f %s of supply in %s"
        #              % (tot_cast, UNIT, tot_supply, UNIT, destination))

    # Format Excel output
    bom_df = (
        pd.DataFrame.from_dict(bom_dict, orient="index")
        .T.fillna(0)
        .rename_axis("Metal")
        .reset_index()
    )
    bom_info_df = pd.DataFrame.from_dict(bom_info_dict, orient="index").T.reset_index()
    plant_info_df = pd.DataFrame.from_dict(
        plant_info_dict, orient="index"
    ).reset_index()
    # add column "Cost" after "Used"
    scrap_used_df = pd.DataFrame(
        scrap_used_list, columns=["Source", "Scrap", "Available", "Used", "Cost"]
    )
    chem_df = pd.DataFrame.from_dict(chem_output_dict, orient="index")

    if os.path.exists(filename):
        writemode = "a"
        exists = "overlay"
    else:
        writemode = "w"
        exists = None

    with pd.ExcelWriter(
        filename, engine="openpyxl", if_sheet_exists=exists, mode=writemode
    ) as writer:
        bom_df.to_excel(writer, sheet_name=f"BOM - {furnace}", index=False)
        bom_info_df.to_excel(
            writer,
            sheet_name=f"BOM - {furnace}",
            index=False,
            header=False,
            startrow=len(bom_df) + 2,
        )
        plant_info_df.to_excel(
            writer,
            sheet_name=f"BOM - {furnace}",
            index=False,
            header=False,
            startrow=len(bom_df) + len(bom_info_df) + 3,
        )
        scrap_used_df.to_excel(
            writer, sheet_name=f"Scrap Used - {furnace}", index=False
        )
        chem_df.to_excel(writer, sheet_name=f"Chemistries - {furnace}")

    return filename
