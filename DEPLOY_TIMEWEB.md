# Размещение «Коллекция винила» на Timeweb

Рекомендуемый способ — **Timeweb Cloud → App Platform** (Python/Django).  
Подходит и **VPS** с nginx + gunicorn (кратко в конце).

## Что нужно заранее

1. Аккаунт [Timeweb Cloud](https://timeweb.cloud/)
2. Репозиторий с проектом (GitHub / GitLab / Bitbucket) — папка `vinyl_collection` в корне репо **или** весь репозиторий = проект
3. Домен (можно привязить после деплоя)

## 1. Подготовка репозитория

Корень приложения для Timeweb — каталог, где лежит `manage.py`.

Загрузите на сервер (через git) также:

- `db.sqlite3` — база с альбомами (если переносите с локального ПК)
- папку `media/` — все фотографии

> **Важно:** на App Platform диск может сбрасываться при пересборке. После первого деплоя загрузите `db.sqlite3` и `media/` через SFTP/консоль или настройте постоянный том. Делайте резервные копии.

## 2. Создание приложения в App Platform

1. Панель Timeweb Cloud → **App Platform** → **Создать приложение**
2. Тип: **Backend**, фреймворк **Django**
3. Подключите репозиторий, ветку `main` / `master`
4. **Корневая директория** — путь к `vinyl_collection`, если репозиторий шире (например `vinyl_collection`)
5. Python: **3.12** или **3.11**

### Команда сборки

```bash
pip3 install --upgrade -r requirements-prod.txt && python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput && python3 manage.py create_vinyl_admin
```

### Команда запуска

```bash
gunicorn vinylsite.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

## 3. Переменные окружения

В настройках приложения → **Переменные**:

| Ключ | Пример значения |
|------|-----------------|
| `DJANGO_SECRET_KEY` | длинная случайная строка (сгенерируйте новую!) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `myvinyl.ru,www.myvinyl.ru` (без пробелов, через запятую) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://myvinyl.ru,https://www.myvinyl.ru` |

Timeweb также поддерживает переменную `DJANGO_ALLOWED_HOSTS` в документации — дублируйте домен в обеих настройках, если панель предлагает отдельное поле.

## 4. Администратор после деплоя

При сборке выполняется `create_vinyl_admin`:

| | |
|---|---|
| **Логин** | `vinyladmin` |
| **Пароль** | `VinylCol2026!` |

**Сразу после первого входа смените пароль** (админка Django `/admin/` → пользователи) или задайте свой пароль локально и пересоберите.

## 5. Перенос данных с локального компьютера

На своём ПК (в каталоге проекта):

```powershell
cd c:\metrica\vinyl_collection
# убедитесь, что есть db.sqlite3 и media/
```

После деплоя загрузите через **файловый менеджер / SFTP** хостинга в корень приложения (рядом с `manage.py`):

- `db.sqlite3`
- каталог `media/` целиком

Перезапустите приложение в панели.

## 6. Проверка

1. Откройте домен — должна открыться страница **Вход**
2. Войдите как `vinyladmin`
3. Проверьте каталог, фото, раздел **Пользователи**
4. Статика (CSS) — через WhiteNoise, отдельный nginx не обязателен

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
