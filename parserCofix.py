import requests
import json
from html.parser import HTMLParser


class Parser(HTMLParser):
    html = []
    ul = False
    place = False
    timeWork = False
    phone = False

    def handle_starttag(self, tag, attrs):
        try:
            if tag == 'ul' and attrs[0][1] == 'table-cafe-list':
                self.timeWork = True
                self.html.append('<ul id=table-cafe-list>')
            elif self.timeWork:
                string = f'<{tag} '
                atrs = []
                for attr in attrs:
                    atrs.append(attr[0] + '=' + attr[1])
                string += f'{"".join(atrs)}>'
                self.html.append(string)
        except IndexError:
            pass

    def handle_data(self, data):
        if self.timeWork:
            self.html.append(data)

    def handle_endtag(self, tag):
        if self.timeWork:
            self.html.append(f'</{tag}>')
        if self.timeWork and tag == 'ul':
            self.timeWork = False


class ParserToJSON(HTMLParser):
    cafeList = []
    match = {}
    parseAddress, address = False, []
    parseMetaData, metaData = False, []

    def handle_starttag(self, tag, attrs):
        try:
            for attr in attrs:
                if attr[0] == 'id' and tag == 'li' and 'list' in attr[1]:
                    self.match['id'] = attr[1]
                if attr[0] == 'class' and attr[1] == 'table-txt' and tag == 'div':
                    self.parseAddress = True
                if attr[0] == 'class' and attr[1] == 'table-txt2' and tag =='div':
                    self.parseMetaData = True
        except Exception:
            ...

    def handle_data(self, data):
        if self.parseAddress:
            self.address.append(data.strip())
        if self.parseMetaData:
            self.metaData.append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'div' and self.parseAddress:
            self.parseAddress = False
            self.match['Address'] = ' '.join(self.address)
            self.address.clear()
        if tag == 'div' and self.parseMetaData:
            self.parseMetaData = False
            self.match['MetaData'] = ' '.join(self.metaData)
            self.metaData.clear()
        if tag == 'li' and self.match:
            self.cafeList.append(self.match.copy())
            self.match.clear()


def geoCoder(address):
    params = {'q': address,
              'apikey': '5032f91e8da6431d8605-f9c0c9a00357'}
    response = requests.get('http://search.maps.sputnik.ru/search/addr?',
                            params=params)
    return response.json()


def correctJSON(jsonlist):
    answer = []  # Итоговые данные
    for elem in jsonlist:

        geocode = geoCoder(elem['Address'])

        phone = elem['MetaData']
        coords = geocode['result']['address'][0]['features'][0]['geometry']['geometries'][0]['coordinates']

        elem['lat'] = coords[1]
        elem['lon'] = coords[0]
        elem['Address'] = geocode['typo']['OriginalQuery'].strip()
        cut = phone.find('Телефон:') + 8
        elem['MetaData'] = phone[cut:].strip()
        answer.append(elem)
    return answer


if __name__ == '__main__':
    parser = Parser()
    jsonparser = ParserToJSON()
    parser.feed(requests.get('https://spb.cofix.ru/cafe/').text)
    jsonparser.feed(' '.join(parser.html))

    with open('cafelist.json', mode='w', encoding='utf8') as file:
        json.dump(correctJSON(jsonparser.cafeList),
                  file, ensure_ascii=False)
