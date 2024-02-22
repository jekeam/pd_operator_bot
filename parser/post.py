import re

import httpx
from bs4 import BeautifulSoup

URL = "https://pd.rkn.gov.ru/operators-registry/operators-list/"


async def get_csrftoken():
    global URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token_meta = soup.find("meta", {"name": "csrf-token-value"})

    if csrf_token_meta:
        return csrf_token_meta["content"]
    else:
        raise ValueError("Failed to retrieve csrf-token-value from the page.")


async def make_request(data):
    # Выполнение POST-запроса
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(URL, data=data, headers=headers)

    # Обработка результата
    return response.text


def convert_for_tg(result_table):
    # Extract and format information
    formatted_message = ""
    for num, row in enumerate(result_table.find_all("tr")):
        if num == 0:
            continue

        columns = row.find_all("td")
        if len(columns) == 6:  # Assuming each row has 6 columns
            # Extract data
            register_number = columns[0].get_text(strip=True)

            # Check if the <a> tag exists before accessing its attributes
            operator_name = (
                f'<a href="{URL}{columns[1].find("a").attrs["href"]}">' f"{columns[1].get_text(strip=True)}" f"</a>"
            )

            operator_type = columns[2].get_text(strip=True)
            inclusion_basis = columns[3].get_text(strip=True)
            registration_date = columns[4].get_text(strip=True)
            processing_start_date = columns[5].get_text(strip=True)

            # Format into Telegram-friendly HTML
            formatted_message += f"<b>Регистр. номер</b>\n{register_number}\n\n"
            formatted_message += f"<b>Наименование оператора / ИНН</b>\n{operator_name}\n\n"
            formatted_message += f"<b>Тип оператора</b>\n{operator_type}\n\n"
            formatted_message += f"<b>Основание включения в реестр</b>\n{inclusion_basis}\n\n"
            formatted_message += f"<b>Дата регистрации уведомления</b>\n{registration_date}\n\n"
            formatted_message += f"<b>Дата начала обработки</b>\n{processing_start_date}\n\n"

    return formatted_message


async def post_request_data(inn: str = None, regn: str = None):
    csrftoken = await get_csrftoken()

    request_data = {
        "csrftoken": csrftoken,
        "act": "search",
        "name_full": "",
        "inn": inn if inn else "",
        "regn": regn if regn else "",
    }

    response_text = await make_request(request_data)

    soup = BeautifulSoup(response_text, "html.parser")

    result_table = soup.find("table", {"id": "ResList1"})

    if result_table:
        d = convert_for_tg(result_table)

        if not d:
            return "Записей не найдено"
        return d
    else:
        return "Записей не найдено"


def clean_input(input_text):
    # Keep only digits and hyphens using regular expressions
    return re.sub(r"[^0-9\-]", "", input_text)


def determine_data_type(data):
    # Функция определения типа данных (ИНН или Регн)
    if data.isdigit():
        return "inn"
    elif "-" in data:
        return "regn"


async def main():
    in_text = clean_input("6672153986")  # Или используйте ваш regn, например, "91-17-005023"

    data_type = determine_data_type(in_text)

    if data_type == "inn":
        resp = await post_request_data(inn=in_text)
    else:
        resp = await post_request_data(regn=in_text)

    print(resp)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
