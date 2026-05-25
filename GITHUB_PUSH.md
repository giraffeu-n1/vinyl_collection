# Загрузка на GitHub (giraffeu-n1)

Локальный репозиторий готов: ветка `main`, коммит создан, remote:

`https://github.com/giraffeu-n1/vinyl_collection.git`

**Пароль от аккаунта в git не подставляется** — GitHub принимает только [Personal Access Token](https://github.com/settings/tokens) (PAT) или SSH-ключ.

## 1. Смените пароль GitHub

Вы отправили пароль в чат — зайдите на https://github.com/settings/security и **смените пароль**.

## 2. Создайте токен

1. https://github.com/settings/tokens → **Generate new token (classic)**
2. Права: **repo**
3. Скопируйте токен (показывается один раз)

## 3. Создайте пустой репозиторий (если ещё нет)

https://github.com/new → имя **vinyl_collection** → **без** README/.gitignore → Create

## 4. Отправьте код (PowerShell)

```powershell
$env:Path += ";C:\Program Files\GitHub CLI"
cd c:\metrica\vinyl_collection

# Вариант А — GitHub CLI (удобно)
gh auth login
# Выберите: GitHub.com → HTTPS → Login with a web browser
gh repo create vinyl_collection --public --source=. --remote=origin --push

# Вариант Б — только git (вместо пароля вставьте PAT)
git push -u origin main
```

При `git push` логин: `giraffeu-n1`, пароль: **вставьте PAT**, не пароль от сайта.

## Что не попало в Git

По `.gitignore`: `db.sqlite3`, `media/`, `.env` — переносите на Timeweb отдельно (см. DEPLOY_TIMEWEB.md).
