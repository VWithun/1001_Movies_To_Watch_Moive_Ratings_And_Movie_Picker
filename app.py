import pandas as pd
import streamlit as st
from collections import Counter
import altair as alt
import io
import requests

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
    <img src="{GIF_URL}" width="150" style="margin-right:20px; border-radius:12px;">
    <h1 style="font-size:2em; margin-top:20px;">🎬 My Movie Tracker (1001 Movies to Watch Before You Die)</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Welcome to **My Movie Tracker**!  

This app is based on **IMDb's list '1001 Movies to Watch Before You Die'**:  
[IMDb Reference](https://www.imdb.com/list/ls024863935/)

### How to Use on Mobile:
1. **Download the starter CSV** to your device. On mobile, it usually saves to your **Downloads** folder.  
2. **Upload your CSV** when you return. Your phone will let you pick the file from Downloads or cloud storage.  
3. Update ratings, mark movies as watched.  
4. **Download your updated CSV** again — the file name is simple and easy to find.  
5. Re-upload the updated CSV next time to continue.
""")

st.download_button(
    label="⬇️ Download Starter CSV",
    data=requests.get(DEFAULT_CSV_URL).content,
    file_name="my_movie_ratings.csv",
    mime="text/csv",
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
    return df

uploaded_file = st.file_uploader(
    "📂 Upload your CSV file (from Downloads or cloud storage):",
    type=["csv"],
    label_visibility="visible"
)

if uploaded_file:
    df = load_data(uploaded_file)
    st.session_state.df = df
else:
    response = requests.get(DEFAULT_CSV_URL)
    df = load_data(io.StringIO(response.text))
    st.session_state.df = df

df = st.session_state.df
df['Genres_list'] = df['Genres'].fillna('').apply(lambda x: x.split(', ') if isinstance(x, str) else [])

# ==============================
# USER STATISTICS (Watched Movies Only)
# ==============================
st.subheader("📊 Your Movie Stats")
watched_df = df[df["Watched"] == True].copy()
watched_df['Rating'] = pd.to_numeric(watched_df['Rating'], errors='coerce')

if watched_df.empty:
    st.write("No watched movies yet. Mark movies as watched to see your statistics!")
else:
    # Highest Rated Movie
    highest_movie = watched_df.sort_values(by='Rating', ascending=False).iloc[0]
    st.markdown(f"### ⭐ Highest Rated Movie: **{highest_movie['Title']}** ({highest_movie['Rating']}/10)")

    # Top 10 Rated Movies
    top10_df = watched_df.sort_values(by='Rating', ascending=False).head(10)
    st.markdown("### 🎞 Top 10 Rated Movies")
    chart_top10 = alt.Chart(top10_df).mark_bar(color="#61dafb").encode(
        x=alt.X('Rating:Q', title='Rating', scale=alt.Scale(domain=[0,10])),
        y=alt.Y('Title:N', sort='-x', title='Movie'),
        tooltip=['Title','Rating']
    ).properties(height=300)
    st.altair_chart(chart_top10, use_container_width=True)

    # Top Directors (≥2 movies)
    director_counts = watched_df['Director'].value_counts()
    top_directors = director_counts[director_counts >= 2]
    if not top_directors.empty:
        st.markdown("### 🎬 Top Directors (≥2 watched movies)")
        for director, count in top_directors.items():
            movies_by_director = watched_df[watched_df['Director']==director]['Title'].tolist()
            st.markdown(f"- **{director}** ({count} movies): {', '.join(movies_by_director)}")

    # Top Actors (≥2 movies)
    actor_list = watched_df['Actors'].dropna().str.split(', ').sum()
    actor_counts = Counter(actor_list)
    top_actors = {actor: cnt for actor, cnt in actor_counts.items() if cnt >= 2}
    if top_actors:
        st.markdown("### 👤 Top Actors (≥2 watched movies)")
        for actor, count in top_actors.items():
            movies_by_actor = watched_df[watched_df['Actors'].str.contains(actor)]['Title'].tolist()
            st.markdown(f"- **{actor}** ({count} movies): {', '.join(movies_by_actor)}")

    # Most Common Genres
    genres_all = watched_df['Genres'].dropna().str.split(', ').sum()
    if genres_all:
        genre_counts = Counter(genres_all)
        most_common_genre, genre_count = genre_counts.most_common(1)[0]
        st.markdown(f"### 🎭 Most Common Genre: **{most_common_genre}** ({genre_count} movies)")
        genre_df = pd.DataFrame(genre_counts.items(), columns=['Genre','Count'])
        chart_genres = alt.Chart(genre_df).mark_bar(color="#ff6961").encode(
            x=alt.X('Count:Q', title='Count'),
            y=alt.Y('Genre:N', sort='-x', title='Genre'),
            tooltip=['Genre','Count']
        ).properties(height=300)
        st.altair_chart(chart_genres, use_container_width=True)

# ==============================
# WATCHED MOVIES LIST (Toggleable)
# ==============================
st.markdown("---")
st.subheader("🎬 Watched Movies")
show_watched = st.checkbox("Show Watched Movies", value=False)

if show_watched:
    if watched_df.empty:
        st.write("No movies marked as watched yet.")
    else:
        for _, row in watched_df.sort_values(by='Rating', ascending=False).iterrows():
            st.markdown(f"- **{row['Title']}** – Rating: {row['Rating']}")

# ==============================
# DOWNLOAD UPDATED CSV
# ==============================
st.markdown("---")
st.subheader("💾 Save Your Progress (Mobile-Friendly)")
st.markdown("Tip: On mobile, the file will usually appear in your **Downloads** folder.")

csv_bytes = st.session_state.df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Updated CSV",
    data=csv_bytes,
    file_name="my_movie_ratings_copy.csv",
    mime="text/csv",
)

# ==============================
# MOBILE-FRIENDLY STYLING
# ==============================
st.markdown("""
<style>
body { font-size:16px; line-height:1.5em; }
h1, h2, h3, h4 { line-height:1.3em; }
.stButton>button { font-size:1em; padding:10px 20px; }
.stFileUploader>div { font-size:1em; padding:10px; }
</style>
""", unsafe_allow_html=True)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("<footer>© 2025 VWithun | <a href='https://github.com/VWithun/' target='_blank'>GitHub</a></footer>", unsafe_allow_html=True)
