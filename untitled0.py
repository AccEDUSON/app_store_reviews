import streamlit as st
import requests
import pandas as pd
import re
import sys

if sys.version_info < (3, 10):
    st.error("Требуется Python 3.10 или выше")
    sys.exit(1)

st.set_page_config(
    page_title="App Store Reviews Scraper",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Сборщик отзывов из App Store")
st.markdown("Введите ссылку на приложение в App Store, чтобы собрать все отзывы.")

# Форма ввода
with st.form("review_scraper_form"):
    app_store_url = st.text_input(
        "Ссылка на приложение в App Store",
        placeholder="Например: https://apps.apple.com/us/app/duolingo/id570060128",
        value=""
    )
    max_reviews = st.slider(
        "Максимальное количество отзывов",
        min_value=10,
        max_value=500,
        value=100,
        help="API App Store может ограничить количество отзывов"
    )
    submitted = st.form_submit_button("🔎 Собрать отзывы")


def extract_app_data(url):
    id_match = re.search(r'id(\d+)', url)
    if not id_match:
        raise ValueError("Не удалось найти ID приложения в ссылке. Убедитесь, что ссылка корректна.")
    app_id = id_match.group(1)
    country_match = re.search(r'apps\.apple\.com/(\w{2})/', url)
    country = country_match.group(1) if country_match else 'us'
    return app_id, country

def fetch_reviews_api(app_id, country, max_reviews):
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
    reviews_data = []
    try:
        with st.spinner("Загружаю отзывы..."):
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                entries = data.get('feed', {}).get('entry', [])
                if not entries:
                    st.warning("⚠️