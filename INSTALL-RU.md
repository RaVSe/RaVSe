# RaVSe · Зелёный маг — установка на GitHub

Это самостоятельный проект для **профильного README GitHub**. В нём нет слов или подписей внутри самой GIF. Изображение с замками и 53 × 7 клетками — это анимированный баннер, **не изменение стандартного календаря на github.com**.

## 1. Создай профильный репозиторий

1. Авторизуйся в GitHub как **RaVSe**.
2. Перейди на https://github.com/new
3. Repository name: `RaVSe` (точно совпадает с именем профиля).
4. Выбери **Public** и создай репозиторий. Если GitHub предложит создать README, можешь согласиться, но наш `README.md` затем должен его заменить.

## 2. Залей проект

Самый надёжный способ — Git (Windows PowerShell, нужен установленный Git):

```powershell
git clone https://github.com/RaVSe/RaVSe.git
cd RaVSe
```

Распакуй ZIP, скачанный из ChatGPT. Скопируй **всё содержимое** распакованной папки *в папку RaVSe*, в том числе скрытую `.github`. Итог: рядом друг с другом должны лежать `README.md`, `requirements.txt`, `assets`, `scripts`, `.github`, `tests`.

```powershell
git add .
git commit -m "Add green mage contribution animation"
git push origin main
```

> Если GitHub уже создал репозиторий с README, `git clone` скопирует его; просто замени его нашим файлом перед коммитом.
>
> Через веб-интерфейс GitHub тоже можно нажать **Add file → Upload files** и перетащить все файлы и папки из распакованного архива. ВАЖНО: после загрузки проверь, что файл `.github/workflows/update-mage.yml` на месте.

## 3. Разреши запись для Actions

В репозитории открой **Settings → Actions → General → Workflow permissions** и выбери **Read and write permissions**, затем Save, если пункт доступен. Это нужно, чтобы Actions мог сохранить обновлённый GIF в репозиторий. Файл workflow уже содержит минимально необходимое разрешение `contents: write`.

## 4. Запусти первый раз

Открой **Actions → Update Green Mage calendar → Run workflow** (ветка `main`). Дождись зелёного статуса, после этого открой https://github.com/RaVSe.

Первоначальная GIF из архива — **демонстрация с вымышленными клетками**, чтобы было видно результат ещё до настройки. **После первого успешного Actions GIF будет автоматически создан на базе реальной публичной активности RaVSe**, и затем обновится каждый день.

Автообновление: каждый день около 04:37 UTC (GitHub Actions `schedule`, фактический старт может немного задержаться).

## 5. Как изменить внешний вид или скорость

- Число целей за цикл: в `.github/workflows/update-mage.yml` поменяй команду на `python scripts/main.py --login RaVSe --shots 18`. По умолчанию **12**.
- Скорость: в `scripts/build_gif.py` параметр `ms=120` — количество миллисекунд на кадр. `ms=160` — медленнее; `ms=90` — быстрее.
- Размер сетки/баннера: константы `W`, `H`, `CELL`, `GAP`, `GRID_X`, `GRID_Y` в `scripts/render_frames.py` (при изменении размера холста также понадобится фон нужного размера).
- Цвета клеток: кортеж `CELL_COLORS` там же.
- Фон с замками: `assets/castle-bg.png`.
- Анимации персонажа из папки `2`: `assets/mage-flying.gif` (полёт), `assets/mage-cast-spell.gif` (поднятие рук, заряд и восстановление), `assets/green-projectile.gif` (снаряд). Генератор использует эти локальные копии; папка `2` для запуска не требуется.
- Плавность полёта и синхронизация заклинания с клетками: `frames_schedule`, `MageAnimation`, `draw_mage`, `draw_projectile` в `scripts/render_frames.py`. Пиксели увеличиваются ровно в 3 раза без сглаживания.

## 6. Локальная проверка на Windows

Из папки репозитория запусти:

```powershell
py -m pip install -r requirements.txt
py scripts/main.py --demo
py -m unittest discover -s tests
```

Для настоящего календаря локально потребуется токен (не добавляй токен в Git и не публикуй его):

```powershell
$env:GITHUB_TOKEN = 'ТВОЙ_ТОКЕН'
py scripts/main.py --login RaVSe
```

## Частые проблемы

**В Actions не появился workflow:** проверь, что `.github/workflows/update-mage.yml` находится именно в default branch (`main`) и Actions разрешены.

**`Resource not accessible by integration` при GraphQL:** встроенный `GITHUB_TOKEN` иногда ограничен политикой GitHub / организации. Если для публичного календаря он не подходит, создай отдельный пользовательский токен с минимально необходимым доступом к профилю (для classic PAT — `read:user`), затем в репозитории открой **Settings → Secrets and variables → Actions → New repository secret**, имя `PROFILE_TOKEN`. Этот секрет уже поддерживается workflow. Не нужно давать токену `repo` или другие права на запись ради чтения календаря.

**Не обновляется GIF:** проверь красный шаг в Actions и доступ на запись (`contents: write`). Сначала всегда проверяй лог: ошибка API, ошибка генерации и ошибка `git push` решаются по-разному.

**GIF показывает не все разрушения:** это задумано. За один повтор маг выбирает до 12 активных клеток, распределённых по году, а не сотни выстрелов подряд. Всё равно все активные клетки присутствуют в календаре и окрашены по настоящим уровням. В следующем дневном обновлении может измениться и выбранный набор целей.

**Пустой профиль:** GitHub отображает профильный README только у публичного репозитория, название которого в точности совпадает с логином, и в корне которого есть `README.md`.

**Почему иногда активность не совпадает со списком коммитов?** Contribution calendar учитывает разные типы contributions (например issues и pull requests), а также применяет свои правила для засчитывания коммитов.

API reference: https://docs.github.com/en/graphql/reference/users#contributioncalendar

Секреты: никаких секретов в ZIP и `README.md` нет; `GITHUB_TOKEN` предоставляется Actions автоматически.
