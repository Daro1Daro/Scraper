from bs4 import BeautifulSoup

from requests.exceptions import RequestException
from requests import Session


class ScrapingError(Exception):
    pass


def scrape(urls):
    visited_urls = set()
    results = []
    invalids = {}

    session = Session()

    for url in urls:
        normalized_url = normalize_url(url)

        if normalized_url in visited_urls:
            continue

        try:
            resp = get_site(url, session)
            result = scrape_site(resp)
            result["URL"] = url
            results.append(result)
            visited_urls.add(normalized_url)
        except ScrapingError as error:
            invalids[url] = str(error)

    session.close()

    return results, invalids


def normalize_url(url):
    normalized = url.replace("http://", "")
    normalized = url.replace("https://", "")

    return normalized


# Raises Scraping error
def get_site(url, session):
    try:
        resp = session.get(url)
    except RequestException as exception:
        raise ScrapingError("Error: {} while fetching url: {}.".format(str(exception), url))

    if resp.status_code != 200:
        raise ScrapingError("HTTP GET status not 200, but: {}".format(resp.status_code))

    content_type = resp.headers['Content-Type'].lower()
    if content_type is None or content_type.find('html') == -1:
        raise ScrapingError("Invalid Content-Type: {}.".format(content_type))

    return resp


def scrape_site(resp):
    html = BeautifulSoup(resp.text)

    mandatory_elements_results = get_mandatory_elements(html)
    product_data_results = get_product_data(html)
    image_address = get_image_address(html)

    result = {"Adres zdjecia": image_address, **mandatory_elements_results, **product_data_results}
    fix_name(result)

    return result


# Raises ScrapingError
def get_mandatory_elements(html):
    elements_text = {
        "Nazwa": "product__header__name",
        "Cena": "product__data__price__regular",
        "Cena przed promocja": "product__data__price__list",    # optional
    }

    results = {}

    for element, class_name in elements_text.items():
        value = get_element_text(html, class_name)

        if value is None or value == "" and element != "Cena przed promocja":
            raise ScrapingError("Mandatory element \'{}\' not found on the site.".format(element))

        results[element] = value

    return results


def get_element_text(html, element_class):
    element_html = html.find(attrs={"class" : element_class})

    if element_html is None:
        return None

    return element_html.getText().strip()


def get_product_data(html):
    # description is not always present
    expected_product_data = set(["Indeks", "Producent", "Płeć", "Opis dodatkowy"])
    mandatory_elements = expected_product_data - set("Opis dodatkowy")

    product_data_class = "product__data__field"
    label_class = "product__data__label"
    content_class = "product__data__content"

    results = {}

    product_data_html = html.findAll(attrs={"class" : product_data_class})

    for element in product_data_html:
        label_text_html = element.find(attrs={"class" : label_class})

        if label_text_html is None:
            continue

        label_text = label_text_html.getText().strip()
        if len(label_text) == 0:
            continue

        label_text = label_text[:-1]                    # remove ':' at the end of the text
        if label_text in expected_product_data:
            value = element.find(attrs={"class" : content_class})

            if value is None:
                continue

            value = value.getText().strip()

            if len(value) == "":
                continue

            results[label_text] = value

    for element in results.keys():
        if element not in mandatory_elements:
            raise ScrapingError("Mandatory element \'{}\' not found on the site.".format(element))

    return results

def get_image_address(html):
    element = html.find("img", {"class": "zoom_item"})

    if element is None:
        raise ScrapingError("Image address not found on the site.")

    return element['src']

# result will be updated
def fix_name(result):
    name = result["Nazwa"]
    name_parts = name.split()

    name_new_start = 0
    name_new_end = len(name_parts)

    if name_parts[-1] == result["Indeks"]:
        name_new_start = 1

    if name_parts[0] == result["Producent"]:
        name_new_end = -1

    result["Nazwa"] = " ".join(name_parts[name_new_start:name_new_end])
