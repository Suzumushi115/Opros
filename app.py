import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
# ═══ КАСТОМНЫЕ СТИЛИ: фиолетовая тема ═══════════════════════════════════
st.markdown("""
<style>
    /* Фиолетовый градиент заголовка */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1, .main-header p {
        color: white !important;
    }
    
    /* Красивые карточки — работает в обеих темах */
    .stForm {
        background: linear-gradient(145deg, #f3e7ff 0%, #e9d5ff 100%);
        border-radius: 1rem;
        padding: 1rem;
        border: 2px solid #c084fc;
    }
    [data-testid="stForm"] label, [data-testid="stForm"] span {
        color: #4c1d95 !important;
    }
    
    /* Кнопка отправки */
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%) !important;
        color: white !important;
        border-radius: 0.8rem !important;
        border: none !important;
        padding: 0.8rem 2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Слайдеры фиолетовые */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #8b5cf6 !important;
    }
    
    /* Успешное сообщение */
    .stSuccess {
        background: linear-gradient(135deg, #d8b4fe 0%, #c084fc 100%) !important;
        border: 2px solid #a855f7 !important;
        border-radius: 1rem !important;
    }
    .stSuccess p {
        color: #4c1d95 !important;
    }
    
    /* Метрики */
    [data-testid="stMetricValue"] {
        color: #7c3aed !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6b21a8 !important;
    }
    
    /* Разделитель */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #c084fc, #8b5cf6, #c084fc);
        margin: 2rem 0;
    }
    
    /* Подписи к графикам */
    .stPlotlyChart {
        background: rgba(243, 231, 255, 0.05) !important;
        border-radius: 1rem;
    }
    
    /* Чекбокс и радио — тёмная тема */
    [data-testid="stCheckbox"] label, [data-testid="stRadio"] label {
        color: inherit !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid #c084fc !important;
        border-radius: 0.5rem;
    }
    
    /* Expander */
    .stExpander {
        border: 1px solid #c084fc !important;
        border-radius: 0.5rem;
    }
      /* Тёмный текст внутри селектбоксов */
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: #4c1d95 !important;
    }
    
    /* Тёмный текст в радиокнопках */
    [data-testid="stMarkdownContainer"] p {
        color: #4c1d95 !important;
    }
    
    /* Тёмный текст в дропдаунах */
    .stSelectbox [data-baseweb="popover"] div {
        color: #4c1d95 !important;
    }
</style>
""", unsafe_allow_html=True)# ── Инициализация Firebase через Streamlit Secrets ─────────────────────
if not firebase_admin._apps:
    try:
        firebase_config = st.secrets["firеbase_key"]
        # Преобразуем секреты в формат credentials
        cred = credentials.Certificate(dict(firebase_config))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Ошибка инициализации Firebase: {e}")
        st.stop()

db = firestore.client()

# ── Настройка страницы ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Опрос: Система баллов в образовании",
    page_icon="📊",
    layout="wide"
)

# Красивый фиолетовый заголовок
st.markdown("""
<div class="main-header">
    <h1>📊 Отношение к системе баллов в образовании</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">
        Анонимный опрос для исследования восприятия балльной системы оценивания
    </p>
</div>
""", unsafe_allow_html=True)
# Счётчик ответов
try:
    count = len(list(db.collection("responses").stream()))
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span style="
            background: linear-gradient(135deg, #8b5cf6, #a855f7);
            color: white;
            padding: 0.4rem 1.2rem;
            border-radius: 2rem;
            font-size: 0.9rem;
            font-weight: 600;
        ">
            📝 Уже собрано ответов: {count}
        </span>
    </div>
    """, unsafe_allow_html=True)
except:
    pass
# ── Форма опроса ──────────────────────────────────────────────────────────
with st.form("survey_form"):
    st.subheader("Заполните форму")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Ваш возраст", min_value=14, max_value=80, step=1, value=18)
        gender = st.radio("Пол", ["Мужской", "Женский", "Предпочитаю не указывать"])
        education_level = st.selectbox(
            "Уровень обучения",
            ["Среднее общее", "Среднее профессиональное", "Бакалавриат", "Магистратура", "Аспирантура", "Другое"]
        )
        year_of_study = st.selectbox(
            "Курс / Стаж обучения",
            ["1 курс", "2 курс", "3 курс", "4 курс", "5+ курс", "Выпускник", "Преподаватель", "Другое"]
        )

    with col2:
        fairness = st.slider(
            "Насколько справедливой вы считаете балльную систему оценивания? (1 — совсем несправедлива, 10 — абсолютно справедлива)",
            1, 10, 5
        )
        motivation = st.slider(
            "Насколько балльная система мотивирует вас к учёбе? (1 — демотивирует, 10 — сильно мотивирует)",
            1, 10, 5
        )
        stress = st.slider(
            "Какой уровень стресса вызывает балльная система? (1 — никакого, 10 — крайне высокий)",
            1, 10, 5
        )

    st.markdown("---")

    # Множественный выбор
    criteria = st.multiselect(
        "Какие критерии, по вашему мнению, должны учитываться в балльной системе? (выберите все подходящие)",
        [
            "Посещаемость",
            "Активность на занятиях",
            "Выполнение домашних заданий",
            "Промежуточные тесты",
            "Проектная работа",
            "Экзамен / Зачёт",
            "Командная работа",
            "Самостоятельная работа",
            "Творческие задания",
            "Другое"
        ]
    )

    comparison = st.radio(
        "Что вы предпочитаете?",
        ["Традиционную пятибалльную систему (2–5)", "Балльную систему (0–100 или иная)", "Зачёт / Незачёт",
         "Портфолио без цифровых оценок", "Другое"]
    )

    comment = st.text_area(
        "Дополнительные комментарии (по желанию)",
        placeholder="Расскажите о своём опыте с балльной системой, предложениях по улучшению и т.д."
    )

       # Прогресс-бар заполнения
    st.markdown("---")
    progress = st.progress(0, text="Заполните форму")
    
    # Считаем заполненность (простая эвристика)
    filled = 0
    if age != 18: filled += 1
    if gender: filled += 1
    if education_level: filled += 1
    if year_of_study: filled += 1
    if fairness != 5: filled += 1
    if motivation != 5: filled += 1
    if stress != 5: filled += 1
    if criteria: filled += 1
    if comparison: filled += 1
    if comment: filled += 1
    
    progress.progress(min(filled / 10, 1.0), text=f"Заполнено: {filled}/10")
    submitted = st.form_submit_button("📤 Отправить ответ", use_container_width=True)
# ── Сохранение данных ───────────────────────────────────────────────────
if submitted:
    doc_data = {
        "age": int(age),
        "gender": gender,
        "education_level": education_level,
        "year_of_study": year_of_study,
        "fairness": int(fairness),
        "motivation": int(motivation),
        "stress": int(stress),
        "criteria": criteria,
        "comparison": comparison,
        "comment": comment,
        "timestamp": datetime.utcnow()
    }

    try:
        db.collection("responses").add(doc_data)
        st.success("✅ Спасибо! Ваш ответ сохранён в облачной базе данных.")
        
        # Фиолетовые шарики-конфетти
        import time
        for _ in range(3):
            st.balloons()
            time.sleep(0.3)
        
        # Благодарственная карточка
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f3e7ff, #e9d5ff);
            border-radius: 1rem;
            padding: 1.5rem;
            border-left: 5px solid #8b5cf6;
            margin-top: 1rem;
        ">
            <h3 style="color: #7c3aed; margin: 0;">🎉 Спасибо за участие!</h3>
            <p style="color: #6b21a8; margin: 0.5rem 0 0 0;">
                Ваше мнение помогает сделать образование лучше.
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Ошибка при сохранении: {e}")
        
        # Фиолетовые шарики-конфетти
        import time
        colors = ["#8b5cf6", "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff"]
        for _ in range(3):
            st.balloons()
            time.sleep(0.3)
        
        # Благодарственная карточка
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f3e7ff, #e9d5ff);
            border-radius: 1rem;
            padding: 1.5rem;
            border-left: 5px solid #8b5cf6;
            margin-top: 1rem;
        ">
            <h3 style="color: #7c3aed; margin: 0;">🎉 Спасибо за участие!</h3>
            <p style="color: #6b21a8; margin: 0.5rem 0 0 0;">
                Ваше мнение помогает сделать образование лучше.
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Ошибка при сохранении: {e}")

# ── Аналитика (режим преподавателя) ──────────────────────────────────────
st.markdown("---")
st.subheader("🔒 Панель аналитики")

if st.checkbox("🔮 Показать аналитику (Instructor View)", value=False):
    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("📭 Пока нет собранных данных.")
    else:
        df = pd.DataFrame(data)
               # Красивый индикатор загрузки
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #f3e7ff, #e9d5ff, #f3e7ff);
            background-size: 200% 100%;
            animation: shimmer 2s infinite;
            height: 4px;
            border-radius: 2px;
            margin: 1rem 0;
        ">
        <style>
            @keyframes shimmer {
                0% { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }
        </style>
        </div>
        """, unsafe_allow_html=True)

        # ── Общая сводка ─────────────────────────────────────────────────
        st.subheader("📋 Сводка данных")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Средняя справедливость", f"{df['fairness'].mean():.1f}/10")
        with col_b:
            st.metric("Средняя мотивация", f"{df['motivation'].mean():.1f}/10")
        with col_c:
            st.metric("Средний стресс", f"{df['stress'].mean():.1f}/10")

        st.dataframe(df.head(20), use_container_width=True)

        # ── Визуализации ───────────────────────────────────────────────
        st.subheader("📈 Визуализация результатов")

        col_v1, col_v2 = st.columns(2)

        with col_v1:
            # Распределение оценки справедливости
            fig_fair = px.histogram(
                df, x="fairness", nbins=10,
                title="Распределение: Справедливость системы",
                labels={"fairness": "Оценка справедливости (1–10)", "count": "Количество"},
                color_discrete_sequence=["#8b5cf6"]
            )
            fig_fair.update_layout(bargap=0.1)
            st.plotly_chart(fig_fair, use_container_width=True)

        with col_v2:
            # Распределение мотивации
            fig_mot = px.histogram(
                df, x="motivation", nbins=10,
                title="Распределение: Мотивация к учёбе",
                labels={"motivation": "Оценка мотивации (1–10)", "count": "Количество"},
                color_discrete_sequence=["#a855f7"]
            )
            fig_mot.update_layout(bargap=0.1)
            st.plotly_chart(fig_mot, use_container_width=True)

        # Радар-график: сравнение средних
        st.subheader("🎯 Средние показатели (радар)")
        categories = ["Справедливость", "Мотивация", "Стресс"]
        values = [
            df["fairness"].mean(),
            df["motivation"].mean(),
            df["stress"].mean()
        ]

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(139, 92, 246, 0.3)',
            line=dict(color='#8b5cf6', width=3),
            name='Средние значения'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], gridcolor='#e9d5ff'),
                bgcolor='#faf5ff'
            ),
            paper_bgcolor='white',
            showlegend=False,
            title="Средние оценки по трём ключевым метрикам"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Распределение по уровню образования
        st.subheader("🎓 Распределение по уровню образования")
        edu_counts = df["education_level"].value_counts().reset_index()
        edu_counts.columns = ["Уровень образования", "Количество"]
        fig_edu = px.pie(
            edu_counts, values="Количество", names="Уровень образования",
            title="Участники по уровню образования"
        )
        st.plotly_chart(fig_edu, use_container_width=True)

        # Предпочтения системы оценивания
        st.subheader("⚖️ Предпочтения системы оценивания")
        comp_counts = df["comparison"].value_counts().reset_index()
        comp_counts.columns = ["Система оценивания", "Количество"]
        fig_comp = px.bar(
            comp_counts, x="Система оценивания", y="Количество",
            title="Что предпочитают респонденты",
            color="Система оценивания",
            color_discrete_sequence=px.colors.sequential.Purples

        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Частота выбора критериев
        st.subheader("✅ Наиболее важные критерии оценивания")
        all_criteria = [item for sublist in df["criteria"].dropna() for item in sublist]
        crit_series = pd.Series(all_criteria).value_counts().reset_index()
        crit_series.columns = ["Критерий", "Количество выборов"]
        fig_crit = px.bar(
            crit_series, x="Количество выборов", y="Критерий",
            title="Какие критерии считают важными",
            orientation='h',
            color="Количество выборов",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_crit, use_container_width=True)

        # Временная динамика
        st.subheader("🕐 Динамика поступления ответов")
        df["date"] = df["timestamp"].dt.date
        daily = df.groupby("date").size().reset_index(name="Количество")
        fig_time = px.line(
            daily, x="date", y="Количество",
            title="Количество ответов по дням",
            markers=True
        )
        st.plotly_chart(fig_time, use_container_width=True)

        # Комментарии
        st.subheader("💬 Комментарии респондентов")
        comments = df[df["comment"].str.strip() != ""]["comment"].dropna().tolist()
        if comments:
            for i, c in enumerate(comments[:10], 1):
                with st.expander(f"Комментарий #{i}"):
                    st.write(c)
        else:
            st.info("Комментариев пока нет.")
