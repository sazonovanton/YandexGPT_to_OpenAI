# Транслятор YandexGPT API в OpenAI API
FastAPI сервер, который преобразует запросы OpenAI API в запросы [YandexGPT](https://yandex.cloud/en/services/yandexgpt) и [YandexART](https://yandex.cloud/en/docs/foundation-models/quickstart/yandexart) API. Это позволяет использовать инструменты и приложения, разработанные для API OpenAI, с языковыми моделями и моделями генерации изображений от Яндекса.  

## Навигация

[English](README.md) | Russian   

- [Возможности](#возможности)
- [Предварительные требования](#предварительные-требования)
- [Установка](#установка)
- [Примеры использования](#примеры-использования)
- [Переменные окружения](#переменные-окружения)
- [Псевдонимы моделей](#псевдонимы-моделей)

## Возможности
- **Генерация текста**: Преобразует запросы чат-комплишенов OpenAI в YandexGPT
  - ✅ Поддержка потоковой передачи
  - ✅ Tools (не потоковая передача)
  - ⬜ Vision (не поддерживается)
- **Текстовые эмбеддинги**: Конвертирует запросы эмбеддингов в модели векторизации текста Яндекса
  - ✅ Поддерживает форматы кодирования `float` и `base64`
- **Генерация изображений**: Преобразует запросы в стиле DALL-E в YandexART
  - ✅ Поддерживает форматы ответа base64 и URL
  - ✅ Настраиваемые соотношения сторон
  - ❌ Несколько изображений за запрос (ограничено 1)

## Предварительные требования
1. Аккаунт в Яндекс Облаке
2. API ключ и ID каталога из [Яндекс Облака](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key)
3. Необходимые роли IAM:
   - `ai.languageModels.user` (для YandexGPT)
   - `ai.imageGeneration.user` (для YandexART)

## Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/sazonovanton/YandexGPT_to_OpenAI
cd YandexGPT_to_OpenAI
```

### 2. Выбор метода аутентификации
Сервер поддерживает два метода аутентификации:

#### А. Сгенерированные токены
Генерация токенов, которые пользователи могут использовать для доступа к API:
```bash
python utils/tokens.py
```
Токены будут сохранены в `data/tokens.json`

#### Б. Собственный ключ (BYOK)
Позволяет пользователям предоставлять свои собственные учетные данные Яндекс Облака в формате:
```
<CatalogID>:<SecretKey>
```

### 3. Варианты развертывания

#### Использование Docker (Рекомендуется)
1. Настройте переменные окружения в `docker-compose.yml`:
```yaml
environment:
  - Y2O_SecretKey=your_secret_key
  - Y2O_CatalogID=your_catalog_id
  - Y2O_BringYourOwnKey=false
  - Y2O_ServerURL=http://127.0.0.1:8520
  - Y2O_LogFile=logs/y2o.log
  - Y2O_LogLevel=INFO
```

2. Запустите сервер:
```bash
docker-compose up -d
```

#### Ручная установка
1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` с конфигурацией:
```bash
Y2O_SecretKey=your_secret_key
Y2O_CatalogID=your_catalog_id
Y2O_BringYourOwnKey=false
Y2O_Host=127.0.0.1
Y2O_Port=8520
Y2O_ServerURL=http://127.0.0.1:8520
Y2O_LogFile=logs/y2o.log
Y2O_LogLevel=INFO
```

3. Запустите сервер:
```bash
python app.py
```

### 4. Настройка SSL (Опционально)

Для включения SSL установите следующие переменные окружения:
```bash
Y2O_SSL_Key=ssl/private.key
Y2O_SSL_Cert=ssl/cert.pem
```

## Примеры использования

### Чат-комплишены
#### Python
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("TOKEN"),
    base_url="http://<your_host>:<your_port>/v1",
)
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="yandexgpt/latest",
)
```
#### cURL
```bash
curl http://<your_host>:<your_port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "yandexgpt/latest",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

### Генерация изображений

#### Python
```python
response = client.images.generate(
    model="yandex-art/latest",
    prompt="A painting of a cat",
    response_format="b64_json"  
)
```
#### cURL
```bash
curl http://<your_host>:<your_port>/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "yandex-art/latest",
    "prompt": "A painting of a cat",
    "response_format": "url"
  }'
```
```bash
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -O http://<your_host>:<your_port>/images/<id>.jpg
```

### Текстовые эмбеддинги

```python
response = client.embeddings.create(
    model="text-search-query/latest",
    input=["Your text here"],
    encoding_format="float" 
)
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|---------------|
| Y2O_SecretKey | API ключ Яндекс Облака | None |
| Y2O_CatalogID | ID каталога Яндекс Облака | None |
| Y2O_BringYourOwnKey | Разрешить пользователям предоставлять свои учетные данные | False |
| Y2O_Host | Хост сервера | 127.0.0.1 |
| Y2O_Port | Порт сервера | 8520 |
| Y2O_ServerURL | Публичный URL сервера для скачивания изображений | http://127.0.0.1:8520 |
| Y2O_LogFile | Путь к файлу логов | logs/y2o.log |
| Y2O_LogLevel | Уровень логирования | INFO |
| Y2O_SSL_Key | Путь к приватному ключу SSL | None |
| Y2O_SSL_Cert | Путь к сертификату SSL | None |
| Y2O_CORS_Origins | Разрешенные CORS источники | * |
| Y2O_TestToken | Тестовый токен для utils/test.py (для разработки) | None |

## Синонимы моделей OpenAI
Транслятор поддерживает автоматическое сопоставление имен моделей от OpenAI к моделям Yandex Foundation Models. Однако эти модели могут не иметь прямых эквивалентов, поэтому данный функционал поддерживается "на всякий случай". Лучше использовать имена моделей Яндекса напрямую (например, `yandexgpt/latest`).      
Поддерживаются следующие псевдонимы:

### Чат-модели
- `gpt-3.5*` → `yandexgpt-lite/latest`
- `*mini*` → `yandexgpt-lite/latest`
- `gpt-4*` → `yandexgpt/latest`
### Модели эмбеддингов
- `text-embedding-3-large` → `text-search-doc/latest`
- `text-embedding-3-small` → `text-search-query/latest`
- `text-embedding-ada-002` → `text-search-query/latest`
### Модели изображений
- `dall-e*` → `yandex-art/latest`
