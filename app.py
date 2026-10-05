import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="OEM1 Sustainability Analysis", layout="wide")


@st.cache_resource
def load_data():
    """
    Load the final dataset for the supply chain analysis.
    """
    dtypes = {
        "Vehicle_Type": "category",
        "Type_Origin": "category",
        "Type_Destination": "category",
        "Route_Stage": "category",
        "City_Origin": "category",
        "City_Destination": "category",
        "Location_Origin": "category",
        "Location_Destination": "category",
        "Distance_km": "float32",
        "Total_Distance_km": "float32",
        "Lat_Origin": "float32",
        "Lon_Origin": "float32",
        "Lat_Destination": "float32",
        "Lon_Destination": "float32",
    }

    return pd.read_csv("data/SoSe26_Case_Study_finalData_Group_11.csv", dtype=dtypes)


@st.cache_resource
def convert_df_to_csv(data):
    """
    Convert the DataFrame to CSV format for download.
    """
    return data.to_csv(index=False).encode("utf-8")


@st.cache_resource
def prepare_boxplot_data(data):
    """
    Prepare the data for boxplot visualizations by extracting relevant columns
    """
    base = data[
        [
            "ID_Vehicle",
            "Vehicle_Type",
            "Type_Origin",
            "Route_Stage",
            "Distance_km",
            "Total_Distance_km",
        ]
    ]

    return {
        "Vehicle Type": (
            base[["ID_Vehicle", "Vehicle_Type", "Total_Distance_km"]].drop_duplicates()
        ),
        "Engine Type": (
            base[base["Type_Origin"].str.startswith("Engine", na=False)][
                ["Type_Origin", "Total_Distance_km"]
            ].drop_duplicates()
        ),
        "Gearshift Type": (
            base[base["Type_Origin"].str.startswith("Gearshift", na=False)][
                ["Type_Origin", "Total_Distance_km"]
            ].drop_duplicates()
        ),
        "Single Part Type": (
            base[base["Type_Origin"].str.startswith("T", na=False)][
                ["Type_Origin", "Total_Distance_km"]
            ].drop_duplicates()
        ),
        "Route Stage": (base[["Route_Stage", "Distance_km"]]),
    }


@st.cache_resource
def get_vehicle_ids(data):
    """
    Get the unique vehicle IDs from the dataset.
    """
    return set(data["ID_Vehicle"].dropna().unique())


@st.cache_resource
def get_example_vehicles(data, n=20):
    """
    Get a random sample of example vehicle IDs from the dataset.
    """
    return (
        data["ID_Vehicle"]
        .dropna()
        .drop_duplicates()
        .sample(n=min(n, data["ID_Vehicle"].nunique()), random_state=42)
        .sort_values()
        .tolist()
    )


def create_boxplot(plot_df, category):
    """
    Create a boxplot figure based on the selected category.
    """
    if category == "Route Stage":
        x_column = "Route_Stage"
        y_column = "Distance_km"
        y_title = "Stage Distance (km)"

    elif category == "Vehicle Type":
        x_column = "Vehicle_Type"
        y_column = "Total_Distance_km"
        y_title = "Total Logistics Distance (km)"

    else:
        x_column = "Type_Origin"
        y_column = "Total_Distance_km"
        y_title = "Total Logistics Distance (km)"

    fig = px.box(
        plot_df,
        x=x_column,
        y=y_column,
        points=False,
        title=f"Distance Distribution by {category}",
    )

    fig.update_layout(xaxis_title=category, yaxis_title=y_title, height=600)

    return fig


@st.cache_resource
def prepare_boxplot_figures(boxplot_data):
    """
    Prepare boxplot figures for each category based on the provided data.
    """
    figures = {}

    for category, data in boxplot_data.items():
        figures[category] = create_boxplot(data, category)

    return figures


def create_map(data):
    """
    Create a scatter map figure to visualize the supply chain routes of a selected vehicle.
    """
    fig = go.Figure()

    for _, row in data.iterrows():

        fig.add_trace(
            go.Scattermap(
                lat=[row["Lat_Origin"], row["Lat_Destination"]],
                lon=[row["Lon_Origin"], row["Lon_Destination"]],
                mode="lines+markers",
                line=dict(width=2),
                marker=dict(size=[7, 12]),
                name=f"{row['Type_Origin']} to {row['Type_Destination']}",
                hoverinfo="text",
                text=(
                    f"Stage: {row['Route_Stage']}<br>"
                    f"Type: {row['Type_Origin']} to {row['Type_Destination']}<br>"
                    f"From: {row['Location_Origin']} {row['City_Origin']}<br>"
                    f"To: {row['Location_Destination']} {row['City_Destination']}<br>"
                    f"Distance: {row['Distance_km']:.1f} km"
                ),
            )
        )

    fig.update_layout(
        map=dict(style="carto-darkmatter", center={"lat": 51.0, "lon": 10.5}, zoom=5),
        height=700,
        showlegend=True,
    )

    return fig


@st.cache_resource
def get_average_vehicle_distance(data):
    """
    Return the average total logistics distance across all vehicles
    """
    return data.groupby("ID_Vehicle")["Total_Distance_km"].first().mean()


df = load_data()
boxplot_data = prepare_boxplot_data(df)
boxplot_figures = prepare_boxplot_figures(boxplot_data)
vehicle_ids = get_vehicle_ids(df)
example_vehicles = get_example_vehicles(df)

# Streamlit Header and Layout
col1, col2 = st.columns([1, 5])

with col1:
    st.image("www/Case_Study_Logo.png", width=180)

with col2:
    st.markdown(
        """
        <h1 style="
            font-size: 42px;
            margin-top: 25px;
            margin-bottom: 0px;
            color: #71bef1";
        ">
            OEM1 Sustainability Analysis
        </h1>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
    <p style="
        color:#7FA8C9;
        font-size:16px;
        margin-top:-10px;
    ">
    Logistics route analysis of vehicles produced in 2015
    </p>
    """,
        unsafe_allow_html=True,
    )

# tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Route Explorer", "Distance Analysis", "Dataset Overview"]
)

# gen overview
with tab1:
    st.markdown(
        """
    <div style="
        max-width: 900px;
        margin: auto;
        text-align: center;
    ">

    <h1>Application Overview</h1>

    <p style="font-size:18px;">
    This application visualizes the logistics routes of vehicles produced by OEM1 in 2015.
    The objective is to analyze transportation distances acros the supply chain and
    explore the logistics structure of vehicles, components, and individual parts.
    </p>

    <p style="font-size:16px;">
    The analysis includes the following supply chain stages:
    <br>
    Single Parts → Components<br>
    Components → Vehicle Production Plant<br>
    Vehicle Production Plant → Distribution Center
    </p>

    <p style="font-size:16px;">
    An analysis of the final customer delivery stage is excluded, as the customer location cannot be reliably determined and is outside the manufacturer's control. 
    Therefore, this stage is not considered relevant for asessing the sustainability of the controllable supply chain.
    </p>

    </div>
    """,
        unsafe_allow_html=True,
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Vehicles Analyzed", f"{df['ID_Vehicle'].nunique():,}")

    with col2:
        st.metric("Supply Chain Routes", f"{len(df):,}")

    with col3:
        st.metric("Total Distance", f"{df['Distance_km'].sum():,.0f} km")

    st.write("")

    st.info("""
        Use the interactive views to explore individual supply chains,
        compare logistics distances, and inspect the processed dataset.
        """)


# route Explorer Tab
with tab2:
    st.header("Interactive Supply Chain Map")

    st.caption(
        "Explore the logistics routes of individual vehicles produced in 2015.\n\n"
        + "Use the search field to find a specific vehicle and visualize its complete\
        supply chain from component suppliers to the distribution center.\n\n"
        + "Each Vehicle ID is of the format: **Vehicle Type - Manufacturer - Plant - Vehicle Number**\n\n"
    )

    if "selected_vehicle" not in st.session_state:
        st.session_state.selected_vehicle = example_vehicles[0]

    def select_example_vehicle():
        st.session_state.selected_vehicle = st.session_state.example_vehicle

    st.subheader("Select Vehicle")

    # show example vehicles in a drop down for quick selection

    st.selectbox(
        "Example Vehicles",
        example_vehicles,
        key="example_vehicle",
        on_change=select_example_vehicle,
    )
    # show a form for manual vehicle selection
    with st.form("vehicle_selection"):

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            vehicle_type = st.text_input("Vehicle Type", placeholder="e.g. 11")

        with col2:
            manufacturer = st.text_input("Manufacturer", placeholder="e.g. 1")

        with col3:
            plant = st.text_input("Plant", placeholder="e.g. 11")

        with col4:
            serial_id = st.text_input("Vehicle Number", placeholder="e.g. 905601")

        submitted = st.form_submit_button("Show Vehicle")

    if submitted:

        vehicle_type = vehicle_type.strip()
        manufacturer = manufacturer.strip()
        plant = plant.strip()
        serial_id = serial_id.strip()

        # check whether al fields are filled
        if not all([vehicle_type, manufacturer, plant, serial_id]):
            st.warning("Please fill in all fields before selecting a vehicle.")

        # reconstruct the vehicle ID from the input fields
        else:
            entered_vehicle = (
                f"{vehicle_type}-" f"{manufacturer}-" f"{plant}-" f"{serial_id}"
            )

            # Check whether vehicle actually exists
            if entered_vehicle not in vehicle_ids:
                st.warning(f"Vehicle '{entered_vehicle}' was not found.")

            else:
                st.session_state.selected_vehicle = entered_vehicle

    selected_vehicle = st.session_state.selected_vehicle

    if selected_vehicle is not None:

        map_df = df[df["ID_Vehicle"] == selected_vehicle]

        st.success(f"Selected Vehicle: {selected_vehicle}")

        st.subheader(f"Supply Chain Map - Vehicle {selected_vehicle}")

    map_df = df[df["ID_Vehicle"] == selected_vehicle]

    # core metrics for the selected vehicle

    col1, col2, col3 = st.columns(3)

    vehicle_total_distance = map_df["Total_Distance_km"].iloc[0]

    average_vehicle_distance = get_average_vehicle_distance(df)

    with col1:
        st.metric("Vehicle Total Distance", f"{vehicle_total_distance:,.1f} km")

    with col2:
        st.metric("Average Vehicle Distance", f"{average_vehicle_distance:,.1f} km")

    with col3:
        difference = vehicle_total_distance - average_vehicle_distance

        st.metric("Difference from Average", f"{difference:+,.1f} km")

    fig = create_map(map_df)

    st.plotly_chart(fig, width="stretch")
    st.info("""
    **Map Interpretation**

    - Small markers represent the **origin** of a logistics route.
    - Large markers represent the **destination** of a logistics route.
    - Lines indicate the transportation path between locations.
    - Hover over a route to view detailed information about the logistics stage,
      locations, and travelled distance.

    The displayed routes represent the supply chain stages of the selected vehicle,
    from component suppliers to the distribution center.
    """)

# Distance Analysis Tab (Boxplot Visualizations)

with tab3:

    st.header("Interactive Logistics Distance Analysis")

    st.caption("Compare logistics distances across different supply chain categories.")

    category = st.selectbox("Compare by", list(boxplot_figures.keys()))

    fig = boxplot_figures[category]

    st.plotly_chart(fig, width="stretch")

    st.info("""
    **Boxplot Interpretation**

    - The box represents the interquartile range (IQR), spanning from the first quartile (Q1) to the third quartile (Q3).
    - The line inside the box represents the median.
    - The whiskers extend to the most extreme observations within **1.5 × IQR** below Q1 and above Q3.
    - Values outside these limits are considered outliers.

    For **Vehicle Type, Engine Type, Gearshift Type, and Single Part Type**, the boxplots compare the **total logistics distance per vehicle**.

    For **Route Stage**, the boxplots instead compare the **individual distances of the respective route stages**, since a route stage represents only one part of the complete supply chain.
    """)

# paged dataset overview

with tab4:

    st.header("Dataset Overview")

    st.caption("Explore the complete final dataset used for the supply chain analysis.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Rows", f"{len(df):,}")

    with col2:
        st.metric("Total Columns", len(df.columns))

    selected_columns = st.multiselect(
        "Select columns to display", df.columns, default=list(df.columns)
    )

    rows_per_page = st.selectbox("Rows per page", [50, 100, 250, 500, 1000], index=1)

    total_pages = max(1, (len(df) + rows_per_page - 1) // rows_per_page)

    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

    start_row = (page - 1) * rows_per_page
    end_row = min(start_row + rows_per_page, len(df))

    st.caption(
        f"Showing rows {start_row + 1:,}–{end_row:,} "
        f"of {len(df):,} | Page {page:,} of {total_pages:,}"
    )

    if selected_columns:

        display_df = df.iloc[start_row:end_row][selected_columns]

        st.dataframe(display_df, width="stretch", height=500)

    else:
        st.warning("Please select at least one column to display.")

    csv = convert_df_to_csv(df)

    st.download_button(
        label="Download Complete Dataset",
        data=csv,
        file_name="OEM1_supply_chain_dataset.csv",
        mime="text/csv",
    )

    st.info(
        "The dataset contains information about the reconstructed supply chain stages "
        "of all analyzed vehicles produced in 2015.\n\n"
        "Each row represents a unique logistics route, including information about "
        "the origin and destination locations, route distance, and vehicle type.\n\n"
        "The long-format structure enables detailed exploration of logistics distances "
        "and supply chain patterns across different vehicles, components, and route stages."
    )
