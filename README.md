# Ecoute — інструмент для інтерактивних інтерв'ю з AI-помічником

Ecoute поєднує локальну/гібридну транскрипцію аудіо та стрімінгові підказки від великих мовних моделей для підтримки інтерв'ю, підготовки кандидатів і запису розмов. Репозиторій містить бекенд (Python/FastAPI) і фронтенд (React + TypeScript + опціонально Tauri), а також механізми збереження сесій і інструменти для аналізу історії.

## Ключові можливості

- Жива транскрипція голосу (підтримка Groq Whisper або сумісного сервісу).
- Push-to-Talk (Ctrl+Alt) та RMS VAD (гейт по середньому RMS) для ігнорування фону.
- Обчислення WPM (слова за хвилину) і реальний сигнал "Speak Slower" при надмірній швидкості мовлення.
- Стрімінгові LLM-підказки із захистом від дублювання (clear-сигнал перед стрімом).
- Локальне збереження сесій у JSON з повним timeline подій і аналітикою.
- Веб-інтерфейс з вкладками: налаштування аудіо/контексту, вибір персоналії, History (перегляд і експорт сесій).
- Парсинг описів вакансій по URL для автоматичного додавання контексту.

## Архітектура (коротко)

- Backend: FastAPI (`backend/server.py`) — WebSocket `/ws`, REST API (`/api/sessions`, `/api/parse_job`), логіка сесій і збереження.
- Транскрипція: `backend/AudioTranscriber.py` — захоплення аудіо, PTT, RMS VAD, виклики до Groq Whisper.
- LLM: `backend/LLMClient.py` — формує системні промпти для двох персоналій (`Interview Copilot`, `Client English Assistant`), sliding-window історії, стрім токенів з clear-сигналом.
- Frontend: React + TypeScript + Vite + Tailwind. Ключові компоненти: `SetupView.tsx`, `InterviewView.tsx`, `useWebSocket.ts`.

## Швидкий старт (локально)

### 1) Backend

  - Створіть віртуальне середовище та встановіть залежності:

  ```powershell
  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

  - Запустіть сервер у режимі розробки:

  ```powershell
  uvicorn server:app --reload
  ```

### 2) Frontend

  - Встановіть Node.js (LTS), залежності та запустіть dev-сервер:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

  - Для збірки production-статичних файлів:

  ```bash
  npm run build
  ```

  - Для запуску десктоп-версії (Tauri):

  ```bash
  npm run tauri dev
  ```

### 3) Зовнішні сервіси та ключі

- Якщо використовуєте віддалений LLM або платні API — налаштуйте відповідні змінні оточення або файли конфігурації згідно коментарів у `backend`.

## API та WebSocket

- WebSocket: `ws://<host>:<port>/ws` — двосторонній стрім подій.
  - Основні типи повідомлень від сервера:
    - `transcript`: `{type: "transcript", speaker, text, timestamp, duration_seconds, word_count, wpm, is_speaking_too_fast}`
    - `llm_hint`: `{type: "llm_hint", text, clear?: true, is_streaming?: true}`
    - `event`/`control`: системні події початку/зупинки інтерв'ю.

- REST:
  - `GET /api/sessions` — повертає список збережених сесій.
  - `GET /api/sessions/{filename}` — повертає повний JSON сесії (history_log, summary).
  - `POST /api/parse_job` — тіло `{ "url": "https://..." }` → повертає очищений текст опису вакансії.

## Формат збереженої сесії

Файли зберігаються у `backend/data/sessions/` та містять:

- `session_id`, `session_started_at`, `session_ended_at`;
- `history_log`: масив подій із полями `{type, timestamp, payload}` (transcript, llm_hint, control-events);
- `summary`: агреговані метрики (`duration_seconds`, `talk_ratio`, `total_words`, тощо).

## UI / користувацька поведінка

- SetupView: вибір аудіо-пристрою, вставка/редагування контексту, персоналії (дві доступні), History вкладка з переліком сесій і експортом.
- InterviewView: жива транскрипція, підказки LLM у вигляді окремої картки; при `is_speaking_too_fast=true` показується жовта підказка "Speak Slower!".
- Експорт: на сторінці History доступна кнопка "Export to Markdown" яка завантажує структуру сесії у читабельному форматі.

## Розробницькі нотатки

- Щоб зменшити небажані транскрипти — комбінуйте Push-to-Talk і RMS VAD (реалізація в `backend/AudioTranscriber.py`).
- Щоб уникнути дублювання підказок у фронтенді — сервер перед стрімом відправляє `{type: "llm_hint", text: "", clear: true}`; клієнт має очистити поточний hint перед додаванням нових токенів.
- Sliding-window у `LLMClient` обмежує кількість повідомлень у prompt (наприклад, останні 10 повідомлень), що запобігає переповненню контексту.

## Нотатки по налагодженню

- Якщо підказки LLM дублюються — перевірте обробку `clear` у `App.tsx` / `InterviewView.tsx`.
- Якщо транскрипції надто чутливі — збільште поріг RMS або використайте PTT.
- Якщо Tauri не бачить мікрофон — перевірте дозволи ОС та правильний deviceId у UI.

## Файли для швидкого доступу

- [backend/server.py](backend/server.py)
- [backend/AudioTranscriber.py](backend/AudioTranscriber.py)
- [backend/LLMClient.py](backend/LLMClient.py)
- [frontend/src/components/SetupView.tsx](frontend/src/components/SetupView.tsx)
- [frontend/src/components/InterviewView.tsx](frontend/src/components/InterviewView.tsx)

---

Якщо потрібно, я можу додати приклади `curl`/JS для WebSocket та REST, створити шаблон `.env.example` з переліком змінних, або підготувати PR з цим README. Скажи, що робити далі.
