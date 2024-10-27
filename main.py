import aiohttp
from bs4 import BeautifulSoup
import json


async def get_wokr_list(lng):
    URL = f"https://jobs.dou.ua/vacancies/?category={lng}"
    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(URL, headers=headers) as resp:
            if resp.status == 200:
                src = await resp.text()
                soup = BeautifulSoup(src, "lxml")
                all_work_list = soup.find_all('li', class_="l-vacancy")

                project_urls = []
                for item in all_work_list:
                    # Extract job details with safe checks
                    title = item.find("a", class_="vt").get_text(strip=True).replace(u'\xa0', u' ')
                    link = item.find("a", class_="vt").get("href")

                    # Safe check for 'city' field
                    city_element = item.find("span", class_="cities")
                    city = city_element.get_text(strip=True) if city_element else "Місто не вказано"

                    # Safe check for 'salary' field
                    salary_element = item.find("span", class_="salary")
                    salary = salary_element.get_text(strip=True).replace(u'\xa0', u' ') if salary_element else 'Зарплата не вказана'

                    # Safe check for 'info' field
                    info_element = item.find("div", class_="sh-info")
                    info = info_element.get_text(strip=True).replace(u'\xa0', u' ').replace('\n', '') if info_element else "Інформація не вказана"

                    # Append job details to the list
                    project_urls.append({
                        "title": title,
                        "city": city,
                        "salary": salary,
                        "info": info,
                        "link": link
                    })

                # Write job listings to JSON file
                with open('work.json', 'w', encoding="utf-8") as json_file:
                    json.dump(project_urls, json_file, ensure_ascii=False, indent=4)
                print("Data saved to work.json")
            else:
                print(f"Failed to retrieve data: Status code {resp.status}")

# Test function with asyncio
# asyncio.run(get_wokr_list('python'))
