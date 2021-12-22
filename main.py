import requests
from bs4 import BeautifulSoup
import json


def get_wokr_list(lng):

    URL = f"https://jobs.dou.ua/vacancies/?category={lng}"
    headers = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"

     }

    req = requests.get(URL, headers=headers)
    src = req.text

    soup = BeautifulSoup(src, "lxml")
    all_work_list = soup.find_all('div', class_="vacancy")

    project_urls = []
    for item in all_work_list:
        salary = item.find("span", class_="salary")
        if salary:
            salary = item.find("span", class_="salary").get_text().replace(u'\xa0', u' ')
        else:
            salary = 'Зарплата не вказана'
        project_urls.append(
            {
            "title": item.find("a", class_="vt", ).get_text(strip=True).replace(u'\xa0', u' '),
            "city": item.find("span", class_="cities").get_text(strip=True),
            "salary": salary,
            "info": item.find("div", class_="sh-info").get_text(strip=True).replace(u'\xa0', u' ').replace('\n', ''),
            "link": item.find("a").get("href")

        }
    )

    with open('work.json', 'w', encoding="utf-8") as json_file:
        json.dump(project_urls, json_file, ensure_ascii=False, indent=4)


def main():
    get_wokr_list()


if __name__ == '__main__':
    main()
