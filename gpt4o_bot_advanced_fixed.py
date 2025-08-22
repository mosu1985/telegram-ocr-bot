print("=== GPT-4o ADVANCED FIXED BOT ===")

try:
    print("1. Importing libraries...")
    import sys
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception as _enc_e:
        pass
    import base64
    import openai
    import hashlib
    import time
    import uuid
    import random
    import string
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
    from datetime import datetime
    print("✅ All libraries imported")

    print("2. Setting up configuration...")
    import os
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    TARGET_GROUP_ID = os.environ.get("TARGET_GROUP_ID", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    if not BOT_TOKEN or not TARGET_GROUP_ID or not OPENAI_API_KEY:
        raise RuntimeError("Missing required env vars: BOT_TOKEN, TARGET_GROUP_ID, OPENAI_API_KEY")
    print("✅ Configuration set")

    print("3. Creating OpenAI client...")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client created")

    print("4. Creating Telegram bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    print("✅ Telegram bot created")

    print("5. Defining handlers...")
    
    # Состояния для ConversationHandler
    WAITING_FOR_PASSWORD = 1
    WAITING_FOR_PHONE = 2
    WAITING_FOR_EDIT = 3
    
    # Пароль для доступа
    ACCESS_PASSWORD = "Bomondstaff"
    
    # Счетчик обработанных изображений
    processed_count = 0
    
    # Словарь для хранения данных пользователей
    user_data = {}
    
    # Словарь для хранения авторизованных пользователей
    authorized_users = {}
    
    def generate_random_string(length=10):
        """Генерирует случайную строку для уникальности"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def save_authorization(user_id, phone_number):
        """Сохраняет авторизацию пользователя в файл"""
        try:
            import json
            auth_file = "authorized_users.json"
            
            # Загружаем существующие данные
            try:
                with open(auth_file, 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
            except FileNotFoundError:
                auth_data = {}
            
            # Добавляем нового пользователя
            auth_data[str(user_id)] = {
                'phone': phone_number,
                'authorized_at': datetime.now().isoformat()
            }
            
            # Сохраняем обратно в файл
            with open(auth_file, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Authorization saved for user_id: {user_id}")
            
        except Exception as e:
            print(f"Error saving authorization: {e}")
    
    def load_authorizations():
        """Загружает авторизации из файла"""
        try:
            import json
            auth_file = "authorized_users.json"
            
            with open(auth_file, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            # Загружаем в словарь авторизованных пользователей
            for user_id_str, user_data in auth_data.items():
                user_id = int(user_id_str)
                authorized_users[user_id] = True
                print(f"✅ Loaded authorization for user_id: {user_id}")
            
            print(f"✅ Loaded {len(auth_data)} authorizations")
            
        except FileNotFoundError:
            print("ℹ️ No authorization file found, starting fresh")
        except Exception as e:
            print(f"Error loading authorizations: {e}")

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Start command received")
        user_id = update.effective_user.id
        
        # Проверяем, авторизован ли пользователь
        if user_id in authorized_users:
            # Восстанавливаем номер телефона из файла
            try:
                import json
                auth_file = "authorized_users.json"
                with open(auth_file, 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
                
                if str(user_id) in auth_data:
                    phone_number = auth_data[str(user_id)]['phone']
                    context.user_data['user_phone'] = phone_number
                    print(f"✅ Restored phone number for user_id: {user_id}: {phone_number}")
            except Exception as e:
                print(f"Error restoring phone number: {e}")
            
            await update.message.reply_text("🤖 Привет! Вы уже авторизованы. Отправьте мне фото с рукописным текстом!")
        else:
            # Запрашиваем пароль
            keyboard = [["🔐 Ввести пароль"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                "🔐 **Доступ к боту ограничен**\n\n"
                "Для использования бота необходимо ввести пароль доступа.\n\n"
                "Нажмите кнопку ниже для ввода пароля:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return WAITING_FOR_PASSWORD

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        global processed_count
        try:
            user_id = update.effective_user.id
            
            # Проверяем авторизацию
            if user_id not in authorized_users:
                await update.message.reply_text(
                    "🔐 **Доступ запрещен!**\n\n"
                    "Для использования бота необходимо авторизоваться.\n"
                    "Отправьте /start для начала авторизации.",
                    parse_mode='Markdown'
                )
                return
            
            print("Photo received")
            
            # Увеличиваем счетчик
            processed_count += 1
            
            # Get photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Создаем уникальные идентификаторы
            unique_id = str(uuid.uuid4())[:8]
            random_string = generate_random_string(15)
            timestamp = int(time.time())
            session_id = f"session_{timestamp}_{random_string}"
            
            # Создаем хеш изображения
            image_hash = hashlib.md5(image_bytes).hexdigest()
            
            # Получаем информацию о пользователе
            user = update.effective_user
            user_name = user.first_name or "Неизвестно"
            user_username = user.username or "Нет"
            
            # Получаем номер телефона из контекста или используем значение по умолчанию
            user_phone = context.user_data.get('user_phone', "Не указан")
            
            print(f"🆔 Unique ID: {unique_id}")
            print(f"🎲 Random string: {random_string}")
            print(f"📊 Processed count: {processed_count}")
            print(f"🕐 Timestamp: {timestamp}")
            print(f"🖼️ Image hash: {image_hash[:8]}...")
            print(f"👤 User ID: {user_id}")
            print(f"👤 User Name: {user_name}")
            print(f"👤 User Username: @{user_username}")
            print(f"📱 User Phone: {user_phone}")
            print(f"🆔 Session ID: {session_id}")
            
            await update.message.reply_text(f"🔄 Обрабатываю изображение #{processed_count} с помощью GPT-4o Advanced Fixed...")
            
            # Encode to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            print("Sending to OpenAI...")
            
            # Точный промпт с акцентом на порядок и количества
            prompt = f"""Распознай рукописный текст с этого изображения. Это список продуктов для ресторана на русском языке.

УНИКАЛЬНЫЙ ЗАПРОС #{processed_count}
УНИКАЛЬНЫЙ ID: {unique_id}
СЛУЧАЙНАЯ СТРОКА: {random_string}
СЕССИЯ: {session_id}
ВРЕМЯ: {timestamp}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. СОБЛЮДАЙ ТОЧНЫЙ ПОРЯДОК СТРОК С ФОТО - первая строка на фото должна быть первой в ответе
2. ТОЧНО КОПИРУЙ КОЛИЧЕСТВА - если написано "6 кг", то и пиши "6 кг"
3. СОХРАНЯЙ ЕДИНИЦЫ ИЗМЕРЕНИЯ - кг, шт, пучки, ящики, головки
4. Читай строки СВЕРХУ ВНИЗ в том же порядке, как на фото

ПРОДУКТЫ ДЛЯ РАСПОЗНАВАНИЯ:
- лук фиолетов, лук зеленый, белый лук
- морковка, картошка (мелкая, крупная)
- чери, листья салата, микс, айсберг
- лимоны, петрушка, укроп, чеснок
- болгарский перец, капуста, баклажан
- апельсины, имбирь, кабачок, яблоки
- грейпфрут, киви, помидоры, огурцы

ЕДИНИЦЫ ИЗМЕРЕНИЯ:
- кг (килограммы)
- шт (штуки)
- пучки, пучка
- ящики, ящик
- головки, головка

ФОРМАТ ОТВЕТА:
- Каждый продукт с новой строки
- Формат: "Продукт - Количество"
- Пример: "Лук фиолетов - 6 кг"
- СОБЛЮДАЙ ТОЧНЫЙ ПОРЯДОК С ФОТО

ВАЖНО: 
- Первая строка на фото = первая строка в ответе
- Точные количества без изменений
- Сохраняй все единицы измерения
- Верни ТОЛЬКО распознанный текст, ничего лишнего"""

            # Используем GPT-4o-mini как основную модель
            try:
                print("Using GPT-4.1 model...")
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.1
                )
                used_model = "gpt-4.1"
                print(f"✅ Successfully used model: {used_model}")
                
            except Exception as e:
                print(f"❌ GPT-4.1 failed: {e}")
                # Fallback to GPT-4o if GPT-4o-mini fails
                print("Trying GPT-4o as fallback...")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.1
                )
                used_model = "gpt-4o (fallback)"
                print(f"✅ Using fallback model: {used_model}")
            
            recognized_text = response.choices[0].message.content.strip()
            print(f"📝 Recognized: '{recognized_text}'")
            
            # Проверяем, не пустой ли ответ
            if not recognized_text or recognized_text.lower() in ['', 'none', 'пусто', 'нет текста', 'текст не виден', 'изображение пустое']:
                error_message = "❌ Не удалось распознать текст. Возможные причины:\n• Изображение слишком темное/светлое\n• Текст нечеткий\n• Изображение пустое\n\nПопробуйте отправить фото снова с лучшим качеством."
                await update.message.reply_text(error_message)
                return
            
            # Сохраняем данные пользователя для последующего использования
            user_data[user_id] = {
                'recognized_text': recognized_text,
                'user_name': user_name,
                'user_username': user_username,
                'user_phone': user_phone,
                'user_id': user_id,
                'unique_id': unique_id,
                'processed_count': processed_count,
                'image_hash': image_hash,
                'random_string': random_string,
                'session_id': session_id,
                'used_model': used_model,
                'timestamp': timestamp
            }
            
            # Создаем кнопки для подтверждения
            keyboard = [
                ["✅ Да, все верно"],
                ["❌ Нет, нужно исправить"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            # Отправляем распознанный текст с кнопками
            await update.message.reply_text(
                f"📝 **Распознанный текст:**\n\n{recognized_text}\n\n"
                f"**Текст распознался корректно?**\n\n"
                f"Выберите действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error in handle_photo: {e}")
            await update.message.reply_text(f"❌ Произошла ошибка: {e}")

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений и кнопок меню"""
        try:
            text = update.message.text
            user_id = update.effective_user.id
            
            # Проверяем авторизацию
            if user_id not in authorized_users:
                await update.message.reply_text(
                    "🔐 **Доступ запрещен!**\n\n"
                    "Для использования бота необходимо авторизоваться.\n"
                    "Отправьте /start для начала авторизации.",
                    parse_mode='Markdown'
                )
                return
            
            print(f"Text received: '{text}' from user_id: {user_id}")
            
            # Проверяем, есть ли данные пользователя
            if user_id not in user_data:
                await update.message.reply_text("❌ Данные не найдены. Отправьте фото заново.")
                return
            
            data = user_data[user_id]
            
            # Обработка кнопок меню
            if text == "✅ Да, все верно":
                print("User confirmed, sending to group...")
                # Пользователь подтвердил - отправляем в группу
                await send_to_group(data, context)
                await update.message.reply_text("Заявка успешно отправлена адмнистратору", reply_markup=ReplyKeyboardRemove())
                # Удаляем данные пользователя
                del user_data[user_id]
                
            elif text == "❌ Нет, нужно исправить":
                print("User wants to edit...")
                # Пользователь хочет редактировать
                await update.message.reply_text(
                    f"📝 **Редактирование текста:**\n\n"
                    f"**Инструкция:**\n"
                    f"1. Скопируйте текст из сообщения ниже\n"
                    f"2. Вставьте его в новое сообщение\n"
                    f"3. Внесите необходимые изменения\n"
                    f"4. Отправьте исправленный текст\n\n"
                    f"После отправки исправленного текста вы сможете еще раз проверить результат.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                
                # Отправляем чистый текст заявки отдельным сообщением
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=data['recognized_text']
                )
                
                context.user_data['editing_user_id'] = user_id
                
            elif text == "📤 Отправить заявку":
                print("User confirmed final edit, sending to group...")
                # Пользователь подтвердил исправленный текст - отправляем в группу
                await send_to_group(data, context)
                await update.message.reply_text("Заявка успешно отправлена адмнистратору", reply_markup=ReplyKeyboardRemove())
                # Удаляем данные пользователя
                del user_data[user_id]
                
            elif text == "✏️ Еще раз исправить":
                print("User wants to edit again...")
                # Пользователь хочет еще раз редактировать
                await update.message.reply_text(
                    f"📝 **Повторное редактирование:**\n\n"
                    f"**Инструкция:**\n"
                    f"1. Скопируйте текст из сообщения ниже\n"
                    f"2. Вставьте его в новое сообщение\n"
                    f"3. Внесите необходимые изменения\n"
                    f"4. Отправьте исправленный текст\n\n"
                    f"После отправки исправленного текста вы сможете еще раз проверить результат.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                
                # Отправляем чистый текст заявки отдельным сообщением
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=data['recognized_text']
                )
                
                context.user_data['editing_user_id'] = user_id
                
            elif text == "❌ Отмена":
                print("User cancelled...")
                # Пользователь отменил
                await update.message.reply_text("❌ Редактирование отменено. Отправьте новое фото.", reply_markup=ReplyKeyboardRemove())
                del user_data[user_id]
                if 'editing_user_id' in context.user_data:
                    del context.user_data['editing_user_id']
                    
            else:
                # Это обычный текст - проверяем, не редактирование ли это
                editing_user_id = context.user_data.get('editing_user_id')
                if editing_user_id and editing_user_id == user_id:
                    # Это редактирование текста
                    await handle_text_edit(update, context)
                else:
                    # Неизвестная команда
                    await update.message.reply_text("❌ Неизвестная команда. Отправьте фото для начала работы.")
                    
        except Exception as e:
            print(f"Error in handle_text: {e}")
            await update.message.reply_text(f"❌ Ошибка обработки: {e}")
            # В случае ошибки очищаем данные
            if user_id in user_data:
                del user_data[user_id]
            if 'editing_user_id' in context.user_data:
                del context.user_data['editing_user_id']

    async def handle_text_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик редактирования текста"""
        try:
            user_id = context.user_data.get('editing_user_id')
            print(f"Text edit received for user_id: {user_id}")
            
            if not user_id or user_id not in user_data:
                await update.message.reply_text("❌ Ошибка. Отправьте фото заново.")
                return
            
            # Обновляем распознанный текст
            user_data[user_id]['recognized_text'] = update.message.text
            print(f"Updated text: {update.message.text}")
            
            # Создаем кнопки для подтверждения исправленного текста
            keyboard = [
                ["📤 Отправить заявку"],
                ["✏️ Еще раз исправить"],
                ["❌ Отмена"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            # Показываем исправленный текст и просим подтверждение
            await update.message.reply_text(
                f"📝 **Исправленный текст:**\n\n{update.message.text}\n\n"
                f"**Текст исправлен корректно?**\n\n"
                f"Выберите действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Очищаем данные редактирования
            if 'editing_user_id' in context.user_data:
                del context.user_data['editing_user_id']
            
        except Exception as e:
            print(f"Error in handle_text_edit: {e}")
            await update.message.reply_text(f"❌ Ошибка при редактировании: {e}")
            # В случае ошибки тоже очищаем данные
            if 'editing_user_id' in context.user_data:
                del context.user_data['editing_user_id']

    async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода пароля"""
        try:
            text = update.message.text
            user_id = update.effective_user.id
            
            print(f"Password attempt from user_id: {user_id}")
            
            if text == "🔐 Ввести пароль":
                # Пользователь нажал кнопку ввода пароля
                await update.message.reply_text(
                    "🔐 **Введите пароль доступа:**\n\n"
                    "Отправьте пароль текстовым сообщением:",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                return WAITING_FOR_PASSWORD
            elif text == ACCESS_PASSWORD:
                # Пароль верный
                print(f"✅ Correct password from user_id: {user_id}")
                authorized_users[user_id] = True
                
                # Временное отключение запроса телефона: сохраняем авторизацию сразу
                phone_number = context.user_data.get('user_phone', "Не указан")
                try:
                    save_authorization(user_id, phone_number)
                except Exception as e:
                    print(f"Warning: failed to persist authorization: {e}")
                await update.message.reply_text(
                    "✅ **Пароль принят!**\n\n"
                    "Вы авторизованы. Теперь вы можете отправлять фото с рукописным текстом.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            else:
                # Неверный пароль
                print(f"❌ Wrong password from user_id: {user_id}")
                await update.message.reply_text(
                    "❌ **Неверный пароль!**\n\n"
                    "Попробуйте еще раз или обратитесь к администратору.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END
                
        except Exception as e:
            print(f"Error in handle_password: {e}")
            await update.message.reply_text("❌ Ошибка при проверке пароля. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик номера телефона"""
        try:
            user_id = update.effective_user.id
            
            # Проверяем, есть ли контакт в сообщении
            if update.message.contact:
                # Пользователь поделился контактом
                phone_number = update.message.contact.phone_number
                print(f"✅ Phone number received from user_id: {user_id}: {phone_number}")
                
                # Сохраняем номер телефона
                context.user_data['user_phone'] = phone_number
                
                # Сохраняем авторизацию в файл
                save_authorization(user_id, phone_number)
                
                await update.message.reply_text(
                    f"✅ **Номер телефона принят!**\n\n"
                    f"📱 Ваш номер: `{phone_number}`\n\n"
                    f"Теперь вы можете отправлять фото с рукописным текстом!",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
                
            elif update.message.text == "📱 Поделиться номером телефона":
                # Пользователь нажал кнопку, но не поделился контактом
                await update.message.reply_text(
                    "📱 **Для продолжения необходимо поделиться номером телефона:**\n\n"
                    "1. Нажмите кнопку '📱 Поделиться номером телефона'\n"
                    "2. В появившемся окне выберите 'Поделиться'\n"
                    "3. Подтвердите отправку номера\n\n"
                    "Это необходимо для идентификации отправителя заявок.",
                    reply_markup=ReplyKeyboardMarkup([["📱 Поделиться номером телефона"]], one_time_keyboard=True, resize_keyboard=True),
                    parse_mode='Markdown'
                )
                return WAITING_FOR_PHONE
            else:
                # Пользователь отправил текст вместо контакта
                await update.message.reply_text(
                    "❌ **Неверный формат!**\n\n"
                    "Пожалуйста, используйте кнопку '📱 Поделиться номером телефона' "
                    "для отправки подтвержденного номера телефона.",
                    reply_markup=ReplyKeyboardMarkup([["📱 Поделиться номером телефона"]], one_time_keyboard=True, resize_keyboard=True)
                )
                return WAITING_FOR_PHONE
                
        except Exception as e:
            print(f"Error in handle_phone: {e}")
            await update.message.reply_text("❌ Ошибка при обработке номера телефона. Попробуйте еще раз.")
            return ConversationHandler.END

    async def send_to_group(data, context):
        """Отправка заявки в группу"""
        try:
            current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            # Сообщение 1: Заголовок и данные отправителя (без распознанного текста)
            header_text = f"""📋 НОВАЯ ЗАЯВКА НА ПРОДУКТЫ

⏰ Время заявки: {current_time}

👤 ОТПРАВИТЕЛЬ:
📱 Имя: {data['user_name']}
📞 Телефон: {data['user_phone']}

🤖 Обработано автоматически"""

            print("Sending header to group...")
            await context.bot.send_message(chat_id=TARGET_GROUP_ID, text=header_text)

            # Сообщение 2: Чистый текст заявки отдельно
            print("Sending pure text to group...")
            await context.bot.send_message(chat_id=TARGET_GROUP_ID, text=data['recognized_text'])
            print("✅ Messages sent to group successfully")
            
        except Exception as e:
            print(f"Error in send_to_group: {e}")
            # Если даже простой текст не отправляется, отправляем еще более простой
            try:
                basic_text = f"НОВАЯ ЗАЯВКА\nВремя: {current_time}\nОт: {data['user_name']}\n\n{data['recognized_text']}"
                await context.bot.send_message(chat_id=TARGET_GROUP_ID, text=basic_text)
                print("✅ Basic message sent to group")
            except Exception as e2:
                print(f"Error sending basic message: {e2}")

    print("6. Registering handlers...")
    
    # Загружаем сохраненные авторизации
    load_authorizations()
    
    # Создаем ConversationHandler для авторизации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
        },
        fallbacks=[],
        per_message=False
    )
    
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Handlers registered")

    print("7. Starting GPT-4o Advanced Fixed bot...")
    print("🤖 GPT-4o Advanced Fixed бот запущен и готов к работе!")
    app.run_polling()

except Exception as e:
    print(f"❌ FATAL ERROR: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
