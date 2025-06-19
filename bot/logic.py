import asyncio
from datetime import datetime, timedelta
from utils.google_sheets import get_sheet_data
from bot.messages import format_block, format_all_blocks


# === Универсальная отправка длинного текста ===
async def send_long(bot, chat_id, text, parse_mode="HTML"):
    """
    Делит длинный текст на части по 4096 символов и отправляет его по частям.
    """
    MAX_LENGTH = 4096
    for i in range(0, len(text), MAX_LENGTH):
        await bot.send_message(chat_id=chat_id, text=text[i:i+MAX_LENGTH], parse_mode=parse_mode)


# === Универсальная отправка блоков с заголовком ===
async def send_combined_blocks(bot, chat_id, blocks, header):
    """
    Объединяет блоки до лимита и отправляет с заголовком.
    """
    combined = header
    messages = []

    for block in blocks:
        if len(combined) + len(block) < 4096:
            combined += block
        else:
            messages.append(combined)
            combined = block
    messages.append(combined)

    await asyncio.sleep(1)  # защита от перегрузки Telegram API
    for i, msg in enumerate(messages):
        await send_long(bot, chat_id, msg if i == 0 else msg.replace(header, ""))


# === Акции: Снеки ===
async def send_sneki_full(bot, chat_id):
    """
    Получает и отправляет все акции из листа "Акции Снеки"
    """
    try:
        rows = get_sheet_data("Акции Снеки")
        blocks = format_all_blocks(rows, skip_rows=2)
        await send_combined_blocks(bot, chat_id, blocks, "🧾 Акция: Снеки\n")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ Ошибка при загрузке акций Снеки: {e}")


# === Акции: Напитки ===
async def send_drinks_full(bot, chat_id):
    """
    Получает и отправляет все акции из листа "Акции Напитки"
    """
    try:
        rows = get_sheet_data("Акции Напитки")
        blocks = format_all_blocks(rows, skip_rows=1)
        await send_combined_blocks(bot, chat_id, blocks, "🥤 Акция: Напитки\n")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ Ошибка при загрузке акций Напитки: {e}")


# === Фильтрация новых акций (по сегодняшней дате начала) ===
def filter_today_blocks(rows, skip_rows=1):
    today = datetime.now().strftime('%d.%m')
    blocks = []
    current_block = []

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    period = main_row[1].strip()
                    if '-' in period:
                        start_str = period.split('-')[0].strip()
                        if start_str == today:
                            blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            period = main_row[1].strip()
            if '-' in period:
                start_str = period.split('-')[0].strip()
                if start_str == today:
                    blocks.append(current_block)

    return [format_block(b) for b in blocks]


# === Отправка новых акций на сегодня по категориям ===
async def send_today_offers(bot, chat_id):
    """
    Отправляет новые акции, дата начала которых совпадает с сегодняшним днём.
    Каждая категория отправляется отдельным сообщением с заголовком.
    """
    categories = [
        ("Акции Аромки", 2, "💧💨 Новые акции: Аромки"),
        ("Акции Снеки", 2, "🥡 Новые акции: Снеки"),
        ("Акции Напитки", 1, "🥤 Новые акции: Напитки")
    ]

    any_found = False

    try:
        for sheet_name, skip_rows, header in categories:
            rows = get_sheet_data(sheet_name)
            filtered_blocks = filter_today_blocks(rows, skip_rows=skip_rows)

            if filtered_blocks:
                any_found = True
                await send_combined_blocks(bot, chat_id, filtered_blocks, header)

        if not any_found:
            await bot.send_message(chat_id=chat_id, text="📜 Новых акций нет на сегодня.")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ Ошибка при получении новых акций: {e}")



# === Фильтрация завершённых акций (вчерашняя дата окончания) ===
def filter_expired_blocks(rows, skip_rows=1):
    today = datetime.now().date()
    blocks = []
    current_block = []

    def parse_date_range(period_str):
        try:
            _, end_str = period_str.split('-')
            end_str = end_str.strip()
            parsed = datetime.strptime(end_str, '%d.%m').date()
            return parsed.replace(year=today.year)
        except:
            return None

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    end_date = parse_date_range(main_row[1])
                    if end_date and end_date == (today - timedelta(days=1)):
                        blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            end_date = parse_date_range(main_row[1])
            if end_date and end_date == (today - timedelta(days=1)):
                blocks.append(current_block)

    return [format_block(b) for b in blocks]


# === Отправка завершённых акций (вчера закончились) ===
async def send_expired_offers(bot, chat_id):
    """
    Отправляет акции, которые завершились вчера.
    """
    try:
        categories = [
            ("Акции Аромки", 2, "💧💨 Завершённые акции: Аромки"),
            ("Акции Снеки", 2, "📴 Завершённые акции: Снеки"),
            ("Акции Напитки", 1, "🥤 Завершённые акции: Напитки")
        ]

        any_found = False
        for sheet_name, skip, header in categories:
            rows = get_sheet_data(sheet_name)
            filtered = filter_expired_blocks(rows, skip_rows=skip)
            if filtered:
                any_found = True
                await send_combined_blocks(bot, chat_id, filtered, header)

        if not any_found:
            await bot.send_message(chat_id=chat_id, text="✅ На сегодня все акции ещё действуют.")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ Ошибка при получении завершённых акций: {e}")


def filter_blocks_by_start_date(rows, target_date, skip_rows=1):
    blocks = []
    current_block = []
    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    period = main_row[1].strip()
                    if '-' in period:
                        start_str = period.split('-')[0].strip()
                        if start_str == target_date:
                            blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)
    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            period = main_row[1].strip()
            if '-' in period:
                start_str = period.split('-')[0].strip()
                if start_str == target_date:
                    blocks.append(current_block)
    return [format_block(b) for b in blocks]

def filter_blocks_by_end_date(rows, target_date, skip_rows=1):
    blocks = []
    current_block = []

    try:
        target_date_obj = datetime.strptime(target_date, "%d.%m").date()
    except ValueError:
        return []

    def parse_end_date(period_str):
        try:
            _, end_str = period_str.split('-')
            end_date = datetime.strptime(end_str.strip(), "%d.%m").date()
            return end_date.replace(year=target_date_obj.year)
        except:
            return None

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    end_date = parse_end_date(main_row[1])
                    if end_date == (target_date_obj - timedelta(days=1)):
                        blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    # Обработка последнего блока
    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            end_date = parse_end_date(main_row[1])
            if end_date == (target_date_obj - timedelta(days=1)):
                blocks.append(current_block)

    return [format_block(b) for b in blocks]


async def send_new_offers_by_date(bot, chat_id, target_date):
    categories = [
        ("Акции Аромки", 2, "💧💨 Новые акции: Аромки"),
        ("Акции Снеки", 2, "🥡 Новые акции: Снеки"),
        ("Акции Напитки", 1, "🥤 Новые акции: Напитки")
    ]
    any_found = False
    for name, skip, header in categories:
        rows = get_sheet_data(name)
        filtered = filter_blocks_by_start_date(rows, target_date, skip_rows=skip)
        if filtered:
            any_found = True
            await send_combined_blocks(bot, chat_id, filtered, header)

    if not any_found:
        await bot.send_message(chat_id=chat_id, text="📭 Новых акций на эту дату нет.")

async def send_expired_offers_by_date(bot, chat_id, target_date):
    categories = [
        ("Акции Аромки", 2, "💧💨 Завершённые акции: Аромки"),
        ("Акции Снеки", 2, "🥡 Завершённые акции: Снеки"),
        ("Акции Напитки", 1, "🥤 Завершённые акции: Напитки")
    ]
    any_found = False
    for name, skip, header in categories:
        rows = get_sheet_data(name)
        filtered = filter_blocks_by_end_date(rows, target_date, skip_rows=skip)
        if filtered:
            any_found = True
            await send_combined_blocks(bot, chat_id, filtered, header)

    if not any_found:
        await bot.send_message(chat_id=chat_id, text="✅ На эту дату завершённых акций нет.")