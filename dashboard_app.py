import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import io # To handle in-memory CSV data for insights

# --- Configuration ---
# Set your Gemini API Key here. Get one from https://aistudio.google.com/app/apikey
# For security, consider using Streamlit Secrets for deployment:
# GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_API_KEY = "AIzaSyBRFiXMsnyFUd1mDNYfEqb1L7NP-k4ibR0" # Using the API key from your last provided React app

# --- Page Configuration ---
st.set_page_config(
    page_title="Interactive Media Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Functions ---

def normalize_column_name(name):
    """Normalizes column names by converting to lowercase and removing non-alphanumeric characters."""
    return name.lower().replace(' ', '').replace('-', '').replace('_', '')

def clean_data(df):
    """
    Cleans the input DataFrame:
    - Converts 'date' column to datetime.
    - Fills missing 'engagements' with 0.
    - Normalizes all column names.
    - Filters out rows with invalid dates.
    """
    st.subheader("2. Data Cleaning Summary")
    st.markdown("""
    - 'Date' column converted to datetime objects. Invalid dates were filtered out.
    - Missing 'Engagements' values filled with 0.
    - Column names normalized (e.g., 'Media Type' became 'mediatype').
    """)

    original_rows = len(df)
    st.info(f"Original number of rows: {original_rows}")

    # Normalize column names
    df.columns = [normalize_column_name(col) for col in df.columns]

    # Ensure all required columns are present
    expected_columns = ['date', 'platform', 'sentiment', 'location', 'engagements', 'mediatype']
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Error: Missing required columns in CSV: {', '.join(missing_columns)}. Please ensure your CSV has 'Date', 'Platform', 'Sentiment', 'Location', 'Engagements', 'Media Type' columns.")
        st.stop() # Stop execution if critical columns are missing

    # Convert 'date' to datetime, handling errors with multiple formats
    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
    df['date'] = pd.to_datetime(df['date'], errors='coerce', format=date_formats)
    df.dropna(subset=['date'], inplace=True) # Drop rows where date conversion failed
    rows_after_date_clean = len(df)
    if rows_after_date_clean < original_rows:
        st.warning(f"Removed {original_rows - rows_after_date_clean} rows due to invalid 'Date' formats.")

    # Fill missing 'engagements' with 0 and convert to integer
    df['engagements'] = pd.to_numeric(df['engagements'], errors='coerce').fillna(0).astype(int)

    st.success(f"Successfully processed {len(df)} rows of data after cleaning.")
    return df

def get_gemini_insight(prompt_text):
    """Fetches insights from the Gemini API."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return "Gemini API key is not configured. Please set your API key to generate insights."

    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }
    # Using gemini-1.5-flash-latest model as specified in the last React app
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result and result.get('candidates'):
            first_candidate = result['candidates'][0]
            if first_candidate.get('content') and first_candidate['content'].get('parts'):
                return first_candidate['content']['parts'][0]['text']
        return "Could not generate insights for this chart."
    except requests.exceptions.RequestException as e:
        return f"Error calling Gemini API: {e}. Please ensure your API key is valid for the Google Generative Language API and has access to 'gemini-1.5-flash-latest'. Also, check your network connection."
    except Exception as e:
        return f"An unexpected error occurred while getting insights: {e}"

# --- Streamlit App ---

st.title("Interactive Media Intelligence Dashboard")
st.markdown("Gain insights from your media data with interactive charts.")

st.markdown("""
<style>
    .stApp {
        background-color: #e0f2fe; /* light blue-50 */
        font-family: 'Inter', sans-serif;
        color: #333;
    }
    .stFileUploader label {
        color: #4338ca; /* indigo-700 */
    }
    .stButton>button {
        background-color: #4f46e5; /* indigo-600 */
        color: white;
        font-weight: bold;
        border-radius: 0.5rem; /* rounded-lg */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4338ca; /* indigo-700 */
        transform: scale(1.05);
    }
    .stAlert {
        border-radius: 0.5rem;
    }
    /* Streamlit's div for main block content that mimics React's outer container */
    div[data-testid="stVerticalBlock"] > div:first-child {
        background-color: white;
        border-radius: 0.75rem; /* rounded-xl */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* shadow-xl */
        padding: 2rem; /* p-8 */
    }
    /* Specific styles for chart sections within the main block */
    .chart-section {
        background-color: #ffffff; /* white */
        padding: 1.5rem; /* p-6 */
        border-radius: 0.5rem; /* rounded-lg */
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); /* shadow-md */
        margin-bottom: 2rem; /* mb-8 */
    }
    h2 {
        color: #1a202c; /* gray-800 */
        font-weight: 600; /* font-semibold */
        font-size: 1.5rem; /* text-2xl */
        margin-bottom: 1.5rem; /* mb-6 */
    }
    h3 {
        color: #374151; /* gray-700 */
        font-weight: 600; /* font-semibold */
        font-size: 1.25rem; /* text-xl */
        margin-bottom: 1rem; /* mb-4 */
    }
    h4 {
        color: #374151; /* gray-700 */
        font-weight: 500; /* font-medium */
        font-size: 1rem; /* text-base */
        margin-bottom: 0.5rem; /* mb-2 */
    }
    .stMarkdown p {
        color: #4b5563; /* gray-700 */
    }
    .stSpinner > div {
        color: #4338ca; /* indigo-700 */
    }
    .code-style {
        background-color:#e2e8f0;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


st.header("1. Upload Your CSV File")
st.markdown(f"""
Please upload a CSV file with the following columns: <code class="code-style">Date</code>, <code class="code-style">Platform</code>, <code class="code-style">Sentiment</code>, <code class="code-style">Location</code>, <code class="code-style">Engagements</code>, <code class="code-style">Media Type</code>.
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader("", type=["csv"], key="csv_uploader")

df = None
if uploaded_file is not None:
    with st.spinner("Processing data..."):
        try:
            # Read CSV directly from uploaded file buffer
            df = pd.read_csv(uploaded_file)
            st.session_state['original_df'] = df.copy() # Store original for potential re-use
            df = clean_data(df.copy()) # Pass a copy to avoid modifying original
            st.session_state['cleaned_df'] = df # Store cleaned data in session state
            st.success("CSV file uploaded and data cleaned successfully!")

        except Exception as e:
            st.error(f"Error reading or cleaning CSV: {e}")
            df = None # Reset df to None on error

# Retrieve df from session state if available (prevents reprocessing on rerun)
if 'cleaned_df' in st.session_state and st.session_state['cleaned_df'] is not None:
    df = st.session_state['cleaned_df']

if df is not None and not df.empty:
    # Data Cleaning Summary Section
    st.markdown(
        f'<div class="chart-section" style="background-color: #eff6ff; border-color: #bfdbfe;">'
        f'<h2 style="color: #1e40af;">2. Data Cleaning Summary</h2>'
        f'<ul style="color: #4b5563; list-style-type: disc; margin-left: 1.5em;">'
        f'<li>\'Date\' column converted to datetime objects. Invalid dates were filtered out.</li>'
        f'<li>Missing \'Engagements\' values filled with 0.</li>'
        f'<li>Column names normalized (e.g., \'Media Type\' became \'mediatype\').</li>'
        f'</ul>'
        f'<p style="color: #4b5563;">Successfully processed <span style="font-weight: bold; color: #4338ca;">{len(df)}</span> rows of data.</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.header("3. Interactive Charts")

    # Chart 1: Sentiment Breakdown (Pie Chart)
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.subheader("Sentiment Breakdown")
    sentiment_counts = df['sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['Sentiment', 'Count']
    fig_sentiment = px.pie(
        sentiment_counts,
        values='Count',
        names='Sentiment',
        title='Sentiment Breakdown',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_sentiment.update_layout(
        title_font_size=24,
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=-0.1,
        legend_xanchor="center",
        legend_x=0.5,
        height=400
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)

    with st.spinner("Generating insights for Sentiment Breakdown..."):
        prompt_sentiment = f"""Given the following sentiment distribution from a media dataset: {sentiment_counts.to_dict('records')}.
        Provide 3 key insights about the overall sentiment. Focus on the most prevalent sentiments and any notable imbalances.
        Present insights as plain text, using bullet points for readability. Also mention the dominant sentiment and why it is important."""
        insights_sentiment = get_gemini_insight(prompt_sentiment)
        st.markdown(f'<div style="background-color: #f8f8f8; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">'
                    f'<h4 style="color: #374151;">Top 3 Insights:</h4>'
                    f'<p style="color: #4b5563; white-space: pre-wrap;">{insights_sentiment}</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # Close chart-section

    # Chart 2: Engagement Trend over time (Line Chart)
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.subheader("Engagement Trend Over Time")
    # Group by date and sum engagements for the trend
    engagement_trend = df.groupby(df['date'].dt.to_period('D'))['engagements'].sum().reset_index()
    engagement_trend['date'] = engagement_trend['date'].astype(str) # Convert Period to string for Plotly
    fig_engagement = px.line(
        engagement_trend,
        x='date',
        y='engagements',
        title='Engagement Trend Over Time',
        markers=True
    )
    fig_engagement.update_layout(
        title_font_size=24,
        xaxis_title="Date",
        yaxis_title="Total Engagements",
        xaxis_rangeslider_visible=True, # Add range slider
        height=400
    )
    st.plotly_chart(fig_engagement, use_container_width=True)

    with st.spinner("Generating insights for Engagement Trend..."):
        prompt_engagement = f"""Analyze the following engagement data over time: {engagement_trend.to_dict('records')}.
        Describe the trend of engagements over the period. Are there any peaks, troughs, or consistent patterns?
        Give 3 key insights. Present insights as plain text, using bullet points for readability.
        Highlight any significant spikes or drops in engagement."""
        insights_engagement = get_gemini_insight(prompt_engagement)
        st.markdown(f'<div style="background-color: #f8f8f8; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">'
                    f'<h4 style="color: #374151;">Top 3 Insights:</h4>'
                    f'<p style="color: #4b5563; white-space: pre-wrap;">{insights_engagement}</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # Close chart-section

    # Chart 3: Platform Engagements (Bar Chart)
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.subheader("Platform Engagements")
    platform_engagements = df.groupby('platform')['engagements'].sum().reset_index()
    platform_engagements = platform_engagements.sort_values('engagements', ascending=False)
    fig_platform = px.bar(
        platform_engagements,
        x='platform',
        y='engagements',
        title='Platform Engagements',
        color='platform', # Assign color based on platform
        color_discrete_sequence=px.colors.qualitative.Dark24 # Use a diverse color sequence
    )
    fig_platform.update_layout(
        title_font_size=24,
        xaxis_title="Platform",
        yaxis_title="Total Engagements",
        height=400
    )
    st.plotly_chart(fig_platform, use_container_width=True)

    with st.spinner("Generating insights for Platform Engagements..."):
        prompt_platform = f"""Based on the total engagements per platform: {platform_engagements.to_dict('records')}.
        What are the top platforms driving engagements? Are there any platforms significantly underperforming?
        Provide 3 key insights. Present insights as plain text, using bullet points for readability.
        Identify top performing platforms."""
        insights_platform = get_gemini_insight(prompt_platform)
        st.markdown(f'<div style="background-color: #f8f8f8; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">'
                    f'<h4 style="color: #374151;">Top 3 Insights:</h4>'
                    f'<p style="color: #4b5563; white-space: pre-wrap;">{insights_platform}</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # Close chart-section

    # Chart 4: Media Type Mix (Pie Chart)
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.subheader("Media Type Mix")
    mediatype_counts = df['mediatype'].value_counts().reset_index()
    mediatype_counts.columns = ['MediaType', 'Count']
    fig_mediatype = px.pie(
        mediatype_counts,
        values='Count',
        names='MediaType',
        title='Media Type Mix',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_mediatype.update_layout(
        title_font_size=24,
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=-0.1,
        legend_xanchor="center",
        legend_x=0.5,
        height=400
    )
    st.plotly_chart(fig_mediatype, use_container_width=True)

    with st.spinner("Generating insights for Media Type Mix..."):
        prompt_mediatype = f"""Given the distribution of media types: {mediatype_counts.to_dict('records')}.
        What are the most common media types used? Is there a significant preference for certain types?
        Give 3 key insights. Present insights as plain text, using bullet points for readability.
        Discuss the most prevalent media type."""
        insights_mediatype = get_gemini_insight(prompt_mediatype)
        st.markdown(f'<div style="background-color: #f8f8f8; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">'
                    f'<h4 style="color: #374151;">Top 3 Insights:</h4>'
                    f'<p style="color: #4b5563; white-space: pre-wrap;">{insights_mediatype}</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # Close chart-section

    # Chart 5: Top 5 Locations (Bar Chart)
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.subheader("Top 5 Locations by Engagements")
    location_engagements = df.groupby('location')['engagements'].sum().reset_index()
    location_engagements = location_engagements.sort_values('engagements', ascending=False).head(5)
    fig_location = px.bar(
        location_engagements,
        x='location',
        y='engagements',
        title='Top 5 Locations by Engagements',
        color='location', # Assign color based on location
        color_discrete_sequence=px.colors.qualitative.Vivid # Use a diverse color sequence
    )
    fig_location.update_layout(
        title_font_size=24,
        xaxis_title="Location",
        yaxis_title="Total Engagements",
        height=400
    )
    st.plotly_chart(fig_location, use_container_width=True)

    with st.spinner("Generating insights for Top 5 Locations..."):
        prompt_location = f"""Here are the top 5 locations by engagements: {location_engagements.to_dict('records')}.
        What does this data tell us about geographical engagement? Are there specific regions that are highly active?
        Provide 3 key insights. Present insights as plain text, using bullet points for readability.
        Point out the most engaged locations."""
        insights_location = get_gemini_insight(prompt_location)
        st.markdown(f'<div style="background-color: #f8f8f8; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">'
                    f'<h4 style="color: #374151;">Top 3 Insights:</h4>'
                    f'<p style="color: #4b5563; white-space: pre-wrap;">{insights_location}</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # Close chart-section
