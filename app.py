import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ── Инициализация Firebase ──────────────────────────────────────────────
KEY_PATH = os.getenv("FIREBASE_KEY", "serviceAccountKey.json")

if not firebase_admin._apps:
    if not os.path.exists(KEY_PATH):
        st.error("❌ Файл serviceAccountKey.json не найден. Поместите его в папку проекта.")
        st.stop()
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ── Настройка страницы ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Опрос: Система баллов в образовании",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Отношение к системе баллов в образовании")
st.caption(
    "Анонимный опрос для исследования восприятия балльной системы оценивания. Данные собираются в образовательных целях.")

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
        st.balloons()
    except Exception as e:
        st.error(f"❌ Ошибка при сохранении: {e}")

# ── Аналитика (режим преподавателя) ──────────────────────────────────────
st.markdown("---")
st.subheader("🔒 Панель аналитики")

if st.checkbox("Показать аналитику (Instructor View)", value=False):
    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("📭 Пока нет собранных данных.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.success(f"📥 Загружено записей: **{len(df)}**")

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
                color_discrete_sequence=["#636EFA"]
            )
            fig_fair.update_layout(bargap=0.1)
            st.plotly_chart(fig_fair, use_container_width=True)

        with col_v2:
            # Распределение мотивации
            fig_mot = px.histogram(
                df, x="motivation", nbins=10,
                title="Распределение: Мотивация к учёбе",
                labels={"motivation": "Оценка мотивации (1–10)", "count": "Количество"},
                color_discrete_sequence=["#00CC96"]
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
            name='Средние значения'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
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
            color_discrete_sequence=px.colors.qualitative.Set2
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