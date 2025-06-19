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
