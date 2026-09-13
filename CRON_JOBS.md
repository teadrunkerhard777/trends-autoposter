# Настройка cron-job.org

Внешний планировщик запускает существующий workflow GitHub Actions. Он не
обращается к Telegram напрямую и не получает данные Telegram-бота.

## 1. Создайте токен GitHub

Создайте fine-grained personal access token только для этого репозитория:

- Репозиторий: `teadrunkerhard777/trends-autoposter`
- Repository permission: **Actions — Read and write**
- Установите срок действия и замените токен до его окончания.

Не добавляйте этот токен в репозиторий. Он используется только в приватном
заголовке запроса на cron-job.org.

## 2. Создайте задачу на cron-job.org

Параметры запроса:

- Title: `Trends Autoposter`
- URL: `https://api.github.com/repos/teadrunkerhard777/trends-autoposter/actions/workflows/autoposter.yml/dispatches`
- Method: `POST`
- Тело запроса: `{"ref":"main"}`
- Header `Accept`: `application/vnd.github+json`
- Header `Authorization`: `Bearer YOUR_FINE_GRAINED_TOKEN`
- Header `Content-Type`: `application/json`
- Header `X-GitHub-Api-Version`: `2026-03-10`

Сохраните GitHub-токен только в приватном заголовке `Authorization`. Не
добавляйте настоящий токен в URL, тело запроса, репозиторий, скриншоты или логи.

## 3. Установите расписание

Запускать ежедневно в:

- 11:00 Asia/Yekaterinburg
- 15:00 Asia/Yekaterinburg
- 19:00 Asia/Yekaterinburg
- 23:00 Asia/Yekaterinburg

Если на cron-job.org выбран UTC, укажите 06:00, 10:00, 14:00 и 18:00 UTC.
Эквивалентное cron-выражение: `0 6,10,14,18 * * *`.

## 4. Проверьте один раз

Запустите тестовое выполнение на cron-job.org. После успешного запроса на
странице **Actions** репозитория должен появиться новый запуск. Workflow
выполнит тесты, запустит автопостер и обновит `storage/published.json` только
после подтверждённой отправки сообщения в Telegram.

До проверки добавьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в GitHub:
**Settings → Secrets and variables → Actions**. Не меняйте настройку workflow
`cancel-in-progress: false`: пересекающиеся запуски не должны прерывать
публикацию с неизвестным результатом.
