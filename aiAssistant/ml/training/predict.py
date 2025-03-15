from pathlib import Path

import joblib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent  # Переходим на два уровня выше
MODELS_DIR = BASE_DIR / "models"  # Путь к папке с моделями

# Загружаем модель, векторизатор и рекомендации
model = joblib.load(MODELS_DIR / "svm_model.pkl")
vectorizer = joblib.load(MODELS_DIR / "tfidf_vectorizer.pkl")
recommendations_dict = joblib.load(MODELS_DIR / "recommendations_dict.pkl")

def find_most_similar_symptom(input_symptoms, vectorizer, symptoms_list):
    input_vector = vectorizer.transform([input_symptoms]).toarray()
    symptoms_vectors = vectorizer.transform(symptoms_list).toarray()
    similarities = cosine_similarity(input_vector, symptoms_vectors)
    most_similar_index = np.argmax(similarities)
    return symptoms_list[most_similar_index]


def predict_specialist_and_recommendation(symptoms):

    # Разбиваем введённые симптомы на отдельные части
    symptoms_parts = [part.strip() for part in symptoms.split(",")]  # Разделяем по запятым и убираем пробелы
    combined_advice = set()  # Используем множество для хранения уникальных советов

    # Для каждой части симптомов ищем рекомендации
    for symptom_part in symptoms_parts:
        most_similar_symptom = find_most_similar_symptom(symptom_part, vectorizer, list(recommendations_dict.keys()))
        recommendation = recommendations_dict.get(most_similar_symptom, "")
        if recommendation:  # Добавляем рекомендацию, если она найдена
            # Разбиваем рекомендацию на отдельные советы
            advice_list = [advice.strip() for advice in recommendation.split(",")]
            # Добавляем каждый совет в множество
            for advice in advice_list:
                combined_advice.add(advice.lower())  # Приводим к нижнему регистру

    # Объединяем советы в одну строку через запятую
    if combined_advice:
        recommendation = ", ".join(combined_advice)  # Объединяем уникальные советы
    else:
        recommendation = "Рекомендации не найдены."

    return recommendation

#
# if __name__ == "__main__":
#     symptoms_input = "повышенное давление, отеки"
#     specialist, recommendation = predict_specialist_and_recommendation(symptoms_input)
#     print(f"Предполагаемый врач: {specialist}")
#     print(f"Рекомендации: {recommendation}. "
#           f"\nВсе рекомендации носят справочный характер. Помните, что обязательно необходимо проконсультироваться с врачом!")