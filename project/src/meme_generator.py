 import logging
from io import BytesIO
from PIL import Image
import requests
import json
import subprocess
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential
import os

logger = logging.getLogger(__name__)

class MemeGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    @lru_cache(maxsize=100)
    def generate_meme(self, slogan: str, meme_idea: str, quality: str = "standard") -> BytesIO:
        """Generate a meme image using DALL-E"""
        try:
            full_prompt = f"{slogan}\n{meme_idea}"
            logger.debug(f"Generating meme with prompt: {full_prompt}")

            data = json.dumps({
                "model": "dall-e-3",
                "prompt": full_prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": quality,
                "response_format": "url"
            })

            curl_command = [
                "curl", "-X", "POST", "https://api.openai.com/v1/images/generations",
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {self.api_key}",
                "-d", data
            ]

            response = subprocess.run(curl_command, capture_output=True, text=True, check=True)
            response_data = json.loads(response.stdout)

            if 'data' not in response_data:
                logger.error(f"API error: {response_data}")
                return None

            image_url = response_data['data'][0]['url']
            img_response = requests.get(image_url)
            img_response.raise_for_status()

            output = BytesIO()
            image = Image.open(BytesIO(img_response.content))
            image.save(output, format='PNG')
            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Meme generation error: {e}")
            return None