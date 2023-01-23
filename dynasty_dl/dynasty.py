import os
import re
import requests
from requests.adapters import (
    HTTPAdapter,
    Retry,
)
import time
import json
import urllib.parse
from typing import Iterator
import bs4
import tqdm


class Dynasty:
    BASE_URL = "https://dynasty-scans.com/"
    DELAY = 0.5
    PAGES = re.compile("var pages = (.*);")
    FILENAME_LENGTH = 3

    def __init__(self) -> None:
        """Setup session."""
        session = requests.Session()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://dynasty-scans.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        session.headers.update(headers)
        retries = Retry(
            status_forcelist=[403, 429, 500, 502, 503, 504],
            total=5,
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session

    def get(self, url, **kwargs) -> requests.Response:
        time.sleep(self.DELAY)
        return self.session.get(url, **kwargs)

    def get_image_links(self, chapter_url: str) -> Iterator[str]:
        """Get full image urls for single chapter.
        """
        res = self.get(chapter_url)
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        page_script = soup.select("body script")[0]
        page_match = self.PAGES.search(page_script.text)
        for item in json.loads(page_match.group(1)):
            yield urllib.parse.urljoin(self.BASE_URL, item.get('image'))

    def download_series(self, url: str, directory: str) -> None:
        res = self.get(url)
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        try:
            title_elem = soup.find("h2", {"class": "tag-title"})
            title = title_elem.b.text
        except Exception:
            title = url.rstrip('/').split('/')[-1]
        print(f"Getting: {title}")

        chapter_list = soup.find("dl", {"class": "chapter-list"})
        chapter_links = [c for c in chapter_list.find_all("a", {"class": "name"}) if c.get('href')]

        for chapter_no, chapter_link in enumerate(chapter_links):
            print(f"{chapter_no+1}/{len(chapter_links)}: {chapter_link.text}")
            chapter_url = urllib.parse.urljoin(self.BASE_URL, chapter_link.get('href'))
            chapter_directory = os.path.join(
                directory,
                title,
                str(chapter_no).zfill(self.FILENAME_LENGTH),
            )
            self.download_chapter(chapter_url, chapter_directory)

    def download_chapter(self, url: str, directory: str) -> None:
        image_links = list(self.get_image_links(url))
        for idx, image_link in enumerate(tqdm.tqdm(image_links)):
            image_filename_from_url = image_link.split("/")[-1]
            ext = os.path.splitext(image_filename_from_url)[1]
            output_filename = os.path.join(directory, str(idx).zfill(self.FILENAME_LENGTH)+ext)
            if os.path.isfile(output_filename):
                continue
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            image = self.get(image_link)
            with open(output_filename, 'wb') as f:
                f.write(image.content)
