import asyncio
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from utils.google_sheets import get_sheet_data
from bot.messages import format_block, format_all_blocks, format_new_offer_blocks, format_expired_offer_blocks

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

def parse_end_date(period_str):
    try:
        # Извлекаем конец периода
        _, end_str = period_str.split('-')
        end_str = end_str.strip()
        # Поддержка форматов с годом и без
        for fmt in ("%d.%m.%y", "%d.%m.%Y", "%d.%m"):
            try:
                parsed = datetime.strptime(end_str, fmt).date()
                # Если год не указан — добавим текущий
                if fmt == "%d.%m":
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed
            except:
                continue
        return None
    except:
        return None
# === Функция: Нормализация и сравнение даты начала ===
def is_starting_today(period_str, today):
    try:
        start_str = period_str.split('-')[0].strip()
        if len(start_str.split('.')) == 3:
            start_date = datetime.strptime(start_str, '%d.%m.%y')
        else:
            start_date = datetime.strptime(start_str, '%d.%m')
            start_date = start_date.replace(year=today.year)
        return start_date.date() == today
    except:
        return False
        
# === Фильтрация новых акций (по сегодняшней дате начала) ===
def filter_today_blocks(rows, skip_rows=1):
    today = datetime.now().date()
    blocks = []
    current_block = []

    def parse_start_date(row):
        try:
            period = row[1] if len(row) > 1 else ""
            start_str = period.split("-")[0].strip()
            today = datetime.now().date()
            for fmt in ("%d.%m", "%d.%m.%y", "%d.%m.%Y"):
                try:
                    parsed = datetime.strptime(start_str, fmt).date()
                    # Если год не указан, ставим текущий
                    if fmt == "%d.%m":
                        parsed = parsed.replace(year=today.year)
                    return parsed
                except:
                    continue
            return None
        except:
            return None

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                start_date = parse_start_date(main_row)
                if start_date == today:
                    blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        start_date = parse_start_date(main_row)
        if start_date == today:
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
def filter_expired_blocks(rows, reference_date: datetime.date, skip_rows=1):
    blocks = []
    current_block = []

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    end_date = parse_end_date(main_row[1])
                    if end_date and end_date == (reference_date - timedelta(days=1)):
                        blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            end_date = parse_end_date(main_row[1])
            if end_date and end_date == (reference_date - timedelta(days=1)):
                blocks.append(current_block)

    return [format_block(b) for b in blocks]


# === Отправка завершённых акций (вчера закончились) ===
# === Вывод завершённых акций (с учётом даты, если передана)
async def send_expired_offers(bot, chat_id, reference_date=None):
    if reference_date is None:
        reference_date = datetime.now().date()

    categories = [
        ("Акции Аромки", 2, "💧💨 Завершённые акции: Аромки"),
        ("Акции Снеки", 2, "🥡 Завершённые акции: Снеки"),
        ("Акции Напитки", 1, "🥤 Завершённые акции: Напитки")
    ]

    any_found = False

    for sheet_name, skip, header in categories:
        rows = get_sheet_data(sheet_name)
        filtered = filter_expired_blocks(rows, reference_date, skip_rows=skip)
        if filtered:
            any_found = True
            await send_combined_blocks(bot, chat_id, filtered, header)

    if not any_found:
        await bot.send_message(chat_id=chat_id, text="✅ На выбранную дату все акции ещё действуют.")



def filter_blocks_by_start_date(rows, target_date, skip_rows=1):
    blocks = []
    current_block = []

    def parse_date(date_str):
        """
        Преобразует строку даты в объект datetime.date
        """
        for fmt in ("%d.%m", "%d.%m.%y", "%d.%m.%Y"):
            try:
                dt = datetime.strptime(date_str, fmt)
                if fmt == "%d.%m":
                    dt = dt.replace(year=datetime.now().year)
                return dt.date()
            except:
                continue
        return None

    # Конвертируем введённую пользователем дату
    target_date_obj = parse_date(target_date)
    if not target_date_obj:
        return []

    def parse_start_date(period_str):
        try:
            start_str = period_str.split("-")[0].strip()
            return parse_date(start_str)
        except:
            return None

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    start_date = parse_start_date(main_row[1])
                    if start_date == target_date_obj:
                        blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    # обработка последнего блока
    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            start_date = parse_start_date(main_row[1])
            if start_date == target_date_obj:
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

async def send_expired_offers_by_date(bot, chat_id, target_date_str):
    try:
        # Преобразуем строку даты в объект с учётом форматов
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d.%m"):
            try:
                reference_date = datetime.strptime(target_date_str, fmt).date()
                if fmt == "%d.%m":
                    reference_date = reference_date.replace(year=datetime.now().year)
                break
            except:
                continue
        else:
            await bot.send_message(chat_id=chat_id, text="❌ Неверный формат даты. Введите в формате ДД.ММ")
            return

        categories = [
            ("Акции Аромки", 2, "💧💨 Завершённые акции: Аромки"),
            ("Акции Снеки", 2, "🥡 Завершённые акции: Снеки"),
            ("Акции Напитки", 1, "🥤 Завершённые акции: Напитки")
        ]

        any_found = False

        for sheet_name, skip, header in categories:
            rows = get_sheet_data(sheet_name)
            filtered = filter_expired_blocks(rows, reference_date, skip_rows=skip)
            if filtered:
                any_found = True
                await send_combined_blocks(bot, chat_id, filtered, header)

        if not any_found:
            await bot.send_message(chat_id=chat_id, text="✅ На выбранную дату завершённых акций нет.")

    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ Ошибка при обработке запроса: {e}")


def get_local_today():
    return datetime.utcnow().date() + timedelta(hours=3) 

def parse_date_range_simple(period: str):
    try:
        start_str, end_str = period.split("-")
        start = datetime.strptime(start_str.strip(), "%d.%m").date()
        end = datetime.strptime(end_str.strip(), "%d.%m").date()
        current_year = datetime.now().year
        return start.replace(year=current_year), end.replace(year=current_year)
    except:
        try:
            start = datetime.strptime(start_str.strip(), "%d.%m.%y").date()
            end = datetime.strptime(end_str.strip(), "%d.%m.%y").date()
            return start, end
        except:
            return None, None

async def send_formatted_new_offers(bot, chat_id, context):
    from datetime import datetime

    chosen_date_str = context.user_data.get("chosen_date")
    target_date = datetime.strptime(chosen_date_str, "%d.%m.%Y").date() if chosen_date_str else datetime.now().date()

    categories = ["Акции Напитки", "Акции Снеки", "Акции Аромки"]
    offers = []
    exceptions = []
    exception_addresses = []

    for category in categories:
        rows = get_sheet_data(category)
        for row in rows:
            try:
                if len(row) < 4:
                    continue

                period = row[1].strip()
                start, end = parse_date_range_simple(period)
                if start != target_date:
                    continue

                products = row[2].splitlines() if len(row) > 2 else []
                discount = row[3].strip()

                for product in products:
                    clean_product = ' '.join(product.strip().split())
                    if clean_product:
                        offer_line = f"🍀 {period.replace(' ', '').replace('-', '–')} {clean_product} {discount}"
                        offers.append(offer_line)

                # Обработка исключений — только в категории "Акции Напитки"
                if category == "Акции Напитки" and len(row) > 5 and row[5].strip().lower() not in ["", "немає", "нет"]:
                    for product in products:
                        clean_product = ' '.join(product.strip().split())
                        if clean_product:
                            exc_line = f"🍀 {period.replace(' ', '').replace('-', '–')} {clean_product} {discount}"
                            exceptions.append(exc_line)

                    # Добавляем адреса, если они есть (в колонке F)
                    exception_addresses += [addr.strip() for addr in row[5].splitlines() if addr.strip()]

            except Exception as e:
                print(f"Ошибка при обработке строки: {e}")
                continue

    if offers:
        await bot.send_message(chat_id, "🟢 НОВЫЕ АКЦИИ 🟢\n" + "\n".join(offers))

        if exceptions:
            await bot.send_message(chat_id, "‼️ Есть исключение для акции:\n" + "\n".join(exceptions))
            if exception_addresses:
                await bot.send_message(chat_id, "\n".join(exception_addresses))
        else:
            await bot.send_message(chat_id, "✅ Для текущих акций исключений нет.")
    else:
        await bot.send_message(chat_id, f"📭 Новых акций на {target_date.strftime('%d.%m.%Y')} нет для отправки.")




async def send_formatted_expired_offers(bot, chat_id, context=None):
    # Определяем целевую дату
    if context and context.user_data.get("chosen_date"):
        try:
            # Берем введенную дату и вычитаем 1 день
            target_date = datetime.strptime(context.user_data["chosen_date"], "%d.%m.%Y").date() - timedelta(days=1)
            custom_date_mode = True
        except ValueError:
            target_date = datetime.now().date() - timedelta(days=1)
            custom_date_mode = False
    else:
        target_date = datetime.now().date() - timedelta(days=1)
        custom_date_mode = False
    
    categories = ["Акции Напитки", "Акции Снеки", "Акции Аромки"]
    expired_offers = []
    
    for category in categories:
        rows = get_sheet_data(category)
        for row in rows:
            try:
                if len(row) < 4:
                    continue
                    
                period = row[1].strip() if len(row) > 1 else ""
                if not period:
                    continue
                    
                start_date, end_date = parse_date_range_simple(period)
                
                # Ищем акции, которые закончились в target_date (введенная дата -1 день)
                if end_date == target_date:
                    products = row[2].splitlines() if len(row) > 2 else []
                    discount = row[3].strip() if len(row) > 3 else ""
                    
                    for product in products:
                        clean_product = ' '.join(product.strip().split())
                        if clean_product:
                            formatted_period = period.replace(' ', '').replace('-', '–')
                            offer_line = f"🍀 {formatted_period} {clean_product} {discount}".strip()
                            expired_offers.append(offer_line)
            
            except Exception as e:
                print(f"Ошибка при обработке строки: {e}")
                continue

    if expired_offers:
        original_date = (target_date + timedelta(days=1)).strftime('%d.%m.%Y') if custom_date_mode else ""
        message = f"🔴ЗАКОНЧИЛАСЬ АКЦИЯ🔴\n" + "\n".join(expired_offers)
        await bot.send_message(chat_id, message)
    else:
        original_date = (target_date + timedelta(days=1)).strftime('%d.%m.%Y') if custom_date_mode else ""
        if custom_date_mode:
            await bot.send_message(chat_id, f"📭 Перед {original_date} не было завершённых акций")
        else:
            await bot.send_message(chat_id, "📭 Вчера не было завершённых акций")
