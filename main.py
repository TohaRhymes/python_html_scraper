import argparse
from urllib.request import urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup
from bs2json import bs2json
import validators
from difflib import SequenceMatcher
from os.path import join
from collections import Counter

## HERE ARE THE PARAMETERS
URL = None
POSTFIX_NAME = None
DIR = None
ENCODING = None
N_TO_CROSS_CHECK = None
PAGES_DELETE_CUTOFF = None
SAME_DELETE_CUTOFF = None

## HERE CODE STARTS

STOP_WORDS = ['style', 'script']


def sort_by_similarity(cur_url):
    """Отсортировать строчки по схожести с анализируемым URL'ом."""
    return SequenceMatcher(None, cur_url, URL).ratio()


def get_second(array):
    """Получить второй элемент в массиве"""
    return array[1]


def get_third(array):
    """Получить третий элемент в массиве"""
    return array[2]


def unflatten(list_of_lists):
    """
    Развернуть лист листов в лист
    """
    return [val for sublist in list_of_lists for val in sublist]


def bfs(soup, depth=0):
    """
    BFS на BeautifulSoup'ном дереве
    Код из:
    https://stackoverflow.com/questions/44798715/how-to-do-a-breadth-first-search-easily-with-beautiful-soup
    """
    text_array = []  # (depth, DOM-way, text)
    link_array = []  # http-links
    queue = [([], soup, depth)]  # queue of (path, element, depth) pairs
    while queue:
        path, element, cur_depth = queue.pop(0)
        if hasattr(element, 'children'):  # check for leaf elements
            for child in element.children:
                queue.append((path + [child.name if child.name is not None else type(child)],
                              child,
                              cur_depth + 1))
        if hasattr(element, 'href'):
            try:
                if validators.url(element.attrs['href']):
                    # print(element.attrs['href'])
                    link_array.append(element.attrs['href'])
            # иногда валится, но только в узлах где вместо ссылок какая-то хрень.
            except KeyError:
                pass
        if element.string and element.string != '\n' and all([node not in STOP_WORDS for node in path]):
            text_array.append((cur_depth, ' '.join(map(str, path)), element.string.strip()))
            pass
    return text_array, list(set(link_array))


class HtmlParseError(Exception):
    pass


def compress_tags(tags):
    count_neighbours = []
    prev_tag = tags[0]
    counter = 1
    for cur_tag in tags[1:]:
        if cur_tag == prev_tag:
            counter += 1
        else:
            count_neighbours.append((prev_tag, counter))
            prev_tag = cur_tag
            counter = 1
    count_neighbours.append((prev_tag, counter))
    return count_neighbours


def save_text(text, dir, prefix, postfix, format='txt'):
    file_name = join(dir, f'{prefix}_{postfix}.{format}')
    with open(file_name, 'w') as out_file:
        out_file.write(text)
    return file_name


class Page():
    def __init__(self, url, encoding='utf-8'):
        self.url = url  # ссылка, с которой работаем
        self.html_text = None  # сырой html-текст
        self.soup = None  # BS-объект
        self.encoding = encoding  # используемая кодировка страницы
        self.link_array = None  # ссылки, находящиеся на этой странице
        self.text_array = None  # массив текстов (всех)
        self.filtered_text_array = None  # отфильтрованный массив текстов
        self.probable_tables = None  # массив с возможными таблицами

    def __read_html(self):
        """
        Служебная функция.

        Просто прочитать и сохранить html-ку
        """
        try:
            self.html_text = urlopen(self.url).read().decode(self.encoding)
        except URLError:
            pass
        return self.html_text

    def __make_soup(self):
        """
        Служебная функция.

        Делаем супчик.

        :return: BeautifulSoup Object
        """
        self.soup = BeautifulSoup(self.html_text, "html.parser")  ## мб 'html5lib'
        return self.soup

    def __extract_info(self):
        """
        Служебная функция.

        Прохоимся поиском в ширину и извлекаем весь текст и все ссылки
        (в ширину - чтобы еще помнить уровень вложенности каждого текста).

        :return: массив строк и массив ссылок
        """
        self.text_array, self.link_array = bfs(self.soup)
        return self.text_array, self.link_array

    def __filter_common(self):
        """
        Служебная функция.

        Доп функция - убрать "мусорные" куски текста - те,
        Которые повторяются на многих страницах сайта.
        Скорее всего это всякие хедеры и т.д.
        """
        self.link_array.sort(key=sort_by_similarity, reverse=True)
        inner_link_texts = [list(map(get_third, set(self.text_array)))]
        for link in self.link_array[:N_TO_CROSS_CHECK]:
            cur_text_array = Page(link).read_url_return_info(return_text=True)
            inner_link_texts.append(list(map(get_third, set(cur_text_array))))
        # можно просто развернуть листы в один большой лист, так как я уже убрал дубликаты
        # и составить топ одинаковых кусков
        all_text_counter = Counter(unflatten(inner_link_texts))
        all_texts_to_delete = list(
            dict(filter(lambda x: x[1] > N_TO_CROSS_CHECK * PAGES_DELETE_CUTOFF, all_text_counter.items())).keys())
        self.filtered_text_array = list(
            filter(lambda text: get_third(text) not in all_texts_to_delete, self.text_array))

    def __filter_garbage(self):
        """
        Служебная функция.

        Еще одна функция для фильтрации.
        Удаляет куски, которые повторяются,
        (обычно это названия кнопок и тому подобная фигня)
        """
        text_counter = Counter(list(map(get_third, self.text_array)))
        texts_to_delete = list(dict(filter(lambda x: x[1] > SAME_DELETE_CUTOFF, text_counter.items())).keys())
        self.filtered_text_array = list(
            filter(lambda text: get_third(text) not in texts_to_delete, self.filtered_text_array))

    def read_url_return_info(self, to_filter=False, return_text=False):
        """
        Запуск основного анализатора:
        - читаем страницу
        - делаем из нее суп
        - получаем список текстов и ссылок
        - фильтруем при необходимости

        :param to_filter: если True, полученные массив текстов отфильтруем
        :param return_text: если True, вернуть результат (иначе его можно добыть по аттрибутам класса)
        """
        self.__read_html()
        try:
            self.__make_soup()
        except TypeError:
            raise HtmlParseError('Ошибка чтения страницы...\nЕмае!')
        self.text_array, self.link_array = bfs(self.soup)

        self.link_array = set(self.link_array)
        if self.url in self.link_array:
            self.link_array.remove(self.url)
        self.link_array = list(self.link_array)

        if to_filter:
            self.__filter_common()
            self.__filter_garbage()

        if return_text:
            return self.text_array

    def extract_table(self):
        """
        Извлечь все вероятные таблицы со страницы.
        """
        tags = list(
            filter(lambda x: "bs4.element" not in x, map(get_second, self.text_array))
        )
        compressed_tags = compress_tags(tags)
        significant_tags = list(filter(lambda x: x[1] > 5, sorted(compressed_tags, key=lambda tup: -tup[1])))
        self.probable_tables = []
        for tag, _ in significant_tags:
            self.probable_tables.append(self.soup.select(tag))


def parse_args():
    """
    Parse command line arguments.
    """

    global URL
    global DIR
    global POSTFIX_NAME
    global ENCODING
    global N_TO_CROSS_CHECK
    global PAGES_DELETE_CUTOFF
    global SAME_DELETE_CUTOFF

    parser = argparse.ArgumentParser()
    # URL = 'https://news.mit.edu/'
    # URL = 'https://www.ozon.ru/category/hokkey-11232/'
    #     POSTFIX_NAME = 'mit_save'
    #     POSTFIX_NAME = 'ozon_save'
    parser.add_argument("-url", "--url", help="URL с которым будем работать.", type=str, required=True)
    parser.add_argument("-dir", '--dir', help="Директория, в которую сохранять файлв", type=str, default='./')
    parser.add_argument("-out", "--postfix_name", help="Постфикс имени файла, в который будем сохранять текст.",
                        type=str)
    parser.add_argument("-enc", "--encoding", help="Кодировка страницы, которую будем парсить", type=str,
                        default='utf-8')

    filtration_group = parser.add_argument_group("Параметры")
    filtration_group.add_argument("-ncc", "--n_to_cross_check",
                                  help="Сколько ссылок мы возьмем для поиска похожих (мусорных) кусков.\n"
                                       "0 <= ncc <= 15", type=int,
                                  default=8)
    filtration_group.add_argument("-pdc", "--pages_delete_cutoff",
                                  help="Удалить текст, который представлен в такой части страниц.\n"
                                       "0 <= pdc <= 1", type=float,
                                  default=0.75)
    filtration_group.add_argument("-sdc", "--same_delete_cutoff",
                                  help="Удалить текст, который встречается на странице больше,"
                                       "чем это число раз (для кнопок и тд).\n"
                                       "0 <= sdc",
                                  type=int, default=4)
    args = parser.parse_args()

    ## HERE ARE THE PARAMETERS
    URL = args.url
    DIR = args.dir
    POSTFIX_NAME = args.postfix_name
    ENCODING = args.encoding
    N_TO_CROSS_CHECK = min(max(0, args.n_to_cross_check), 15)
    PAGES_DELETE_CUTOFF = min(max(0, args.pages_delete_cutoff), 1)
    SAME_DELETE_CUTOFF = max(0, args.same_delete_cutoff)


def main():
    """
    Тут происходит вся магия
    """

    parse_args()

    print('Анализ страницы...')

    # прочитать страницу
    main_page = Page(URL)
    try:
        # извлечь всю инфу + отфильтровать грязный текст
        main_page.read_url_return_info(to_filter=True)
    except HtmlParseError as e:
        print(str(e))
        return

    # выведем инфу об извлеченном тексте и сохраним информацию
    html_text = main_page.html_text
    plain_text = '\n'.join(list(map(get_third, main_page.text_array)))
    filtered_text = '\n'.join(list(map(get_third, main_page.filtered_text_array)))

    page_length = len(html_text)
    plain_text_length = len(plain_text)
    filtered_text_length = len(filtered_text)
    print(f'\nАнализируемая страница: {URL}')
    print(f'Длина html-страницы:\t\t\t{page_length}')
    print(f'Длина извлеченного текста:'
          f'\t\t{plain_text_length}'
          f'\t({round(plain_text_length / page_length * 100, 2)}%)')
    print(f'Длина отфильтрованного текста:'
          f'\t{filtered_text_length}'
          f'\t({round(filtered_text_length / page_length * 100, 2)}%)')
    print()

    print('Сохранение html-текста...')
    html_text_file = save_text(html_text, DIR, 'html', POSTFIX_NAME)
    print(f'Html-текст сохранен в: {html_text_file}')

    print('Сохранение извлеченного текста...')
    plain_text_file = save_text(plain_text, DIR, 'plain', POSTFIX_NAME)
    print(f'Извлеченный текст сохранен в: {plain_text_file}')

    print('Сохранение отфильтрованного текста...')
    filtered_text_file = save_text(filtered_text, DIR, 'filtered', POSTFIX_NAME)
    print(f'Отфильтрованный текст сохранен в: {filtered_text_file}')

    # извлечем и сохраним таблицы
    print()
    print('Извлечение таблиц...')
    main_page.extract_table()
    tables = main_page.probable_tables

    print()
    print('Запись возможных таблиц...')
    converter = bs2json()
    for index, table in enumerate(tables):
        json_text = str(converter.convertAll(table, join=True))
        table_file = save_text(json_text, DIR, f'raw_table_{index}', POSTFIX_NAME, format='json')
        print(f'html-текст с возможной таблицей сохранен в: {table_file}')

    print('\nСпасибо за пользование тулом!\nПодписывайтесь в соц сетях по нику:\n@TohaRhymes или @Toha_Rhymes')


if __name__ == '__main__':
    main()
