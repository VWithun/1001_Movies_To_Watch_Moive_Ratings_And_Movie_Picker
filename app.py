import pandas as pd
import streamlit as st
from collections import Counter
import random
import altair as alt
import io
import requests
from rapidfuzz import process

# ==============================
# CONFIG
# ==============================
DEFAULT_CSV_URL = "https://raw.githubusercontent.com/VWithun/1001_Movies_To_Watch_Moive_Ratings_And_Movie_Picker/main/my_movie_ratings.csv"
GIF_URL = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaDRnd2M4NnRtYTAwM3VxMnBrNHNmYXRoc2E5amw0cDNwNGlnOTVtMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ToMjGpp7glCbyd7Id1u/giphy.gif"

# ==============================
# HEADER
# ==============================
st.markdown(f"""
<div style="display:flex; align-items:center; flex-wrap: wrap;">
    <img src="{GIF_URL}" width="200" style="margin-right:20px; border-radius:12px;">
    <h1 style="font-size:2.5em;">🎬 My Movie Tracker (1001 Movies to Watch Before You Die)</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Welcome to **My Movie Tracker**!  

This app is based on **IMDb's list '1001 Movies to Watch Before You Die'**:  
[IMDb Reference](https://www.imdb.com/list/ls024863935/)

### How to Use:
1. **Download the default CSV** using the button below to get started.  
2. **Upload your saved CSV** when you return to continue where you left off.  
3. Search movies, update ratings, and mark as watched.  
4. **Download your updated CSV** — the app will automatically create a copy to prevent overwriting your original file.  
""")

st.download_button(
    label="⬇️ Download Starter CSV",
    data=requests.get(DEFAULT_CSV_URL).content,
    file_name="my_movie_ratings.csv",
    mime="text/csv"
)
st.markdown("---")

# ==============================
# LOAD DATA
# ==============================
def load_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    df.columns = [col.strip() for col in df.columns]
    required_columns = ["Title", "Year", "Genres", "Actors", "Director", "Plot", "Poster_URL", "Rating", "Watched"]
    for col in required_columns:
        if col not in df.columns:
            if col == "Rating":
                df[col] = None
            elif col == "Watched":
                df[col] = False
            else:
                df[col] = "N/A"
    df['Genres_list'] = df['Genres'].fillna('').apply(lambda x: x.split(', ') if isinstance(x, str) else [])
    return df

uploaded_file = st.file_uploader("📂 Upload your CSV file:", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
    st.session_state.df = df
else:
    response = requests.get(DEFAULT_CSV_URL)
    df = load_data(io.StringIO(response.text))
    st.session_state.df = df

df = st.session_state.df

# ==============================
# HELPER FUNCTIONS
# ==============================
def get_fuzzy_matches(query, choices, limit=8, score_cutoff=60):
    if not query:
        return []
    results = process.extract(query, choices, limit=limit, score_cutoff=score_cutoff)
    return [r[0] for r in results]

# ==============================
# SEARCH & FILTER
# ==============================
st.subheader("🔍 Search & Filter Movies")
search_query = st.text_input("Search by Title", placeholder="e.g., Braveheart")

all_titles = df["Title"].dropna().astype(str).tolist()
matched_titles = get_fuzzy_matches(search_query, all_titles)

all_directors = sorted(df["Director"].dropna().unique())
selected_director = st.selectbox("Filter by Director", ["All"] + all_directors)

all_actors = sorted(set(a for sublist in df['Actors'].dropna().str.split(', ') for a in sublist))
selected_actor = st.selectbox("Filter by Actor", ["All"] + all_actors)

all_genres = sorted(set(g for lst in df['Genres_list'] for g in lst))
selected_genres = st.multiselect("Filter by Genre(s)", all_genres)

decades = sorted(df["Year"].dropna().apply(lambda y: (y//10)*10).unique())
selected_decade = st.selectbox("Filter by Decade", ["All"] + [str(d) for d in decades])

watched_filter = st.selectbox("Filter by Watched Status", ["All", "Watched", "Not Watched"])

# Apply filters
filtered_df = df.copy()
if selected_director != "All":
    filtered_df = filtered_df[filtered_df["Director"] == selected_director]
if selected_actor != "All":
    filtered_df = filtered_df[filtered_df['Actors'].str.contains(selected_actor, case=False, na=False)]
if selected_genres:
    filtered_df = filtered_df[filtered_df['Genres_list'].apply(lambda g: any(genre in g for genre in selected_genres))]
if selected_decade != "All":
    filtered_df = filtered_df[filtered_df["Year"].apply(lambda y: (y//10)*10) == int(selected_decade)]
if watched_filter == "Watched":
    filtered_df = filtered_df[filtered_df["Watched"] == True]
elif watched_filter == "Not Watched":
    filtered_df = filtered_df[filtered_df["Watched"] == False]

search_or_filter_applied = bool(search_query) or selected_director != "All" or selected_actor != "All" or selected_genres or selected_decade != "All" or watched_filter != "All"

# ==============================
# DISPLAY SEARCH RESULTS WITH WATCHED CHECKBOX
# ==============================
if search_or_filter_applied:
    st.subheader("🎥 Search Results")
    
    # Strict closest title match
    if search_query and matched_titles:
        top_match_idx = df[df["Title"] == matched_titles[0]].index[0]
        top_match = df.loc[top_match_idx]
        with st.container():
            st.markdown(f"### {top_match['Title']} ({top_match['Year']})")
            if pd.notna(top_match['Poster_URL']):
                st.image(top_match['Poster_URL'], width=150)
            st.write(f"Genres: {top_match['Genres']}")
            st.write(f"Director: {top_match['Director']}")
            # Show all actors
            actors_list = []
            if pd.notna(top_match['Actors']):
                actors_list = [a.strip() for a in top_match['Actors'].split(',')]
            st.write(f"Actors: {', '.join(actors_list)}")
            if 'Plot' in top_match and top_match['Plot']:
                st.write(f"**Plot:** {top_match['Plot']}")

            # Checkbox for Watched
            watched_val = st.checkbox("Mark as Watched", value=top_match['Watched'], key=f"watched_{top_match['Title']}")
            df.loc[top_match_idx, "Watched"] = watched_val

            # Rating
            rating_options = [None] + [x/2 for x in range(1, 21)]
            rating_val = st.selectbox(f"Update Rating for {top_match['Title']}", rating_options, index=0 if pd.isna(top_match['Rating']) else rating_options.index(top_match['Rating']), key=f"Rating_{top_match['Title']}")
            df.loc[top_match_idx, "Rating"] = rating_val
            if rating_val is not None:
                df.loc[top_match_idx, "Watched"] = True  # rating implies watched

    # Filtered matches
    filters_applied_only = not search_query and (selected_director != "All" or selected_actor != "All" or selected_genres or selected_decade != "All" or watched_filter != "All")
    if filters_applied_only and not filtered_df.empty:
        st.markdown("**Other Matches:**")
        for idx, row in filtered_df.iterrows():
            actors_list = []
            if pd.notna(row['Actors']):
                actors_list = [a.strip() for a in row['Actors'].split(',')]
            with st.container():
                st.markdown(f"- **{row['Title']} ({row['Year']})** | 🎥 {row['Director']} | 🎭 {row['Genres']} | 👤 {', '.join(actors_list)}")
                watched_val = st.checkbox(f"Mark as Watched", value=row['Watched'], key=f"watched_{row['Title']}_{idx}")
                df.loc[idx, "Watched"] = watched_val


# ==============================
# RANDOM MOVIE PICKER
# ==============================
st.markdown("### 🎲 Can't decide what to watch?")
if st.button("Pick a Random Movie"):
    random_picker_df = df[df["Watched"] == False].copy()
    if random_picker_df.empty:
        st.write("🎬 You have watched all movies!")
    else:
        movie = random_picker_df.sample(1).iloc[0]
        st.markdown(f"### {movie['Title']} ({movie['Year']})")
        st.write(f"Genres: {movie['Genres']}")
        st.write(f"Director: {movie['Director']}")
        if pd.notna(movie['Actors']):
            st.write(f"Actors: {movie['Actors']}")
        if 'Plot' in movie and movie['Plot']:
            st.write(f"**Plot:** {movie['Plot']}")
        if pd.notna(movie['Poster_URL']):
            st.image(movie['Poster_URL'], width=200)
# ==============================
# USER STATS (WATCHED MOVIES)
# ==============================
st.markdown("---")
st.subheader("📊 Your Movie Stats")
watched_df = df[df["Watched"] == True].copy()
watched_df['Rating'] = pd.to_numeric(watched_df['Rating'], errors='coerce')

if not watched_df.empty:
    # Summary stats
    total_watched = len(watched_df)
    avg_rating = watched_df['Rating'].mean()
    st.markdown(f"### 🎬 Total Movies Watched: **{total_watched}**")
    st.markdown(f"### 🌟 Average Rating Given: **{avg_rating:.1f}/10**")

    # Highest rated
    highest_movie = watched_df.sort_values(by='Rating', ascending=False).iloc[0]
    st.markdown(f"### ⭐ Highest Rated Movie: **{highest_movie['Title']}** ({highest_movie['Rating']}/10)")

    # -----------------------------
    # Top 10 Rated Movies Chart
    # -----------------------------
    top10_df = watched_df.sort_values(by='Rating', ascending=False).head(10)
    chart_top10 = alt.Chart(top10_df).mark_bar(color="#61dafb").encode(
        x=alt.X('Rating:Q', title='Rating', scale=alt.Scale(domain=[0,10])),
        y=alt.Y('Title:N', sort='-x', title='Movie'),
        tooltip=['Title','Rating']
    ).properties(height=300)
    st.altair_chart(chart_top10, use_container_width=True)

    # -----------------------------
    # Favorite Genres
    # -----------------------------
    genres_all = watched_df['Genres'].dropna().str.split(', ').sum()
    if genres_all:
        genre_counts = Counter(genres_all)
        genre_df = pd.DataFrame(genre_counts.items(), columns=['Genre','Count']).sort_values(by='Count', ascending=False)
        st.markdown("### 🎭 Favorite Genres")
        chart_genres = alt.Chart(genre_df).mark_bar(color="#ff6961").encode(
            x=alt.X('Count:Q', title='Count'),
            y=alt.Y('Genre:N', sort='-x', title='Genre'),
            tooltip=['Genre','Count']
        ).properties(height=250)
        st.altair_chart(chart_genres, use_container_width=True)

    # -----------------------------
    # Top Directors (>=2 watched)
    # -----------------------------
    director_counts = watched_df['Director'].value_counts()
    top_directors = director_counts[director_counts >= 2]
    if not top_directors.empty:
        st.markdown("### 🎬 Top Directors (≥2 movies)")
        director_df = pd.DataFrame(top_directors).reset_index()
        director_df.columns = ['Director','Count']
        chart_directors = alt.Chart(director_df).mark_bar(color="#FFD700").encode(
            x=alt.X('Count:Q', title='Movies Watched'),
            y=alt.Y('Director:N', sort='-x', title='Director'),
            tooltip=['Director','Count']
        ).properties(height=250)
        st.altair_chart(chart_directors, use_container_width=True)

    # -----------------------------
    # Top Actors (>=2 watched)
    # -----------------------------
    actor_list = watched_df['Actors'].dropna().str.split(', ').sum()
    actor_counts = Counter(actor_list)
    top_actors = {actor: cnt for actor, cnt in actor_counts.items() if cnt >= 2}
    if top_actors:
        st.markdown("### 👤 Top Actors (≥2 movies)")
        actor_df = pd.DataFrame(top_actors.items(), columns=['Actor','Count']).sort_values(by='Count', ascending=False)
        chart_actors = alt.Chart(actor_df).mark_bar(color="#00FF7F").encode(
            x=alt.X('Count:Q', title='Movies Watched'),
            y=alt.Y('Actor:N', sort='-x', title='Actor'),
            tooltip=['Actor','Count']
        ).properties(height=250)
        st.altair_chart(chart_actors, use_container_width=True)


# ==============================
# WATCHED MOVIES LIST (TOGGLE)
# ==============================
show_watched = st.checkbox("Show Watched Movies", value=False)
if show_watched and not watched_df.empty:
    for _, row in watched_df.sort_values(by='Rating', ascending=False).iterrows():
        st.markdown(f"- **{row['Title']}** – Rating: {row['Rating']}")

# ==============================
# DOWNLOAD UPDATED CSV
# ==============================
st.markdown("---")
st.subheader("💾 Save Your Progress")
st.download_button(
    label="⬇️ Download Updated CSV",
    data=df.to_csv(index=False),
    file_name="my_movie_ratings_updated.csv",
    mime="text/csv"
)

# ==============================
# STYLES
# ==============================
st.markdown("""
<style>
body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size:16px; }
.stApp { background-color: #121212; }
h1, h2, h3, h4 { color: #e0e0e0; }
h3 { font-size: 1.6em; }
h4 { font-size: 1.4em; }
.stCheckbox label { font-size: 1.1em; color: #e0e0e0; }
.markdown-text-container p, .markdown-text-container li { font-size: 1.1em; line-height:1.5em; }
</style>
""", unsafe_allow_html=True)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("<footer>© 2025 VWithun | <a href='https://github.com/VWithun/' target='_blank'>GitHub</a></footer>", unsafe_allow_html=True)
