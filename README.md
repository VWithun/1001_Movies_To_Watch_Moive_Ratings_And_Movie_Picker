# 🎬 My Movie Tracker - Streamlit App

Welcome to **My Movie Tracker**! This interactive app lets you explore, track, and rate your favorite movies. You can upload your own CSV file of movies, mark them as watched, and add personal ratings.
https://1001ratingandmoviespicker.streamlit.app/

---

## 🚀 Features

- **Search by Title**: Quickly find any movie in your collection using fuzzy search.  
- **Filter by Watched/Unwatched**: Toggle between movies you have seen and those you haven’t.  
- **Rate Movies**: Add ratings for each movie and update your CSV on the fly.  
- **View Movie Details**: See actors, director, genres, plot, poster, and average rating.  
- **Upload Your Own CSV**: Connect your own CSV file (`Title`, `Poster_URL`, `Rating`, `Watched`) to personalize your movie tracking.  

---

## 🖥 How to Use

1. Open the app via the link below.  
2. Use the **search bar** to find movies by title.  
3. Use the **filter panel** to show either watched or unwatched movies.  
4. Click on a movie to view its details and add a rating.  
5. Press the **“Save Changes”** button to update your CSV.  
6. Optional: Upload your own movie CSV to track your personal ratings.

---

## 📌 Data

The app works with a CSV of movies containing:

- **Title**  
- **Year**  
- **Genres**  
- **Actors**  
- **Director**  
- **Plot**  
- **Poster_URL**  
- **OMDb_URL** (optional)  
- **Watched** (True/False)  
- **Rating** (numeric value)

You can start with a copy of `all_movies_with_full_info.csv` and rename it `my_movie_ratings.csv` for testing.

---

## 🌐 Try it Live

Check out the app online here:  
[🎬 Open Movie Tracker](https://share.streamlit.io/VWithun/YOUR_REPO/main/movie_app.py)  

> Replace the link with your Streamlit deployment URL once published.

---
## ✅ License
This project is licensed under the [CC BY-NC-ND 4.0 License](LICENSE).

You may **not** copy, modify, or distribute this code without explicit permission from the author.

Copyright (c) 2025 VWithun

## 💻 Installation (Optional - Run Locally)

If you want to run the app on your own machine:

```bash
# Clone this repository
git clone https://github.com/VWithun/YOUR_REPO.git
cd YOUR_REPO

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run movie_app.py




Copyright (c) 2025 VWithun


