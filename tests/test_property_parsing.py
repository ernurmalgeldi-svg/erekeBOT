import pytest
from hypothesis import given, settings, strategies as st

# ============================================================================
# ЗАДАЧА 25: Property-based тестирование через Hypothesis
# ============================================================================


# --- Парсер команды /gcal_add ---
def stable_gcal_parser(text: str):
    """Логика парсинга хендлера cmd_gcal_add."""
    args = text.replace("/gcal_add", "").strip().split("|")
    if len(args) < 3:
        return None
    return {
        "title": args[0].strip(),
        "date": args[1].strip(),
        "time": args[2].strip(),
    }


# --- Нормализация текста (из process_text_logic) ---
def normalize_text(text: str) -> str:
    """Нормализует текст: убирает лишние пробелы, приводит к нижнему регистру."""
    if not isinstance(text, str):
        raise TypeError("Ожидается строка")
    return " ".join(text.strip().split()).lower()


# --- Валидация длины сообщения (Telegram max = 4096) ---
def validate_message_length(text: str) -> bool:
    """Проверяет, что сообщение не превышает лимит Telegram."""
    return isinstance(text, str) and len(text) <= 4096


# --- Парсер команды /calc ---
def parse_calc_expression(text: str) -> str:
    """Извлекает выражение из команды /calc."""
    expr = text.replace("/calc", "").strip()
    if not expr:
        return ""
    # Безопасная проверка — только цифры и операторы
    allowed = set("0123456789+-*/()., ")
    return expr if all(c in allowed for c in expr) else ""


# ============================================================================
# PROPERTY-BASED ТЕСТЫ
# ============================================================================

@given(st.text(max_size=4096))
@settings(max_examples=500)
def test_gcal_parsing_never_crashes(incoming_text: str):
    """
    Задача 25 - Баг #1: Парсер gcal не должен падать ни на какой строке.
    Для любой строки до 4096 символов функция не должна выбрасывать исключение.
    """
    try:
        result = stable_gcal_parser(incoming_text)
        if result is not None:
            assert isinstance(result, dict)
            assert "title" in result
            assert "date" in result
            assert "time" in result
    except Exception as e:
        pytest.fail(f"Парсер упал на строке {repr(incoming_text)}: {e}")


@given(st.text(max_size=4096))
@settings(max_examples=300)
def test_normalize_text_always_returns_string(text: str):
    """
    Задача 25 - Баг #2: normalize_text всегда возвращает строку.
    Никакой ввод не должен ломать нормализацию.
    """
    result = normalize_text(text)
    assert isinstance(result, str), f"Ожидалась строка, получили: {type(result)}"
    # Нет двойных пробелов
    assert "  " not in result, "В результате есть двойные пробелы!"
    # Нет ведущих/завершающих пробелов
    assert result == result.strip(), "В результате есть ведущие/завершающие пробелы!"


@given(st.text(max_size=4096))
@settings(max_examples=300)
def test_validate_message_length_no_false_negatives(text: str):
    """
    Задача 25 - Баг #3: validate_message_length не должна возвращать False
    для строк длиной <= 4096.
    """
    result = validate_message_length(text)
    if len(text) <= 4096:
        assert result is True, f"Строка длиной {len(text)} неверно отклонена!"
    else:
        assert result is False


@given(st.text(alphabet="0123456789+-*/()., ", max_size=100))
@settings(max_examples=200)
def test_calc_parser_with_valid_chars(expr: str):
    """
    Задача 25: parse_calc_expression не падает на безопасных символах.
    """
    try:
        full_cmd = f"/calc {expr}"
        result = parse_calc_expression(full_cmd)
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(f"parse_calc упал: {e}")


@given(st.text(max_size=4096))
@settings(max_examples=200)
def test_calc_parser_never_crashes(text: str):
    """
    Задача 25: parse_calc_expression не падает ни на каком вводе.
    """
    try:
        result = parse_calc_expression(text)
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(f"parse_calc упал на {repr(text)}: {e}")


@given(
    st.text(max_size=200),
    st.text(max_size=20),
    st.text(max_size=20),
)
@settings(max_examples=200)
def test_gcal_parser_with_pipe_format(title, date, time_str):
    """
    Задача 25: Если передать корректный формат title|date|time,
    парсер всегда возвращает dict с нужными полями.
    """
    text = f"/gcal_add {title}|{date}|{time_str}"
    try:
        result = stable_gcal_parser(text)
        # Если pipes есть — должен вернуть dict
        if result is not None:
            assert isinstance(result, dict)
            assert set(result.keys()) == {"title", "date", "time"}
    except Exception as e:
        pytest.fail(f"Парсер упал: {e}")


@given(st.integers(min_value=0, max_value=10000))
@settings(max_examples=100)
def test_validate_message_length_with_integers(length: int):
    """
    Задача 25: validate_message_length корректно работает со строками любой длины.
    """
    text = "a" * length
    result = validate_message_length(text)
    expected = length <= 4096
    assert result == expected, (
        f"Для длины {length} ожидали {expected}, получили {result}"
    )


# ============================================================================
# ДОПОЛНИТЕЛЬНО: Обычные unit-тесты для property функций
# ============================================================================

def test_gcal_parser_valid_input():
    result = stable_gcal_parser("/gcal_add Кездесу|2026-06-01|14:00")
    assert result is not None
    assert result["title"] == "Кездесу"
    assert result["date"] == "2026-06-01"
    assert result["time"] == "14:00"


def test_gcal_parser_missing_fields():
    result = stable_gcal_parser("/gcal_add Тек тақырып")
    assert result is None


def test_gcal_parser_empty_string():
    result = stable_gcal_parser("")
    assert result is None


def test_normalize_text_removes_extra_spaces():
    assert normalize_text("  привет   мир  ") == "привет мир"


def test_normalize_text_lowercase():
    assert normalize_text("Hello World") == "hello world"


def test_validate_message_max_length():
    assert validate_message_length("a" * 4096) is True
    assert validate_message_length("a" * 4097) is False

