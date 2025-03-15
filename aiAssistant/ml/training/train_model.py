import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import RandomOverSampler
import joblib

# === Шаг 1: Загрузка данных ===
df = pd.read_csv("../data/training_data.csv")  # Убедитесь, что файл находится в той же директории

# Проверка данных
print(df.head())

# Проверка распределения классов
print("Распределение классов до балансировки:")
print(df["doctor_specialty"].value_counts())

# === Шаг 2: Токенизация и преобразование текста в числовые признаки ===
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X = vectorizer.fit_transform(df["symptoms"]).toarray()  # Преобразуем симптомы в числовые признаки

# Целевая переменная (специализация врача)
y = df["doctor_specialty"]

# === Шаг 3: Балансировка данных ===
ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)

# Проверка распределения классов после балансировки
print("Распределение классов после балансировки:")
print(pd.Series(y_resampled).value_counts())

# === Шаг 4: Разделение данных на обучающую и тестовую выборки ===
X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=52)

# === Шаг 5: Обучение модели SVM ===
model = SVC(kernel="linear", probability=True)  # Используем линейное ядро для SVM
model.fit(X_train, y_train)  # Обучаем модель

# === Шаг 6: Оценка модели ===
y_pred = model.predict(X_test)
print("Точность модели:", accuracy_score(y_test, y_pred))
print("Отчёт по классификации:\n", classification_report(y_test, y_pred))

# === Шаг 7: Сохранение модели и векторизатора ===
joblib.dump(model, "../models/svm_model.pkl")  # Сохраняем модель
joblib.dump(vectorizer, "../models/tfidf_vectorizer.pkl")  # Сохраняем векторизатор

# Сохраняем рекомендации в отдельный файл
recommendations_dict = dict(zip(df["symptoms"], df["recommendations"]))
joblib.dump(recommendations_dict, "../models/recommendations_dict.pkl")

print("✅ Модель и векторизатор сохранены!")