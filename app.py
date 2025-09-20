import pandas as pd
import streamlit as st
from rapidfuzz import process
from collections import Counter
import random
import altair as alt
import io
import requests

# ==============================
# CONFIG
# ==============================
DEFAULT_CSV_URL = "https://raw.githubusercontent.com/VWithun/1001_Movies_To_Watch_Moive_Ratings_And_Movie_Picker/main/my_movie_ratings.csv"
DEFAULT_CSV_PATH = "my_movie_ratings.csv"

# ==============================
# HEADER
# ==============================
st.title("🎬 My Movie Tracker (1001 Movies to Watch Before You Die)")

st.markdown("""
Welcome to **My Movie Tracker**!  

This app is based on **IMDb's list '1001 Movies to Watch Before You Die'**:  
[IMDb Reference](https://www.imdb.com/list/ls024863935/)

### How to Use:
1. **Download the default CSV** to get started using the button below.  
2. **Upload your saved CSV** at the start of each session to continue where you left off.  
3. Search for movies, update your ratings, and mark them as watched.  
4. When finished, **download the updated CSV** and save it on your computer.  
5. Next time you return, upload your saved CSV to pick up where you left off.  
""")

# Download default CSV
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
    return df

uploaded_file = st.file_uploader("📂 Upload your CSV file:", type=["csv"], key="csv_upload")

if uploaded_file:
    CSV_PATH = uploaded_file.name
    df = load_data(uploaded_file)
else:
    # If no file uploaded, use default GitHub file
    response = requests.get(DEFAULT_CSV_URL)
    CSV_PATH = DEFAULT_CSV_PATH
    df = load_data(io.StringIO(response.text))

if "df" not in st.session_state or st.session_state.get("csv_path") != CSV_PATH:
    st.session_state.df = df
    st.session_state.csv_path = CSV_PATH

df = st.session_state.df

# Ensure required columns exist
required_columns = ["Title", "Year", "Genres", "Actors", "Director", "Plot", "Poster_URL", "Rating", "Watched"]
for col in required_columns:
    if col not in df.columns:
        if col == "Rating":
            df[col] = None
        elif col == "Watched":
            df[col] = False
        else:
            df[col] = "N/A"

# Prepare Genres list safely
df['Genres_list'] = df['Genres'].fillna('').apply(lambda x: x.split(', ') if isinstance(x, str) else [])

# ==============================
# HELPER FUNCTIONS
# ==============================
def get_fuzzy_matches(query, choices, limit=8, score_cutoff=60):
    if not query:
        return []
    results = process.extract(query, choices, limit=limit, score_cutoff=score_cutoff)
    return [r[0] for r in results]

# ==============================
# STYLES
# ==============================
st.markdown("""
<style>
body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.stApp { background-color: #121212; }
.movie-card { background-color: #1e1e1e; border-radius: 12px; padding: 10px; margin-bottom: 12px; display: flex; flex-direction: row; box-shadow: 0px 4px 12px rgba(0,0,0,0.4); }
.movie-details { flex: 1; margin-left: 10px; }
.movie-title { font-size: 1em; font-weight: bold; }
.small-meta { font-size: 0.8em; color: #bdbdbd; margin: 2px 0; }
.movie-plot { font-size: 0.85em; font-style: italic; margin: 4px 0; }
a { color: #61dafb; text-decoration: none; }
footer { text-align: center; margin-top: 20px; font-size: 0.8em; color: #888; }
</style>
""", unsafe_allow_html=True)

# ==============================
# SEARCH & FILTER MOVIES
# ==============================
col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.subheader("🔍 Search & Filter Movies")

    st.markdown(
        "<span style='color:#ff6961;'>⚠️ Do not rename the CSV file or modify columns as it may cause errors.</span>",
        unsafe_allow_html=True
    )

    # ---------- TITLE SEARCH (Top Match Only) ----------
    all_titles = df["Title"].dropna().astype(str).tolist()
    search_query = st.text_input("Search by Title", placeholder="e.g., Braveheart", key="search_title_input")
    matched_titles = get_fuzzy_matches(search_query, all_titles) if search_query else []

    # ---------- OTHER FILTERS ----------
    all_directors = sorted(df["Director"].dropna().unique())
    selected_director = st.selectbox("Search Director", ["All"] + all_directors, key="director_filter")

    all_actors = sorted(set(a for sublist in df['Actors'].dropna().str.split(', ') for a in sublist))
    selected_actor = st.selectbox("Search Actor", ["All"] + all_actors, key="actor_filter")

    all_genres = sorted(set(g for lst in df['Genres_list'] for g in lst))
    selected_genres = st.multiselect("Select Genre(s)", all_genres, key="genre_filter")

    decades = sorted(df["Year"].dropna().apply(lambda y: (y//10)*10).unique())
    selected_decade = st.selectbox("Select Decade", ["All"] + [str(d) for d in decades], key="decade_filter")

# Apply filters (other than title)
filtered_df = df.copy()
if selected_director != "All":
    filtered_df = filtered_df[filtered_df["Director"] == selected_director]
if selected_actor != "All":
    filtered_df = filtered_df[filtered_df['Actors'].str.contains(selected_actor, case=False, na=False)]
if selected_genres:
    filtered_df = filtered_df[filtered_df['Genres_list'].apply(lambda g: any(genre in g for genre in selected_genres))]
if selected_decade != "All":
    filtered_df = filtered_df[filtered_df["Year"].apply(lambda y: (y//10)*10) == int(selected_decade)]

# ==============================
# SEARCH RESULTS DISPLAY
# ==============================
with col_right:
    st.subheader("🎥 Search Results")

    show_results = bool(search_query) or selected_director != "All" or selected_actor != "All" or selected_genres or selected_decade != "All"

    if show_results:
        if search_query:
            if matched_titles:
                # Display only the top match
                best_title = matched_titles[0]
                movie_row = df[df["Title"] == best_title].iloc[0]

                st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
                poster_url = movie_row.get("Poster_URL", "")
                if pd.notna(poster_url) and poster_url.strip():
                    st.image(poster_url, width=120)
                actors_html = ", ".join([a.strip() for a in str(movie_row["Actors"]).split(",")]) if pd.notna(movie_row["Actors"]) else "N/A"
                rating_display = movie_row['Rating'] if pd.notna(movie_row['Rating']) else "None"
                watched_status = "Watched" if movie_row["Watched"] else "Not Watched"
                st.markdown(
                    f"<div class='movie-details'>"
                    f"<div class='movie-title'>{movie_row['Title']} ({movie_row['Year']})</div>"
                    f"<div class='small-meta'>🎭 {movie_row['Genres']}</div>"
                    f"<div class='small-meta'>🎥 {movie_row['Director']}</div>"
                    f"<div class='small-meta'>👤 {actors_html}</div>"
                    f"<div class='movie-plot'>{movie_row['Plot']}</div>"
                    f"<div class='small-meta'>My Rating: {rating_display}</div>"
                    f"<div class='small-meta'>{watched_status}</div>"
                    f"</div>", unsafe_allow_html=True
                )
                rating_options = [None] + [x/2 for x in range(1, 21)]
                rating_val = st.selectbox(f"Update Rating for {movie_row['Title']}", rating_options, index=0, key=f"Rating_{movie_row['Title']}")
                if rating_val is not None:
                    df.loc[df["Title"] == movie_row['Title'], "Rating"] = rating_val
                    df.loc[df["Title"] == movie_row['Title'], "Watched"] = True
                if st.button(f"💾 Save {movie_row['Title']}", key=f"save_{movie_row['Title']}"):
                    st.session_state.df = df
                    st.success(f"Saved '{movie_row['Title']}' successfully!")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.write("No movies match your title search.")
        else:
            if filtered_df.empty:
                st.write("No movies match your filter.")
            else:
                for _, row in filtered_df.iterrows():
                    st.markdown(f"- **{row['Title']} ({row['Year']})** | 🎥 {row['Director']} | 🎭 {row['Genres']}")
    else:
        st.write("Enter a title or apply filters to see search results.")

# ==============================
# RANDOM MOVIE PICKER (UNWATCHED ONLY)
# ==============================
st.markdown("<h3 style='color:#e0e0e0;'>🎲 Can't decide what to watch?</h3>", unsafe_allow_html=True)

if st.button("Pick a Random Movie"):
    random_picker_df = df[df["Watched"] == False].copy()
    
    if random_picker_df.empty:
        st.write("🎬 You have watched all movies! Nothing left to pick.")
    else:
        movie = random_picker_df.sample(1).iloc[0]
        st.markdown(f"### {movie['Title']} ({movie['Year']})")
        st.write(f"Genres: {movie['Genres']}")
        st.write(f"Director: {movie['Director']}")
        st.write(f"Actors: {movie['Actors']}")
        if 'Plot' in movie and movie['Plot']:
            st.write(f"**Plot:** {movie['Plot']}")
        if 'Poster_URL' in movie and movie['Poster_URL'] and movie['Poster_URL'] != "N/A":
            st.image(movie['Poster_URL'], width=250)

# ==============================
# WATCHED MOVIES LIST
# ==============================
with st.expander("🎬 Watched Movies"):
    watched_df = df[df["Watched"] == True].copy()
    if not watched_df.empty:
        watched_df['Rating'] = watched_df['Rating'].fillna("None")
        for _, row in watched_df.sort_values(by='Rating', ascending=False).iterrows():
            st.markdown(f"- **{row['Title']}** - Rating: {row['Rating']}")
    else:
        st.write("No movies marked as watched yet.")

# ==============================
# USER STATISTICS
# ==============================
rated_df = df[df['Rating'].notna() & (df['Rating'] != "None")].copy()
if rated_df.shape[0] > 5:
    st.subheader("📊 Your Movie Stats")

    # Average Rating
    watched_ratings = rated_df['Rating'].astype(float)
    avg_rating = watched_ratings.mean()
    st.markdown(f"**Average Rating:** {avg_rating:.2f}/10")

    # Rating distribution
    rating_counts = watched_ratings.value_counts().sort_index()
    rating_chart = (
        alt.Chart(pd.DataFrame({'Rating': rating_counts.index, 'Count': rating_counts.values}))
        .mark_bar(color='#ff7f0e')
        .encode(
            x=alt.X('Rating:O', title='Rating'),
            y=alt.Y('Count:Q', title='Number of Movies'),
        )
    )
    text = rating_chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-2,
        color='white'
    ).encode(text='Count:Q')
    st.altair_chart(rating_chart + text, use_container_width=True)

    # Favorite Genres
    genre_list = rated_df['Genres'].dropna().str.split(', ').sum()
    if genre_list:
        genre_counts = Counter(genre_list)
        genre_df = pd.DataFrame({'Genre': list(genre_counts.keys()), 'Count': list(genre_counts.values())})
        genre_chart = (
            alt.Chart(genre_df)
            .mark_bar(color='#17becf')
            .encode(
                x=alt.X('Count:Q', title='Count'),
                y=alt.Y('Genre:N', sort='-x', title='Genre'),
            )
        )
        text = genre_chart.mark_text(
            align='left',
            baseline='middle',
            dx=3,
            color='white'
        ).encode(text='Count:Q')
        st.subheader("🎭 Favorite Genres (Watched)")
        st.altair_chart(genre_chart + text, use_container_width=True)

# ==============================
# DOWNLOAD UPDATED CSV
# ==============================
st.markdown("---")
st.subheader("💾 Save Your Progress")

st.download_button(
    label="⬇️ Download Updated CSV",
    data=st.session_state.df.to_csv(index=False),
    file_name="my_movie_ratings.csv",
    mime="text/csv",
)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("<footer>© 2025 VWithun | <a href='https://github.com/VWithun/' target='_blank'>GitHub</a></footer>", unsafe_allow_html=True)
