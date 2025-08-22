# Telegram OCR Bot (GPT‑4.1)

Запуск локально:
- Установить Python 3.10+
- `pip install -r requirements.txt`
- Создать переменные окружения: `BOT_TOKEN`, `OPENAI_API_KEY`, `TARGET_GROUP_ID`
- `python gpt4o_bot_advanced_fixed.py`

Деплой на Railway:
1. Подключите репозиторий к Railway
2. В разделе Variables добавьте: `BOT_TOKEN`, `OPENAI_API_KEY`, `TARGET_GROUP_ID`
3. Build: авто (Python)
4. Start command: `python gpt4o_bot_advanced_fixed.py`
5. Нажмите Deploy

# 🤖 Telegram Bot для распознавания рукописного текста

Бот для распознавания рукописных заявок на продукты с помощью Google Document AI.

## 📋 Что нужно сделать:

### 1. Получить credentials.json
Следуйте инструкции в файле `GET_CREDENTIALS.md`

### 2. Запустить бот
```bash
.\start_bot.bat
```

## 📁 Файлы проекта:

- `bot_document_ai_simple.py` - основной файл бота
- `start_bot.bat` - запуск бота
- `config.py` - настройки
- `requirements.txt` - зависимости
- `GET_CREDENTIALS.md` - инструкция по настройке Google Cloud
- `test_setup.py` - тест настроек
- `check_python.bat` - проверка Python

## 🚀 Быстрый старт:

1. Скачайте `credentials.json` из Google Cloud Console
2. Поместите в папку проекта
3. Запустите: `.\start_bot.bat`
4. Отправьте фото с рукописным текстом боту

## 🔧 Тестирование:

```bash
py test_setup.py
``` 
