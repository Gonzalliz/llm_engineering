import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.markdown import Markdown
from openai_util import OpenAIUtils
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebPageSummarizer:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url

    def scrape_website(self, response):
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
            return [self.title, self.text]
        except Exception as e:
            logger.error(f"An error occurred while scraping the website: {e}")
            return None

    def send_request(self, url, headers):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
        return response

    def create_user_prompt(self, title, text):
        user_prompt = f"You are looking at a website titled {title}"
        user_prompt += "\nThe contents of this website is as follows; \
                    please provide a short summary of this website in markdown. \
                    If it includes news or announcements, then summarize these too.\n\n"
        user_prompt += text
        return user_prompt

    def create_system_prompt(self):
        system_prompt = "You are an assistant that analyzes the contents of a website \
            and provides a short summary, ignoring text that might be navigation related. \
            Respond in markdown."
        return system_prompt

    def summarize(self):
        # Some websites need you to use proper headers when fetching them:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        response = self.send_request(self.url, headers)
        if response is None:
            raise ValueError("Failed to fetch the webpage.")

        website_data = self.scrape_website(response)
        if website_data is None:
            raise ValueError("Failed to scrape the webpage.")

        user_prompt = self.create_user_prompt(website_data[0], website_data[1])
        system_prompt = self.create_system_prompt()

        # calls openAI to summarize the text
        openai_util = OpenAIUtils()
        return openai_util.summarize_text(system_prompt, user_prompt, model="gpt-4o-mini")

    # Fetches the summary of the given URL and displays it in markdown format.
    def display_summary(self):
        try:
            summary = self.summarize()
            if summary is None:
                raise ValueError("Failed to summarize the webpage.")
            console = Console()
            md = Markdown(summary)
            console.print(md)
        except Exception as e:
            logger.error(f"An error occurred while summarizing the webpage using openAI: {e}")
            return
