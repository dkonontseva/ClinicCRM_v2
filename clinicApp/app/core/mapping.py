SPECIALTY_MAPPING = {
    "neurology": ["невролог", "неврология"],
    "cardiology": ["кардиолог", "кардиология"],
    "therapy": ["терапевт", "терапия"],
    "ophthalmology": ["офтальмолог", "офтальмология"],
    "dentistry": ["стоматолог", "стоматология"],
    "surgery": ["хирург", "хирургия"],
}

# Обратный маппинг для поиска по русским названиям
REVERSE_SPECIALTY_MAPPING = {
    russian: eng
    for eng, russian_list in SPECIALTY_MAPPING.items()
    for russian in russian_list
}

def get_department_name(specialty: str) -> str:
    """Преобразует специальность из ответа ассистента в название отделения"""
    specialty_lower = specialty.lower()
    
    # Проверяем прямое совпадение с ключами
    if specialty_lower in SPECIALTY_MAPPING:
        return SPECIALTY_MAPPING[specialty_lower][0]
    
    # Проверяем совпадение с русскими названиями
    if specialty_lower in REVERSE_SPECIALTY_MAPPING:
        return specialty_lower
    
    # Если нет точного совпадения, ищем частичное
    for eng, russian_list in SPECIALTY_MAPPING.items():
        if any(russian.lower() in specialty_lower for russian in russian_list):
            return russian_list[0]
    
    return specialty