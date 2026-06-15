import streamlit as st
import requests
import pandas as pd
import re
import time
import sys

if sys.version_info < (3, 10):
    st.error("Требуется Python 3.10 или выше")
    sys.exit(1)


def extract_app_data(url):
    """Извлекает ID приложения и код страны из URL App Store."""
    id_match = re.search(r'id(\d+)', url)
    if not id_match:
        raise ValueError("Не удалось найти ID приложения в ссылке.")
    app_id = id_match.group(1)

    country_match = re.search(r'apps\.apple\.com/(\w{2})/', url)
    country = country_match.group(1) if country_match else 'us'
    return app_id, country

def fetch_reviews_api(app_id, country, max_reviews=500):
    """Собирает отзывы через API App Store с улучшенной обработкой данных."""
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
    reviews_data = []

    st.info(f"Начинаю сбор отзывов для приложения ID: {app_id}, страна: {country}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])

            for entry in entries:
                # Пропускаем заголовок фида
                if 'im:name' in entry:
                    continue

                # Извлекаем и очищаем данные
                author = entry.get('author', {}).get('name', {}).get('label', 'Не указан')
                title = entry.get('title', {}).get('label', 'Без заголовка')
                content = entry.get('content', {}).get('label', 'Отзыв отсутствует')
                rating = entry.get('im:rating', {}).get('label', 'N/A')
                version = entry.get('im:version', {}).get('label', 'N/A')

                # Форматируем дату: оставляем только год-месяц-день
                date_full = entry.get('updated', {}).get('label', '')
                date = date_full.split('T')[0] if date_full else 'N/A'

                reviews_data.append({
                    'Автор отзыва': author,
                    'Рейтинг (звёзды)': rating,
                    'Заголовок': title,
                    'Текст отзыва': content,
                    'Дата публикации': date,
            'Версия приложения': version,
            'Отредактировано': 'Нет'  # API не предоставляет эту информацию
                })

            st.success(f"✅ Собрано {len(reviews_data)} отзывов.")
        else:
            st.error(f"❌ Ошибка API: HTTP {response.status_code}")
    except Exception as e:
        st.error(f"❌ Ошибка при запросе к API: {e}")

    return reviews_data

def save_to_csv_formatted(reviews_data, filename='app_reviews_formatted.csv'):
    """Сохраняет данные в CSV с улучшенной структурой и кодировкой."""
    if not reviews_data:
        st.warning("❌ Нет данных для сохранения.")
        return None

    df = pd.DataFrame(reviews_data)

    # Сортируем по дате (новые сверху)
    df['Дата публикации'] = pd.to_datetime(df['Дата публикации'], errors='coerce')
    df = df.sort_values(by='Дата публикации', ascending=False).reset_index(drop=True)

    # Форматируем рейтинг: добавляем звёздочки визуально
    def format_rating(rating):
        try:
            num = int(rating)
            return f"{rating} ⭐"
        except:
            return rating

    df['Рейтинг (звёзды)'] = df['Рейтинг (звёзды)'].apply(format_rating)

    # Ограничиваем длину текста отзыва для CSV
    df['Текст отзыва'] = df['Текст отзыва'].str[:500] + '...'

    # Сохраняем с улучшенной кодировкой и форматированием
    df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
    return df

# Интерфейс Streamlit
st.set_page_config(
    page_title="Сбор отзывов из App Store",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Сбор отзывов из App Store")
st.markdown("Введите ссылку на приложение в App Store для сбора отзывов.")

# Поле ввода URL
app_store_url = st.text_input(
    "Ссылка на приложение в App Store:",
    value="https://apps.apple.com/us/app/duolingo/id570060128",
    help="Пример: https://apps.apple.com/us/app/app-name/id123456789"
)

# Кнопка запуска сбора данных
if st.button("🔎 Собрать отзывы"):
    if not app_store_url:
        st.warning("Пожалуйста, введите ссылку на приложение.")
    else:
        try:
            with st.spinner("Извлекаем данные..."):
                app_id, country = extract_app_data(app_store_url)
                reviews = fetch_reviews_api(app_id, country)
                df = save_to_csv_formatted(reviews)

            if df is not None and not df.empty:
                st.success("✅ Данные успешно собраны и обработаны!")

                # Отображаем таблицу с отзывами
                st.subheader("📊 Полученные отзывы")
                st.dataframe(df, use_container_width=True)

                # Статистика
                st.subheader("📈 Статистика")
                col1, col2, col3 = st.columns(3)
                col1.metric("Всего отзывов", len(df))
                avg_rating = pd.to_numeric(df['Рейтинг (звёзды)'].str.replace(' ⭐', ''), errors='coerce').mean()
                col2.metric("Средний рейтинг", f"{avg_rating:.1f} ⭐")
                col3.metric("Версии приложения", df['Версия приложения'].nunique())

                # Кнопка для скачивания CSV
                csv = df.to_csv(index=False, encoding='utf-8-sig', sep=';').encode('utf-8-sig')
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv,
            file_name='app_reviews_formatted.csv',
            mime='text/csv'
                )

        except Exception as e:
            st.error(f"❌ Произошла ошибка: {e}")

# Боковая панель с информацией
st.sidebar.header("🔎 Информация")
st.sidebar.info("""
Этот инструмент собирает отзывы из App Store по указанной ссылке.

**Как использовать:**
1. Введите ссылку на приложение
2. Нажмите «Собрать отзывы»
3. Просмотрите результаты и скачайте CSV

**Поддерживаемые форматы:**
- Ссылки на приложения в App Store
- Автоматическое определение ID и страны
""")
