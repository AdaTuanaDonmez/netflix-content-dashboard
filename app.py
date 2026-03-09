import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Netflix Dashboard", layout="wide")

NETFLIX_RED = "#E50914"
NETFLIX_BLACK = "#141414"
SIDEBAR_BLACK = "#000000"
NETFLIX_GRAY = "#B3B3B3"

st.markdown(f"""
<style>
    .stApp {{
        background-color: {NETFLIX_BLACK};
        color: white;
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: {NETFLIX_BLACK};
    }}

    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BLACK};
    }}

    [data-testid="stHeader"] {{
        background-color: {NETFLIX_BLACK};
    }}

    h1, h2, h3 {{
        color: {NETFLIX_RED};
    }}

    p {{
        color: white;
    }}

    /* Sidebar labels */
    label {{
        color: white !important;
    }}

    /* Dropdown text */
    div[data-baseweb="select"] > div {{
        color: black !important;
    }}

    /* Dropdown menu options */
    ul {{
        color: black !important;
    }}

</style>
""", unsafe_allow_html=True)

st.markdown(
    f"<h1 style='color:{NETFLIX_RED};'>Netflix Content Intelligence Dashboard</h1>",
    unsafe_allow_html=True
)
st.write("Explore Netflix content by country, category, rating, creators, and runtime.")

st.markdown("""
### Key Insights

• Netflix catalog is dominated by movies (~72% of titles).  
• Most films fall around the 90–110 minute runtime range.  
• Content production grew rapidly after 2016.  
• A small group of actors and directors appear frequently across titles.
""")

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("netflix_clean.csv")

# Split countries properly
df["Country"] = df["Country"].fillna("").str.split(", ")
df = df.explode("Country").reset_index(drop=True)
df["Country"] = df["Country"].astype(str).str.strip()
df.loc[df["Country"] == "", "Country"] = pd.NA

# Dates
df["Release_Date"] = pd.to_datetime(df["Release_Date"], errors="coerce")
df["Release_Year"] = df["Release_Date"].dt.year

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

country = st.sidebar.selectbox(
    "Country",
    ["All"] + sorted(df["Country"].dropna().astype(str).unique().tolist())
)

category = st.sidebar.selectbox(
    "Category",
    ["All"] + sorted(df["Category"].dropna().astype(str).unique().tolist())
)

rating = st.sidebar.selectbox(
    "Rating",
    ["All"] + sorted(df["Rating"].dropna().astype(str).unique().tolist())
)

min_year = int(df["Release_Year"].dropna().min())
max_year = int(df["Release_Year"].dropna().max())

selected_years = st.sidebar.slider(
    "Release Year",
    min_year,
    max_year,
    (min_year, max_year)
)

# -----------------------------
# Apply filters
# -----------------------------
filtered_df = df.copy()

if country != "All":
    filtered_df = filtered_df[filtered_df["Country"] == country]

if category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == category]

if rating != "All":
    filtered_df = filtered_df[filtered_df["Rating"] == rating]

filtered_df = filtered_df[
    (filtered_df["Release_Year"] >= selected_years[0]) &
    (filtered_df["Release_Year"] <= selected_years[1])
]

# -----------------------------
# Helper dataframes
# -----------------------------
filtered_movies = filtered_df[filtered_df["Category"] == "Movie"].copy()
filtered_movies["Duration_Minutes"] = (
    filtered_movies["Duration"].str.extract(r"(\d+)").astype(float)
)

filtered_tv = filtered_df[filtered_df["Category"] == "TV Show"].copy()
filtered_tv["Seasons"] = (
    filtered_tv["Duration"].str.extract(r"(\d+)").astype(float)
)

# -----------------------------
# KPI cards
# -----------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Titles", len(filtered_df))
col2.metric("Movies", int((filtered_df["Category"] == "Movie").sum()))
col3.metric("TV Shows", int((filtered_df["Category"] == "TV Show").sum()))

avg_movie_duration = filtered_movies["Duration_Minutes"].mean()
col4.metric(
    "Avg Movie Duration",
    f"{avg_movie_duration:.1f} min" if pd.notnull(avg_movie_duration) else "N/A"
)

# -----------------------------
# Chart 1: Movie vs TV Ratio
# -----------------------------
category_counts = filtered_df["Category"].value_counts().reset_index()
category_counts.columns = ["Category", "Count"]

fig1 = px.pie(
    category_counts,
    names="Category",
    values="Count",
    title="Movie vs TV Ratio",
    color_discrete_sequence=[NETFLIX_RED, NETFLIX_GRAY],
    hole=0.4
)

# -----------------------------
# Chart 2: Top Directors
# -----------------------------
director_df = filtered_df.dropna(subset=["Director"]).copy()
director_df["Director"] = director_df["Director"].str.split(", ")
director_df = director_df.explode("Director").reset_index(drop=True)
director_df["Director"] = director_df["Director"].str.strip()

top_directors = director_df["Director"].value_counts().head(10).reset_index()
top_directors.columns = ["Director", "Count"]

fig2 = px.bar(
    top_directors,
    x="Director",
    y="Count",
    title="Top Directors",
    text="Count",
    color_discrete_sequence=[NETFLIX_RED]
)
fig2.update_layout(xaxis_tickangle=-45)

# -----------------------------
# Chart 3: Movie Duration Distribution
# -----------------------------
fig3 = px.histogram(
    filtered_movies.dropna(subset=["Duration_Minutes"]),
    x="Duration_Minutes",
    nbins=30,
    title="Movie Duration Distribution",
    color_discrete_sequence=[NETFLIX_RED]
)

# -----------------------------
# Chart 4: Titles Released Over Time
# -----------------------------
release_trend = (
    filtered_df.dropna(subset=["Release_Year"])
    .groupby("Release_Year")
    .size()
    .reset_index(name="Count")
)

fig4 = px.line(
    release_trend,
    x="Release_Year",
    y="Count",
    title="Titles Released Over Time",
    markers=True,
    color_discrete_sequence=[NETFLIX_RED]
)

# -----------------------------
# Chart 5: Top Actors
# -----------------------------
actor_df = filtered_df.dropna(subset=["Cast"]).copy()
actor_df["Cast"] = actor_df["Cast"].str.split(", ")
actor_df = actor_df.explode("Cast").reset_index(drop=True)
actor_df["Cast"] = actor_df["Cast"].str.strip()

top_actors = actor_df["Cast"].value_counts().head(10).reset_index()
top_actors.columns = ["Actor", "Count"]

fig5 = px.bar(
    top_actors,
    x="Actor",
    y="Count",
    title="Top 10 Actors",
    text="Count",
    color_discrete_sequence=[NETFLIX_RED]
)
fig5.update_layout(xaxis_tickangle=-45)

# -----------------------------
# Chart 6: Rating Distribution
# -----------------------------
rating_counts = filtered_df["Rating"].value_counts().reset_index()
rating_counts.columns = ["Rating", "Count"]

fig6 = px.bar(
    rating_counts,
    x="Rating",
    y="Count",
    title="Rating Distribution",
    text="Count",
    color_discrete_sequence=[NETFLIX_RED]
)
fig6.update_layout(xaxis_tickangle=-45)

# -----------------------------
# Chart 7: TV Show Seasons Distribution
# -----------------------------
fig7 = px.histogram(
    filtered_tv.dropna(subset=["Seasons"]),
    x="Seasons",
    nbins=15,
    title="TV Show Seasons Distribution",
    color_discrete_sequence=[NETFLIX_RED]
)

# -----------------------------
# Chart 8: Country vs Category
# -----------------------------
country_category_counts = (
    filtered_df.groupby(["Country", "Category"])
    .size()
    .reset_index(name="Count")
)

top_countries = (
    country_category_counts.groupby("Country")["Count"]
    .sum()
    .nlargest(10)
    .index
)

country_category_counts = country_category_counts[
    country_category_counts["Country"].isin(top_countries)
]

fig8 = px.bar(
    country_category_counts,
    x="Country",
    y="Count",
    color="Category",
    barmode="group",
    title="Top 10 Countries by Category",
    color_discrete_sequence=[NETFLIX_RED, NETFLIX_GRAY]
)
fig8.update_layout(xaxis_tickangle=-45)

# -----------------------------
# Chart 9: Rating vs Runtime
# -----------------------------
fig9 = px.box(
    filtered_movies.dropna(subset=["Rating", "Duration_Minutes"]),
    x="Rating",
    y="Duration_Minutes",
    title="Movie Duration by Rating",
    color="Rating",
    color_discrete_sequence=[NETFLIX_RED] * 20
)
fig9.update_layout(xaxis_tickangle=-45, showlegend=False)

# -----------------------------
# Apply dark theme to all charts
# -----------------------------
all_figs = [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9]

for fig in all_figs:
    fig.update_layout(
        paper_bgcolor=NETFLIX_BLACK,
        plot_bgcolor=NETFLIX_BLACK,
        font_color="white",
        title_font_color=NETFLIX_RED
    )

# -----------------------------
# Final layout
# -----------------------------
st.subheader("Catalog Overview")
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(fig4, use_container_width=True)
with row1_col2:
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("Creators and Cast")
row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.plotly_chart(fig2, use_container_width=True)
with row2_col2:
    st.plotly_chart(fig5, use_container_width=True)

st.subheader("Audience and Geography")
row3_col1, row3_col2 = st.columns(2)
with row3_col1:
    st.plotly_chart(fig6, use_container_width=True)
with row3_col2:
    st.plotly_chart(fig8, use_container_width=True)

st.subheader("Content Length")
row4_col1, row4_col2 = st.columns(2)
with row4_col1:
    st.plotly_chart(fig3, use_container_width=True)
with row4_col2:
    st.plotly_chart(fig7, use_container_width=True)

st.subheader("Ratings and Runtime")
st.plotly_chart(fig9, use_container_width=True)