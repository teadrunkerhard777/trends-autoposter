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

## 2. Обычные посты

Параметры запроса:

- Title: `Ну и ГАДЖЕТЫ — посты`
- URL: `https://api.github.com/repos/teadrunkerhard777/trends-autoposter/actions/workflows/autoposter.yml/dispatches`
- Method: `POST`
- Тело запроса: `{"ref":"main"}`
- Header `Accept`: `application/vnd.github+json`
- Header `Authorization`: `Bearer YOUR_FINE_GRAINED_TOKEN`
- Header `Content-Type`: `application/json`
- Header `X-GitHub-Api-Version`: `2026-03-10`

Этот workflow принудительно использует режим `photo`: существующая задача
продолжает публиковать обычные посты и не превращается в видеозадачу.

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

Все эти запуски продолжают публиковать обычные фото-посты.

## 4. Отдельная задача для стоковых видео

Создайте вторую независимую задачу cron-job.org:

- Title: `Ну и ГАДЖЕТЫ — видео`
- URL: `https://api.github.com/repos/teadrunkerhard777/trends-autoposter/actions/workflows/video-autoposter.yml/dispatches`
- Method: `POST`
- Тело запроса: `{"ref":"main"}`
- Заголовки и Fine-grained token: те же, что у обычной задачи
- Timezone: `Asia/Yekaterinburg`
- Hours: `13, 21`
- Minutes: `0`
- Cron: `0 13,21 * * *`

Если задача настроена в UTC, используйте `0 8,16 * * *`.

Время специально сдвинуто относительно обычных публикаций: видео выходят
между постами в 11:00/15:00 и 19:00/23:00, а не одновременно с ними.

Новый workflow принудительно включает видеорежим. Он ищет вертикальный ролик
сначала в Pexels, затем в Pixabay, накладывает оформление и публикует его с
заметкой. Если оба источника или рендеринг недоступны, используется
анимированная картинка новости, затем фото или текст. Общая блокировка не
позволяет обычной и видеозадаче публиковаться одновременно, а общая история
защищает от повторов.

Для живого фона добавьте ключ официального Pexels API в GitHub Secret с точным
именем `PEXELS_API_KEY`. Workflow передаёт его только процессу автопостера.
Если ключ отсутствует, лимит API исчерпан или подходящий вертикальный ролик не
найден, публикация автоматически использует анимированную картинку новости.

Для резервного Pixabay добавьте GitHub Secret `PIXABAY_API_KEY`. Поисковые
ответы Pixabay кешируются на 24 часа через GitHub Actions cache; видео всегда
скачивается во временный файл и сопровождается ссылкой на автора и источник.

В расширенном редакторе расписания обычной задачи:

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

## 5. Проверьте один раз

Запустите тестовое выполнение на cron-job.org. После успешного запроса на
странице **Actions** репозитория должен появиться новый запуск. Workflow
выполнит тесты, запустит автопостер и обновит `storage/published.json` только
после подтверждённой отправки сообщения в Telegram.

До проверки добавьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в GitHub:
**Settings → Secrets and variables → Actions**. Не меняйте настройку workflow
`cancel-in-progress: false`: пересекающиеся запуски не должны прерывать
публикацию с неизвестным результатом.
