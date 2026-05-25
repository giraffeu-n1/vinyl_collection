# Размещение «Коллекция винила» на Timeweb

Рекомендуемый способ — **Timeweb Cloud → App Platform** (Python/Django).  
Подходит и **VPS** с nginx + gunicorn (кратко в конце).

## Что нужно заранее

1. Аккаунт [Timeweb Cloud](https://timeweb.cloud/)
2. Репозиторий с проектом (GitHub / GitLab / Bitbucket) — папка `vinyl_collection` в корне репо **или** весь репозиторий = проект
3. Домен (можно привязить после деплоя)

## 1. Подготовка репозитория

Корень приложения для Timeweb — каталог, где лежит `manage.py`.

**SSH/SFTP к контейнеру недоступен** — Timeweb деплоит только из Git. База и фото кладутся в папку `deploy-data/` в репозитории (см. раздел 5).

## 2. Создание приложения в App Platform

1. Панель Timeweb Cloud → **App Platform** → **Создать приложение**
2. Тип: **Backend**, фреймворк **Django**
3. Подключите репозиторий, ветку `main` / `master`
4. **Корневая директория** — путь к `vinyl_collection`, если репозиторий шире (например `vinyl_collection`)
5. Python: **3.12** или **3.11**

### Команда сборки

Порядок важен: сначала зависимости и статика, затем база и администратор.  
`migrate` и `create_vinyl_admin` — **только здесь**, не в команде запуска (иначе блокировки SQLite).

**Рекомендуется** (короткая строка — панель Timeweb не обрежет команду):

```bash
sh scripts/build_production.sh
```

Скрипт: `scripts/build_production.sh` (pip, `BUILD_COMMIT.txt`, копирование `deploy-data/`, `collectstatic`, `migrate`, `create_vinyl_admin`).

Если нужна одна строка без скрипта (без `media/.` в конце — иначе панель может обрезать `cp -r`):

```bash
pip3 install --upgrade -r requirements-prod.txt && git rev-parse --short HEAD > BUILD_COMMIT.txt 2>/dev/null || true && mkdir -p media && ([ -f deploy-data/db.sqlite3 ] && cp deploy-data/db.sqlite3 db.sqlite3 || true) && ([ -d deploy-data/media ] && cp -r deploy-data/media . || true) && python3 manage.py collectstatic --noinput && python3 manage.py migrate --noinput && python3 manage.py create_vinyl_admin
```

> Опечатка **`collectstat`** ломает сборку — нужно **`collectstatic`** (с буквой **ic** в конце).

`create_vinyl_admin` — встроенная команда проекта (только Django, без OCR и лишних пакетов).

### Команда запуска

**Без** `migrate`. Копирует базу в `/tmp` и запускает **1 worker** (SQLite не любит несколько процессов):

```bash
sh scripts/start_production.sh
```

Или одной строкой:

```bash
sh scripts/start_production.sh
```

Скрипт копирует `deploy-data/`, выполняет **`migrate` на `/tmp/vinyl_collection.sqlite3`** (нужно для регистрации) и запускает gunicorn с **1 worker**.

## 3. Переменные окружения

В настройках приложения → **Переменные**:

| Ключ | Пример значения |
|------|-----------------|
| `DJANGO_SECRET_KEY` | длинная случайная строка (сгенерируйте новую!) |
| `DJANGO_DEBUG` | **`False`** (если не задан `DJANGO_SECRET_KEY`, иначе по умолчанию уже `False`) |
| `DJANGO_SECRET_KEY` | обязательно на Timeweb |
| `DJANGO_BEHIND_PROXY` | `True` (по умолчанию; не отключайте на Timeweb) |
| `DATABASE_PATH` | `/tmp/vinyl_collection.sqlite3` (опционально, скрипт запуска задаёт сам) |
| `DJANGO_ALLOWED_HOSTS` | `giraffeu-n1-vinyl-collection-1635.twc1.net` или `*` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://giraffeu-n1-vinyl-collection-1635.twc1.net` (можно не задавать — код добавит Origin того же хоста автоматически) |

Для домена Timeweb `*.twc1.net` достаточно указать хост в `DJANGO_ALLOWED_HOSTS` **или** оставить `*` — после деплоя с обновлённым кодом CSRF для POST с того же URL больше не падает.

Свой домен: дублируйте в `DJANGO_CSRF_TRUSTED_ORIGINS` с префиксом `https://`.

## 4. Администратор после деплоя

При сборке выполняется `create_vinyl_admin`:

| | |
|---|---|
| **Логин** | `vinyladmin` |
| **Пароль** | `VinylCol2026!` |

**Сразу после первого входа смените пароль** (админка Django `/admin/` → пользователи) или задайте свой пароль локально и пересоберите.

## 5. Перенос базы и фото (через Git)

1. На ПК в каталоге проекта:

```powershell
cd c:\metrica\vinyl_collection
.\scripts\prepare_deploy_data.ps1
```

2. Отправьте на GitHub:

```powershell
git add deploy-data
git commit -m "Add database and media for deploy"
git push origin main
```

3. В Timeweb App Platform → **Пересобрать** приложение.

При сборке файлы из `deploy-data/` копируются в `db.sqlite3` и `media/`.

> Репозиторий лучше сделать **приватным**. Обновили коллекцию локально — снова `prepare_deploy_data.ps1`, commit, push, пересборка.

## 6. Проверка

1. Откройте домен — должна открыться страница **Вход**
2. Войдите как `vinyladmin`
3. Проверьте каталог, фото, раздел **Пользователи**
4. Статика (CSS) — через WhiteNoise, отдельный nginx не обязателен

### Server Error (500)

1. В переменных временно: `DJANGO_DEBUG` = `True` → пересборка → откройте сайт и прочитайте текст ошибки.
2. **Логи приложения** (не только сборки) в App Platform.
3. `https://ваш-домен/health/` — смотрите `git_commit` (должен совпадать с последним push в GitHub), `db_exists`, `deploy_data_db` (должны быть `true`).

### Какая сборка на сервере

1. **Панель Timeweb** → ваше приложение → **История деплоев / Сборки** — там коммит и время последней успешной сборки.
2. **В браузере:** `https://giraffeu-n1-vinyl-collection-1635.twc1.net/health/` — поле **`git_commit`** (например `5996bc7`). Сравните с GitHub → репозиторий → Commits.
3. **Локально:** `git rev-parse --short HEAD` — должно совпасть с `git_commit` на сервере после пересборки.

Если `git_commit` = `null` — старая сборка без записи коммита; обновите команду сборки (с `BUILD_COMMIT.txt`) и пересоберите.
4. В **команде запуска** — `workers 1`, не 2 (SQLite + 2 workers = 500).
5. В запуске должно копироваться `deploy-data/` → см. `scripts/start_production.sh`.
6. В Git есть `deploy-data/db.sqlite3` и `deploy-data/media/`.
7. Не дублируйте `migrate` в команде запуска.

### Ошибка DisallowedHost

Добавьте домен в `DJANGO_ALLOWED_HOSTS` и пересоберите приложение.

### Нет фотографий

Проверьте, что папка `media/` загружена на сервер и пользователь **вошёл** в аккаунт (медиа недоступны гостям).

## 7. Виртуальный хостинг Timeweb (альтернатива)

На классическом Python-хостинге (Passenger, Python 3.10):

1. В панели включите **Python 3.10** для сайта
2. Загрузите файлы по FTP в каталог сайта
3. Создайте виртуальное окружение и установите `requirements-prod.txt`
4. Настройте `passenger_wsgi.py` / `wsgi.py` по инструкции Timeweb для Django
5. `ALLOWED_HOSTS` и переменные — как в таблице выше

Подробнее: [хостинг Python](https://timeweb.com/ru/services/hosting/python/), [деплой Django в App Platform](https://timeweb.cloud/docs/apps/deploying-backend-applications/django).

## 8. VPS (Timeweb Cloud)

```bash
sudo apt update && sudo apt install -y python3-venv nginx
cd /var/www/vinyl_collection
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_vinyl_admin
gunicorn vinylsite.wsgi:application --bind 127.0.0.1:8001 --workers 2
```

Настройте nginx как reverse proxy на `127.0.0.1:8001`, SSL через Let's Encrypt в панели Timeweb.

---

Документация Timeweb: [App Platform — Django](https://timeweb.cloud/docs/apps/deploying-backend-applications/django)
