from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from pydantic_core import ValidationError
from settings import Settings
import http
import requests
import logging
import sys


@dataclass
class Response:
    urls: Dict[str, ...]
    headers: Dict[str, ...]
    params: Tuple[Tuple[str, ...], ...]
    data: str
    user_input: str

    def get_info_user(self) -> None:
        """Получение информации о юзере"""
        response = requests.get(self.urls["base_url"], headers=headers)
        logger.info(f"[+] Информация о пользователе: ")
        [print(f" ---  {key}: {val}") for key, val in response.json().items()]

    def get_shorten_link(self) -> Optional[str]:
        """Получение короткой ссылки"""
        response = requests.post(
            self.urls["shorten"], data=self.data.format(user_input), headers=self.headers
        )
        link = response.json().get("link", None)

        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            logger.error(f"[-] Неверная ссылка.")
            return

        elif not link:
            logger.info("[-] Ссылка не была создана. Вероятно вы ввели неверный url.")
            return

        logger.info(f"[+] Битлинк {link}")
        return response.json()["link"][8:]

    def bitlink_counter(self, shorten_link: str, no_count: bool = False) -> None:
        """Счетчик кликов"""
        if no_count:
            shorten_link += "/clicks"

        response = requests.get(
            self.urls["summary_clicks"].format(shorten_link),
            headers=self.headers,
            params=self.params,
        )
        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            logger.error("[-] Что то пошло не так")
            return

        elif response.status_code == http.HTTPStatus.PAYMENT_REQUIRED:
            logger.warning(
                "[!] Обновите учетную запись. Т.е купите расширение. Кол-во просмотров недоступно."
            )
            return

        logger.info("[+] Информация о созданной ссылке: ")
        [print(f" ---  {key}: {val}") for key, val in response.json().items()]

    @staticmethod
    def is_bitlink(user_link: str) -> bool:
        """Проверка ввода пользователя"""
        if user_link.startswith("bit.ly"):
            return True
        return False

    def __call__(self) -> None:
        self.get_info_user()
        if self.is_bitlink(user_input):
            self.bitlink_counter(user_input, no_count=True)
            return

        shorten_link = self.get_shorten_link()
        if not shorten_link:
            return

        self.bitlink_counter(shorten_link)


if __name__ == "__main__":
    logger = logging.getLogger("MyBitLink")
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    try:
        settings = Settings()
    except ValidationError:
        logger.error('Поле "TOKEN" отсутствует в файле .env')
        sys.exit()

    token = settings.TOKEN.get_secret_value()
    user_input: str = input("Введите полное название сайта." "Например: Google.com\n")
    headers: Dict[str, ...] = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    params: Tuple[Tuple[str, ...], ...] = (
        ("unit", "month"),
        ("units", "1"),
        ("unit_reference", "2006-01-02T15:04:05-0700"),
    )
    data: str = '{{"long_url": "https://{}", "domain": "bit.ly"}}'
    urls: Dict[str, ...] = {
        "base_url": "https://api-ssl.bitly.com/v4/user",
        "shorten": "https://api-ssl.bitly.com/v4/shorten",
        "summary_clicks": "https://api-ssl.bitly.com/v4/bitlinks/{}",
    }

    monitor = Response(urls, headers, params, data, user_input)
    monitor()
