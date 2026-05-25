# Данные для деплоя на Timeweb App Platform

У App Platform **нет SSH/SFTP** в контейнер — база и фото попадают на сервер **только через Git** при сборке.

## Подготовка (на вашем ПК)

```powershell
cd c:\metrica\vinyl_collection
.\scripts\prepare_deploy_data.ps1
```

Скрипт копирует `db.sqlite3` и `media/` сюда, в `deploy-data/`.

Затем закоммитьте и отправьте на GitHub:

```powershell
git add deploy-data
git commit -m "Add collection database and media for Timeweb deploy"
git push origin main
```

После этого в Timeweb нажмите **Пересобрать** приложение.

## Важно

- Репозиторий лучше сделать **приватным** (в базе учётные записи).
- Обновление фото/альбомов: снова запустите скрипт, `git push`, пересборка на Timeweb.
- Папки `db.sqlite3` и `media/` в корне проекта в Git **не** попадают (только `deploy-data/`).
