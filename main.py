from urllib.request import urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup
import validators
from difflib import SequenceMatcher
from os.path import join
from collections import Counter

## HERE ARE PARAMETERS
URL = 'https://www.ozon.ru/highlight/globalpromo/'  # url с которым будем работать
PREFIX_NAME = 'ozon_save'  # префикс для файла, в который сохранять будем
ENCODING = 'utf-8'  # кодировка, e.g. ['utf-8', 'cp1251']
N_TO_CROSS_CHECK = 8  # сколько ссылок мы возьмем для поиска похожих
PAGES_DELETE_CUTOFF = 0.7  # удалить текст, который представлен в такой части страниц
SAME_DELETE_CUTOFF = 4  # удалить текст, который встречается на странице больше чем это число раз (для кнопок и тд)
DIR = 'data/'

## HERE CODE STARTS

STOP_WORDS = ['style', 'script']


def sort_by_similarity(cur_url):
    return SequenceMatcher(None, cur_url, URL).ratio()


def get_second(array):
    return array[1]


def get_third(array):
    return array[2]


def unflatten(list_of_lists):
    return [val for sublist in list_of_lists for val in sublist]


## From: https://stackoverflow.com/questions/44798715/how-to-do-a-breadth-first-search-easily-with-beautiful-soup
def bfs(soup, depth=0):
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
            text_array.append((cur_depth, '/'.join(map(str, path)), element.string.strip()))
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


class Page():
    def __init__(self, url, encoding='utf-8'):
        self.probable_tables = None
        self.html_text = None
        self.soup = None
        self.encoding = encoding
        self.link_array = None
        self.text_array = None
        self.filtered_text_array = None
        self.url = url

    def __read_html(self):
        try:
            self.html_text = urlopen(self.url).read().decode(self.encoding)
        except URLError:
            pass
        return self.html_text

    def __make_soup(self):
        self.soup = BeautifulSoup(self.html_text, "html.parser")  ## мб 'html5lib'
        return self.soup

    def __extract_info(self):
        self.text_array, self.link_array = bfs(self.soup)
        return self.text_array, self.link_array

    # доп функция - убрать "мусорные" куски текста - те,
    # которые повторяются на многих страницах сайта.
    # Скорее всего это всякие хедеры и т.д.
    def __filter_common(self):
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

    # еще удалю куски, которые повторяются (обычно это названия кнопок и тому подобная фигня)
    def __filter_garbage(self):
        text_counter = Counter(list(map(get_third, self.text_array)))
        texts_to_delete = list(dict(filter(lambda x: x[1] > SAME_DELETE_CUTOFF, text_counter.items())).keys())
        self.filtered_text_array = list(
            filter(lambda text: get_third(text) not in texts_to_delete, self.filtered_text_array))

    def read_url_return_info(self, to_filter=False, return_text=False):
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

        tags = list(
            filter(lambda x: "bs4.element" not in x, map(get_second, self.text_array))
        )

        compressed_tags = compress_tags(tags)
        significant_tags = list(filter(lambda x: x[1] > 5, sorted(compressed_tags, key=lambda tup: -tup[1])))
        self.probable_tables = []
        for tag in significant_tags:
            self.probable_tables.append(self.soup.select(tag))


def save_text(text, dir, prefix, postfix):
    file_name = join(dir, f'{prefix}_{postfix}.txt')
    with open(file_name, 'w') as out_file:
        out_file.write(text)
    return file_name


def main():
    main_page = Page(URL)
    try:
        main_page.read_url_return_info(to_filter=True)
    except HtmlParseError as e:
        print(str(e))
        return

    html_text = main_page.html_text
    plain_text = '\n'.join(list(map(get_third, main_page.text_array)))
    filtered_text = '\n'.join(list(map(get_third, main_page.filtered_text_array)))

    page_length = len(html_text)
    plain_text_length = len(plain_text)
    filtered_text_length = len(filtered_text)
    print(f'Анализируемая страница: {URL}')
    print(f'Длина html-страницы:\t\t\t{page_length}')
    print(f'Длина извлеченного текста:'
          f'\t\t{plain_text_length}'
          f'\t({round(plain_text_length / page_length * 100, 2)}%)')
    print(f'Длина отфильтрованного текста:'
          f'\t{filtered_text_length}'
          f'\t({round(filtered_text_length / page_length * 100, 2)}%)')
    print()

    print('Сохранение html-текста...')
    html_text_file = save_text(html_text, DIR, 'html', PREFIX_NAME)
    print(f'Html-текст сохранен в: {html_text_file}')

    print('Сохранение извлеченного текста...')
    plain_text_file = save_text(plain_text, DIR, 'plain', PREFIX_NAME)
    print(f'Извлеченный текст сохранен в: {plain_text_file}')

    print('Сохранение отфильтрованного текста...')
    filtered_text_file = save_text(filtered_text, DIR, 'filtered', PREFIX_NAME)
    print(f'Отфильтрованный текст сохранен в: {filtered_text_file}')

    count_DOM_ways = Counter(map(get_second, main_page.text_array))

    print(count_DOM_ways)


if __name__ == '__main__':
    main()
