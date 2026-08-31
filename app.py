import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import get_engine
from queries import SALES_DATA_QUERY


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Northwind Executive Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# EXECUTIVE THEME
# =========================================================

NAVY = "#0F172A"
BLUE = "#2563EB"
TEAL = "#0F766E"
SLATE = "#475569"
LIGHT_BLUE = "#EFF6FF"
LIGHT_GREY = "#F8FAFC"
BORDER = "#E2E8F0"
MUTED = "#64748B"


st.markdown(
    f"""
    <style>

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}

    h1 {{
        font-size: 30px !important;
        font-weight: 700 !important;
        color: {NAVY};
        letter-spacing: -0.4px;
        margin-bottom: 0 !important;
    }}

    h2, h3 {{
        color: {NAVY};
        font-weight: 650 !important;
    }}

    /* KPI cards */
    div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 18px 20px;
        min-height: 110px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 600;
    }}

    div[data-testid="stMetricValue"] {{
        color: {NAVY};
        font-size: 28px;
        font-weight: 700;
    }}

    div[data-testid="stMetricDelta"] {{
        font-size: 12px;
    }}

    /* Filter labels */
    label {{
        font-weight: 600 !important;
        color: {SLATE} !important;
        font-size: 13px !important;
    }}

    /* Filter section */
    .filter-bar {{
        background: {LIGHT_GREY};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 14px 16px 8px 16px;
        margin-bottom: 18px;
    }}

    /* Tabs */
    button[data-baseweb="tab"] {{
        font-size: 14px;
        font-weight: 600;
    }}

    hr {{
        border-color: {BORDER};
    }}

    .section-note {{
        color: {MUTED};
        font-size: 12px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOAD LIVE DATA FROM AWS
# =========================================================

@st.cache_data(ttl=600)
def load_sales_data():

    engine = get_engine()

    df = pd.read_sql(
    SALES_DATA_QUERY,
    engine
)

    df["order_date"] = pd.to_datetime(df["order_date"])

    df["shipped_date"] = pd.to_datetime(
        df["shipped_date"],
        errors="coerce"
    )

    return df


df = load_sales_data()


# =========================================================
# HEADER
# =========================================================

left_header, right_header = st.columns([4, 1])

with left_header:

    st.title("Northwind Executive Sales Dashboard")

    st.caption(
        "Performance overview powered by live AWS RDS MySQL data"
    )

with right_header:

    st.markdown(
        """
        <div style="
            text-align:right;
            color:#64748B;
            font-size:12px;
            padding-top:14px;
        ">
        Executive Performance View
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# FILTER BAR
# =========================================================

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

countries = sorted(df["country"].dropna().unique())
categories = sorted(df["category"].dropna().unique())
customers = sorted(df["customer"].dropna().unique())


st.markdown(
    '<div class="filter-bar">',
    unsafe_allow_html=True
)

f1, f2, f3, f4, f5 = st.columns(
    [1.6, 1.1, 1.1, 1.5, 0.8]
)

with f1:

    selected_dates = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )


with f2:

    selected_country = st.selectbox(
        "Country",
        ["All"] + countries
    )


with f3:

    selected_category = st.selectbox(
        "Category",
        ["All"] + categories
    )


with f4:

    selected_customer = st.selectbox(
        "Customer",
        ["All"] + customers
    )


with f5:

    top_n = st.selectbox(
        "Top N",
        [5, 10, 15, 20],
        index=1
    )


st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# APPLY FILTERS
# =========================================================

if len(selected_dates) == 2:

    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1])

else:

    start_date = pd.Timestamp(min_date)
    end_date = pd.Timestamp(max_date)


filtered_df = df[
    (df["order_date"] >= start_date)
    &
    (df["order_date"] <= end_date)
].copy()


if selected_country != "All":

    filtered_df = filtered_df[
        filtered_df["country"] == selected_country
    ]


if selected_category != "All":

    filtered_df = filtered_df[
        filtered_df["category"] == selected_category
    ]


if selected_customer != "All":

    filtered_df = filtered_df[
        filtered_df["customer"] == selected_customer
    ]


if filtered_df.empty:

    st.warning("No data available for the selected filters.")

    st.stop()


# =========================================================
# PREVIOUS PERIOD
# =========================================================

period_days = (end_date - start_date).days + 1

previous_end = start_date - pd.Timedelta(days=1)

previous_start = (
    previous_end
    - pd.Timedelta(days=period_days - 1)
)


previous_df = df[
    (df["order_date"] >= previous_start)
    &
    (df["order_date"] <= previous_end)
].copy()


if selected_country != "All":

    previous_df = previous_df[
        previous_df["country"] == selected_country
    ]


if selected_category != "All":

    previous_df = previous_df[
        previous_df["category"] == selected_category
    ]


if selected_customer != "All":

    previous_df = previous_df[
        previous_df["customer"] == selected_customer
    ]


# =========================================================
# HELPERS
# =========================================================

def pct_change(current, previous):

    if previous == 0:
        return None

    return ((current - previous) / previous) * 100


def delta_label(value):

    if value is None:
        return None

    return f"{value:+.1f}%"


# =========================================================
# KPIs
# =========================================================

revenue = filtered_df["revenue"].sum()

orders = filtered_df["order_id"].nunique()

customers_count = filtered_df["customer_id"].nunique()

units = filtered_df["quantity"].sum()

aov = revenue / orders if orders else 0


prev_revenue = previous_df["revenue"].sum()

prev_orders = previous_df["order_id"].nunique()

prev_customers = previous_df["customer_id"].nunique()

prev_units = previous_df["quantity"].sum()

prev_aov = (
    prev_revenue / prev_orders
    if prev_orders
    else 0
)


# =========================================================
# KPI STRIP
# =========================================================

k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.metric(
        "Revenue",
        f"${revenue:,.0f}",
        delta_label(
            pct_change(
                revenue,
                prev_revenue
            )
        )
    )


with k2:

    st.metric(
        "Orders",
        f"{orders:,}",
        delta_label(
            pct_change(
                orders,
                prev_orders
            )
        )
    )


with k3:

    st.metric(
        "Customers",
        f"{customers_count:,}",
        delta_label(
            pct_change(
                customers_count,
                prev_customers
            )
        )
    )


with k4:

    st.metric(
        "Avg Order Value",
        f"${aov:,.0f}",
        delta_label(
            pct_change(
                aov,
                prev_aov
            )
        )
    )


with k5:

    st.metric(
        "Units Sold",
        f"{units:,.0f}",
        delta_label(
            pct_change(
                units,
                prev_units
            )
        )
    )


st.markdown(
    f"""
    <div class="section-note">
    Comparison period:
    {previous_start.strftime("%d %b %Y")}
    to
    {previous_end.strftime("%d %b %Y")}
    </div>
    """,
    unsafe_allow_html=True
)


st.write("")


# =========================================================
# TABS
# =========================================================

overview_tab, product_tab, customer_tab, order_tab = st.tabs(
    [
        "Executive Overview",
        "Product Performance",
        "Customer Performance",
        "Order Explorer"
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with overview_tab:

    # -----------------------------------------------------
    # MONTHLY REVENUE TREND
    # -----------------------------------------------------

    trend_df = (
        filtered_df
        .assign(
            month=filtered_df[
                "order_date"
            ].dt.to_period("M").dt.to_timestamp()
        )
        .groupby(
            "month",
            as_index=False
        )
        .agg(
            Revenue=("revenue", "sum"),
            Orders=("order_id", "nunique")
        )
    )


    fig_trend = go.Figure()


    fig_trend.add_trace(

        go.Scatter(
            x=trend_df["month"],
            y=trend_df["Revenue"],
            mode="lines+markers",

            line=dict(
                color=BLUE,
                width=3
            ),

            marker=dict(
                size=7,
                color=BLUE
            ),

            fill="tozeroy",

            fillcolor="rgba(37,99,235,0.08)",

            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Revenue: $%{y:,.0f}"
                "<extra></extra>"
            )
        )
    )


    fig_trend.update_layout(

        title=dict(
            text="Revenue Trend",
            font=dict(
                size=18,
                color=NAVY
            )
        ),

        height=340,

        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",

        showlegend=False,

        hovermode="x unified",

        xaxis=dict(
            title=None,
            showgrid=False
        ),

        yaxis=dict(
            title=None,
            tickprefix="$",
            tickformat="~s",
            gridcolor="#EEF2F7",
            zeroline=False
        )
    )


    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )


    # -----------------------------------------------------
    # COUNTRY + CATEGORY
    # -----------------------------------------------------

    left, right = st.columns(2)


    country_df = (
        filtered_df
        .groupby(
            "country",
            as_index=False
        )["revenue"]
        .sum()
        .nlargest(
            8,
            "revenue"
        )
        .sort_values("revenue")
    )


    with left:

        fig_country = px.bar(
            country_df,
            x="revenue",
            y="country",
            orientation="h"
        )


        fig_country.update_traces(

            marker_color=SLATE,

            hovertemplate=(
                "<b>%{y}</b><br>"
                "Revenue: $%{x:,.0f}"
                "<extra></extra>"
            )
        )


        fig_country.update_layout(

            title=dict(
                text="Top Markets by Revenue",
                font=dict(
                    size=17,
                    color=NAVY
                )
            ),

            height=390,

            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10
            ),

            paper_bgcolor="white",
            plot_bgcolor="white",

            xaxis=dict(
                title=None,
                tickprefix="$",
                tickformat="~s",
                gridcolor="#EEF2F7"
            ),

            yaxis_title=None,

            showlegend=False
        )


        st.plotly_chart(
            fig_country,
            use_container_width=True
        )


    category_df = (
        filtered_df
        .groupby(
            "category",
            as_index=False
        )["revenue"]
        .sum()
        .sort_values(
            "revenue",
            ascending=False
        )
    )


    with right:

        fig_category = px.bar(
            category_df,
            x="category",
            y="revenue"
        )


        fig_category.update_traces(

            marker_color=TEAL,

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Revenue: $%{y:,.0f}"
                "<extra></extra>"
            )
        )


        fig_category.update_layout(

            title=dict(
                text="Revenue by Category",
                font=dict(
                    size=17,
                    color=NAVY
                )
            ),

            height=390,

            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10
            ),

            paper_bgcolor="white",
            plot_bgcolor="white",

            xaxis=dict(
                title=None,
                tickangle=-25
            ),

            yaxis=dict(
                title=None,
                tickprefix="$",
                tickformat="~s",
                gridcolor="#EEF2F7"
            ),

            showlegend=False
        )


        st.plotly_chart(
            fig_category,
            use_container_width=True
        )


# =========================================================
# PRODUCTS
# =========================================================

with product_tab:

    product_df = (
        filtered_df
        .groupby(
            [
                "product_name",
                "category"
            ],
            as_index=False
        )
        .agg(
            Revenue=("revenue", "sum"),
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum")
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
    )


    top_products = (
        product_df
        .head(top_n)
        .sort_values("Revenue")
    )


    fig_products = px.bar(
        top_products,
        x="Revenue",
        y="product_name",
        orientation="h"
    )


    fig_products.update_traces(

        marker_color=BLUE,

        hovertemplate=(
            "<b>%{y}</b><br>"
            "Revenue: $%{x:,.0f}"
            "<extra></extra>"
        )
    )


    fig_products.update_layout(

        title=f"Top {top_n} Products by Revenue",

        height=500,

        paper_bgcolor="white",
        plot_bgcolor="white",

        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10
        ),

        xaxis=dict(
            title=None,
            tickprefix="$",
            tickformat="~s",
            gridcolor="#EEF2F7"
        ),

        yaxis_title=None,

        showlegend=False
    )


    st.plotly_chart(
        fig_products,
        use_container_width=True
    )


    st.dataframe(
        product_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# CUSTOMERS
# =========================================================

with customer_tab:

    customer_df = (
        filtered_df
        .groupby(
            [
                "customer",
                "country"
            ],
            as_index=False
        )
        .agg(
            Revenue=("revenue", "sum"),
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum")
        )
    )


    customer_df["Avg Order Value"] = (
        customer_df["Revenue"]
        /
        customer_df["Orders"]
    )


    customer_df = customer_df.sort_values(
        "Revenue",
        ascending=False
    )


    top_customers = (
        customer_df
        .head(top_n)
        .sort_values("Revenue")
    )


    fig_customers = px.bar(
        top_customers,
        x="Revenue",
        y="customer",
        orientation="h"
    )


    fig_customers.update_traces(

        marker_color=SLATE,

        hovertemplate=(
            "<b>%{y}</b><br>"
            "Revenue: $%{x:,.0f}"
            "<extra></extra>"
        )
    )


    fig_customers.update_layout(

        title=f"Top {top_n} Customers by Revenue",

        height=500,

        paper_bgcolor="white",
        plot_bgcolor="white",

        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10
        ),

        xaxis=dict(
            title=None,
            tickprefix="$",
            tickformat="~s",
            gridcolor="#EEF2F7"
        ),

        yaxis_title=None,

        showlegend=False
    )


    st.plotly_chart(
        fig_customers,
        use_container_width=True
    )


    st.dataframe(
        customer_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ORDER EXPLORER
# =========================================================

with order_tab:

    orders_df = filtered_df[
        [
            "order_id",
            "order_date",
            "customer",
            "country",
            "product_name",
            "category",
            "quantity",
            "unit_price",
            "revenue"
        ]
    ].copy()


    orders_df = orders_df.sort_values(
        "order_date",
        ascending=False
    )


    orders_df.columns = [
        "Order ID",
        "Order Date",
        "Customer",
        "Country",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Revenue"
    ]


    st.dataframe(
        orders_df,
        use_container_width=True,
        hide_index=True,

        column_config={

            "Order Date":
                st.column_config.DateColumn(
                    "Order Date",
                    format="DD MMM YYYY"
                ),

            "Unit Price":
                st.column_config.NumberColumn(
                    "Unit Price",
                    format="$%.2f"
                ),

            "Revenue":
                st.column_config.NumberColumn(
                    "Revenue",
                    format="$%.2f"
                )
        }
    )


    csv = orders_df.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(
        "Download Filtered Orders",
        data=csv,
        file_name="northwind_orders.csv",
        mime="text/csv"
    )