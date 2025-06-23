from datetime import datetime, timedelta

# === Форматирование одного блока акции ===
def format_block(block):
    def get(col_index, row):
        try:
            return row[col_index].strip() if len(row) > col_index and row[col_index].strip() else "не указано"
        except Exception:
            return "не указано"

    main_row = block[0] if block else []
    text = "————————————————————\n"
    text += f"📅 Дата внесения акции: {get(0, main_row)}\n"
    text += f"📅 Период проведения: {get(1, main_row)}\n"
    text += "————————————————————\n"
    text += f"🛍 ТОВАРЫ: {get(2, main_row)}\n"

    # Добавляем дополнительные строки с товарами (если есть)
    for row in block[1:]:
        try:
            if len(row) > 2 and row[2].strip():
                text += row[2].strip() + "\n"
        except Exception:
            continue

    text += "————————————————————\n"
    text += f"⚙️ МЕХАНИКА/% скидки: {get(3, main_row)}\n"
    text += "————————————————————\n"
    text += f"👥 УЧАСТНИКИ: {get(4, main_row)}\n"
    if len(main_row) > 5 and main_row[5].strip():
        text += "————————————————————\n"
        text += f"🙅‍♂️ ИСКЛЮЧЕНИЯ: {main_row[5].strip()}\n"
    text += "————————————————————\n"
    text += "Есть\n"
    return text


# === Разделение всех строк на отдельные акции-блоки ===
def format_all_blocks(rows, skip_rows=1):
    blocks = []
    current_block = []

    # Пропускаем служебные строки (заголовки)
    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):  # Пустая строка = разделитель блока
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    # Добавляем последний блок, если не завершился пустой строкой
    if current_block:
        blocks.append(current_block)

    # Преобразуем каждый блок в текст
    messages = [format_block(b) for b in blocks]
    return messages


# === Форматирование спец. акции "Аромки" ===
def format_aromki_message(rows):
    text = "🧾 Акция: Аромки\n"
    text += "————————————————————\n"
    main_row = rows[2] if len(rows) > 2 else []
    extra_row = rows[3] if len(rows) > 3 else []

    def get(col_index, row=main_row):
        try:
            return row[col_index].strip() if len(row) > col_index and row[col_index].strip() else "не указано"
        except Exception:
            return "не указано"

    text += f"📅 Дата внесения акции: {get(0)}\n"
    text += f"📅 Период проведения: {get(1)}\n"
    text += "————————————————————\n"
    text += f"🛍 ТОВАРЫ: {get(2)}\n"

    try:
        if len(extra_row) > 2 and extra_row[2].strip():
            text += extra_row[2].strip() + "\n"
    except Exception:
        pass

    text += "————————————————————\n"
    text += f"⚙️ МЕХАНИКА/% скидки: {get(3)}\n"
    text += "————————————————————\n"
    text += f"👥 УЧАСТНИКИ: {get(4)}\n"
    text += "————————————————————\n"
    text += "Есть"
    return text


def format_expired_offer_blocks(rows):
    today = datetime.now().date()
    result_lines = []

    for row in rows:
        try:
            period = row[1].strip()
            if "-" not in period:
                continue
            start_str, end_str = period.split("-")
            end_str = end_str.strip()

            # Автоматическое определение года
            if "." in end_str and len(end_str.split(".")[-1]) == 2:
                end_date = datetime.strptime(end_str, "%d.%m").date().replace(year=today.year)
            elif "." in end_str and len(end_str.split(".")[-1]) == 4:
                end_date = datetime.strptime(end_str, "%d.%m.%Y").date()
            else:
                continue

            if end_date == today - timedelta(days=1):
                text = f"🍀{period} {row[2].strip()} {row[3].strip()}"
                result_lines.append(text)
        except:
            continue

    if result_lines:
        return "🔴 ЗАКОНЧИЛАСЬ АКЦИЯ🔴\n" + "\n".join(result_lines)
    else:
        return "✅ Завершённых акций нет для отправки."

def format_new_offer_blocks(rows):
    from collections import defaultdict
    today = datetime.now().date()
    grouped = defaultdict(list)

    for row in rows:
        try:
            start_date_str = row[0].strip()

            if len(start_date_str.split(".")[-1]) == 2:
                start_date = datetime.strptime(start_date_str, "%d.%m").date().replace(year=today.year)
            elif len(start_date_str.split(".")[-1]) == 4:
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
            else:
                start_date = datetime.strptime(start_date_str, "%d.%m").date().replace(year=today.year)

            if start_date == today:
                period = row[1].strip()
                products_raw = row[2]
                discount = row[3].strip()

                # Очищаем от табов и неразрывных пробелов
                products = [line.strip().replace('\t', '').replace('\xa0', ' ') for line in products_raw.splitlines() if line.strip()]
                products_cleaned = "\n".join([f"***{p} {discount}".strip() for p in products])

                # ✅ Продукты идут с новой строки после даты
                grouped[period].append(products_cleaned)

        except Exception:
            continue

    if grouped:
        result_lines = ["🟢 НОВЫЕ АКЦИИ 🟢"]
        for period, items in grouped.items():
            for item in items:
                result_lines.append(f"🍀{period}\n{item}")
        return "\n".join(result_lines)
    else:
        return "📭 Новых акций нет для отправки."











