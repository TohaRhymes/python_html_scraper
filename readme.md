# Скрэпинг-тул HTML'ек

## Параметры:

```
usage: main.py [-h] -url URL [-dir DIR] [-out POSTFIX_NAME] [-enc ENCODING] [-ncc N_TO_CROSS_CHECK] [-pdc PAGES_DELETE_CUTOFF] [-sdc SAME_DELETE_CUTOFF]

options:
  -h, --help            show this help message and exit
  -url URL, --url URL   URL с которым будем работать.
  -dir DIR, --dir DIR   Директория, в которую сохранять файлв
  -out POSTFIX_NAME, --postfix_name POSTFIX_NAME
                        Постфикс имени файла, в который будем сохранять текст.
  -enc ENCODING, --encoding ENCODING
                        Кодировка страницы, которую будем парсить

Параметры:
  -ncc N_TO_CROSS_CHECK, --n_to_cross_check N_TO_CROSS_CHECK
                        Сколько ссылок мы возьмем для поиска похожих (мусорных) кусков. 0 <= ncc <= 15
  -pdc PAGES_DELETE_CUTOFF, --pages_delete_cutoff PAGES_DELETE_CUTOFF
                        Удалить текст, который представлен в такой части страниц. 0 <= pdc <= 1
  -sdc SAME_DELETE_CUTOFF, --same_delete_cutoff SAME_DELETE_CUTOFF
                        Удалить текст, который встречается на странице больше,чем это число раз (для кнопок и тд). 0 <= sdc

```


## Пример запуска:

#### Вызов
```text
python main.py -url 'https://news.mit.edu/' -dir data/ -out mit
```
#### Вывод:

```text
Анализ страницы...

Анализируемая страница: https://news.mit.edu/
Длина html-страницы:                    190629
Длина извлеченного текста:              27444   (14.4%)
Длина отфильтрованного текста:  23279   (12.21%)

Сохранение html-текста...
Html-текст сохранен в: data/html_mit.txt
Сохранение извлеченного текста...
Извлеченный текст сохранен в: data/plain_mit.txt
Сохранение отфильтрованного текста...
Отфильтрованный текст сохранен в: data/filtered_mit.txt

Извлечение таблиц...

Запись возможных таблиц...
html-текст с возможной таблицей сохранен в: data/raw_table_0_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_1_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_2_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_3_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_4_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_5_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_6_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_7_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_8_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_9_mit.json
html-текст с возможной таблицей сохранен в: data/raw_table_10_mit.json

Спасибо за пользование тулом!
Подписывайтесь в соц сетях по нику:
@TohaRhymes или @Toha_Rhymes
```

#### Вызов
```text
python main.py -url 'https://academy.yandex.ru/dataschool/course/machine-learning' -dir data/ -out shad
```
#### Вывод:

```text
Анализ страницы...

Анализируемая страница: https://academy.yandex.ru/dataschool/course/machine-learning
Длина html-страницы:                    163631
Длина извлеченного текста:              30833   (18.84%)
Длина отфильтрованного текста:  29078   (17.77%)

Сохранение html-текста...
Html-текст сохранен в: data/html_shad.txt
Сохранение извлеченного текста...
Извлеченный текст сохранен в: data/plain_shad.txt
Сохранение отфильтрованного текста...
Отфильтрованный текст сохранен в: data/filtered_shad.txt

Извлечение таблиц...

Запись возможных таблиц...
html-текст с возможной таблицей сохранен в: data/raw_table_0_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_1_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_2_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_3_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_4_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_5_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_6_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_7_shad.json
html-текст с возможной таблицей сохранен в: data/raw_table_8_shad.json

Спасибо за пользование тулом!
Подписывайтесь в соц сетях по нику:
@TohaRhymes или @Toha_Rhymes
```

