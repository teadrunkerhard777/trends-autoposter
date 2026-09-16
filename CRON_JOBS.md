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

## Расширенные настройки запроса

В блоке **Advanced / Расширенные настройки** укажите:

- Request method: `POST`
- Request timeout: `30 seconds`
- Follow redirects / Treat redirects as success: `Off`
- Save responses: `Off` после успешной проверки
- HTTP basic authentication: `Off`
- Request body type: `Raw / application/json`
- Request body: `{"ref":"main"}` без переносов и дополнительных полей

Если интерфейс предлагает автоматические повторы запроса, отключите их. При
потере ответа повторный `POST` может запустить второй workflow. Защитная
настройка `concurrency` не даст двум публикациям идти одновременно, но лишний
запуск всё равно потратит время GitHub Actions.

GitHub должен ответить успешным кодом `200`. Ответы `401` и `403` означают
ошибку токена или недостаточное разрешение **Actions — Read and write**; `404`
обычно означает неверный адрес workflow, репозиторий или ветку.

## 3. Установите расписание

Запускать ежедневно в:

- 11:00 Asia/Yekaterinburg
- 15:00 Asia/Yekaterinburg
- 19:00 Asia/Yekaterinburg
- 23:00 Asia/Yekaterinburg

Если на cron-job.org выбран UTC, укажите 06:00, 10:00, 14:00 и 18:00 UTC.
Эквивалентное cron-выражение: `0 6,10,14,18 * * *`.

При `AUTOPOSTER_MEDIA_MODE=auto` запуски в 15:00 и 19:00 создают короткие
нативные MP4-ролики. Запуски в 11:00 и 23:00 продолжают публиковать обычные
фото-посты. Если в видеослоте нет подходящей новости или ролик не удалось
подготовить, используется фото либо текст. История не допускает второго
подтверждённого видео в том же слоте.

Для живого фона добавьте ключ официального Pexels API в GitHub Secret с точным
именем `PEXELS_API_KEY`. Workflow передаёт его только процессу автопостера.
Если ключ отсутствует, лимит API исчерпан или подходящий вертикальный ролик не
найден, публикация автоматически использует анимированную картинку новости.

В расширенном редакторе расписания:

- Timezone: `Asia/Yekaterinburg`
- Minutes: `0`
- Hours: `11, 15, 19, 23`
- Days of month: `Every day`
- Months: `Every month`
- Days of week: `Every day`
- Expiration date: `Never`

Не задавайте одновременно локальные часы и UTC-выражение: выберите один из
двух вариантов, иначе время запуска сместится на пять часов.

## Уведомления

Рекомендуемые настройки:

- Notify on failure: `On`
- Number of failures before notification: `1`
- Notify when execution succeeds after failure: `On`
- Notify when job is automatically disabled: `On`
- Notify on every success: `Off`
- SSL certificate expiry notification: `Off` — запрос идёт на GitHub

## 4. Проверьте один раз

Запустите тестовое выполнение на cron-job.org. После успешного запроса на
странице **Actions** репозитория должен появиться новый запуск. Workflow
выполнит тесты, запустит автопостер и обновит `storage/published.json` только
после подтверждённой отправки сообщения в Telegram.

До проверки добавьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в GitHub:
**Settings → Secrets and variables → Actions**. Не меняйте настройку workflow
`cancel-in-progress: false`: пересекающиеся запуски не должны прерывать
публикацию с неизвестным результатом.
