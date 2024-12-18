import logging
import os
import subprocess
import json
from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from io import BytesIO
from PIL import Image
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API key and Telegram bot token from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not openai_api_key:
    logger.error("API key not found in environment. Please set OPENAI_API_KEY.")
    exit()

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def generate_meme(prompt: str) -> BytesIO:
    """
    Generate a meme image based on the given prompt using the OpenAI API via a cURL command.
    
    Args:
        prompt (str): The text prompt for generating the meme.

    Returns:
        BytesIO: The generated image in a bytes buffer.
    
    Raises:
        subprocess.CalledProcessError: If an error occurs during the cURL request.
    """
    try:
        # Add context to the user's input without including text in the final image
        full_prompt = f"Create an image featuring a happy and cheeky honey bee with a face resembling Pepe the Frog, wearing cultural attire of {prompt}. The bee is mining green honey-coated hexagonal coins using a CPU computer that looks like a hexagonal box. The scene is set in a picturesque and modern environment in {prompt}. The overall mood of the image should be lively and playful, capturing the humorous and symbolic nature of the meme. Ensure the image contains no text at all."

        # Log the full prompt for debugging
        logger.debug(f"Full prompt: {full_prompt}")

        # JSON data for the API request
        data = json.dumps({
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "hd",
            "response_format": "url"
        })

        # Constructing the cURL command for the API request
        curl_command = [
            "curl", "-X", "POST", "https://api.openai.com/v1/images/generations",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {openai_api_key}",
            "-d", data
        ]

        # Executing the cURL command and capturing the response
        response = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        response_data = json.loads(response.stdout)

        # Log the response for debugging
        logger.debug(f"OpenAI API response: {response_data}")

        # Check for the 'data' key in the response
        if 'data' not in response_data:
            logger.error(f"API response does not contain 'data' key: {response_data}")
            if 'error' in response_data and response_data['error']['code'] == 'billing_hard_limit_reached':
                raise RuntimeError("Billing limit reached. Cannot generate more images.")
            raise KeyError("'data' key not found in the API response")

        # Extract the URL of the generated image from the response
        image_url = response_data['data'][0]['url']

        # Download the generated image
        response_image = Image.open(BytesIO(requests.get(image_url).content))

        # Save the generated image to a bytes buffer
        output = BytesIO()
        response_image.save(output, format='PNG')
        output.seek(0)
        return output
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred during cURL request: {e}")
        raise
    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        if e.response:
            logger.error(f"Response content: {e.response.content.decode()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def meme_command(update: Update, context: CallbackContext) -> None:
    """Handle the /meme command by generating a meme based on the user's location input."""
    user = update.message.from_user
    chat_type = update.message.chat.type

    if chat_type in [Chat.GROUP, Chat.SUPERGROUP]:
        # Ensure bot is mentioned in group commands
        if not context.bot.username in update.message.text:
            return

    try:
        # Get the location from the command
        location = ' '.join(context.args)
        if not location:
            await update.message.reply_text("Please provide a country, county, city, or village after the /meme command.")
            return

        logger.info("Location from %s: %s", user.first_name, location)

        # Generate meme
        meme_image = generate_meme(location)
        if meme_image:
            # Send the meme back to the user with additional text
            await update.message.reply_photo(photo=meme_image)
            await update.message.reply_text("Earn $WHIVE Coins here; http://Nyukia.AI")
        else:
            # Inform the user about the error
            await update.message.reply_text("Sorry, there was an error generating your meme. Please try a different location.")
    except RuntimeError as e:
        if str(e) == "Billing limit reached. Cannot generate more images.":
            await update.message.reply_text("Sorry, the billing limit for image generation has been reached. Please try again later.")
        else:
            logger.error(f"Runtime error: {e}")
            await update.message.reply_text("Sorry, there was an error generating your meme. Please try a different location.")
    except Exception as e:
        logger.error(f"Error generating meme: {e}")
        await update.message.reply_text("Sorry, there was an error generating your meme. Please try a different location.")

def main() -> None:
    """Main function to run the Telegram bot."""
    # Check if the API key and token are available
    if not openai_api_key or not TOKEN:
        logger.error("API key or token not found. Make sure to set OPENAI_API_KEY and TELEGRAM_BOT_TOKEN environment variables.")
        return

    # Create the Telegram bot application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers for the bot commands and messages
    application.add_handler(CommandHandler("meme", meme_command))

    # Start the bot and run it until manually stopped
    application.run_polling()

if __name__ == '__main__':
    main()
