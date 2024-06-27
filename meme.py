import logging
import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from io import BytesIO
from PIL import Image
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname=s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API key and Telegram bot token from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def meme(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a caption or idea for the bee meme.')

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def generate_meme(prompt: str) -> BytesIO:
    try:
        # Add context to the user's input without including text in the final image
        full_prompt = f"A busy bee mining coins using a CPU computer. The bee is doing this in a context where {prompt}. The image should be symbolic and contain no text."

        # Call OpenAI's API to generate the context image
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        data = {
            "model": "image-alpha-001",  # Use the correct model name from OpenAI documentation
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1024"
        }

        logger.info(f"Request payload: {json.dumps(data, indent=2)}")
        response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, data=json.dumps(data))
        response.raise_for_status()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.content}")

        image_url = response.json()['data'][0]['url']
        response_image = Image.open(BytesIO(requests.get(image_url).content))
        
        # Save the generated image to a bytes buffer
        output = BytesIO()
        response_image.save(output, format='PNG')
        output.seek(0)
        return output
    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        logger.error(f"Response content: {e.response.content if e.response else 'No response content'}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def meme_caption(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    caption = update.message.text
    logger.info("Caption from %s: %s", user.first_name, caption)

    # Generate meme
    try:
        meme_image = generate_meme(caption)
        if meme_image:
            # Send the meme back to the user
            await update.message.reply_photo(photo=meme_image)
        else:
            # Inform the user about the error
            await update.message.reply_text("Sorry, there was an error generating your meme. Please try a different caption.")
    except Exception as e:
        logger.error(f"Error generating meme: {e}")
        await update.message.reply_text("Sorry, there was an error generating your meme. Please try a different caption.")

def main() -> None:
    # Check if the API key and token are available
    if not openai_api_key or not TOKEN:
        logger.error("API key or token not found. Make sure to set OPENAI_API_KEY and TELEGRAM_BOT_TOKEN environment variables.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("meme", meme))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, meme_caption))

    application.run_polling()

if __name__ == '__main__':
    main()
