import logging
import os
import subprocess
import json
import random
from telegram import Update, Chat, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from io import BytesIO
from PIL import Image
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import asyncio

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API key and Telegram bot token from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not openai_api_key:
    logger.error("API key not found in environment. Please set OPENAI_API_KEY.")
    exit()

# List of slogans and meme ideas
slogans_and_ideas = [
    ("Bee the Change. Power the World.", "A bee holding a miniature solar panel, with a background of CPUs mining in the hive."),
    ("Hive Together, Thrive Together.", "Bees forming a chain, representing a blockchain, with smiling faces as they connect to each other."),
    ("Buzzing Towards a Greener Future.", "A bee flying towards a sun, with solar panels beneath and energy lines connecting the world."),
    ("Small Buzz, Big Impact.", "A small bee with a huge lightning bolt, symbolizing that CPU mining with Whive has a big environmental impact."),
    ("Proof of Work, Proof of Honey.", "A bee dressed as a miner with coins that look like honey dripping, symbolizing mining rewards."),
    ("Let Your CPU Bee Part of the Swarm.", "A bee sitting on a laptop with a 'Join the Hive' button on screen, showing CPU mining activity."),
    ("The Hive is Stronger When We Buzz Together.", "Multiple bees with mining hats working together to build a stronger hive, showcasing network collaboration."),
    ("CPU Power, Green Future.", "A bee plugging a CPU into a tree, with energy flowing from the tree into the hive."),
    ("Empower the Hive, Harvest the Future.", "Bees collecting honey while solar panels charge the hive, emphasizing energy harvesting."),
    ("Sustainable Rewards, Sweet as Honey.", "Bees flying with honey jars filled with digital rewards, showing that renewable energy rewards are sweet."),
    ("Bee Smart. Bee Renewable.", "A bee holding a lightbulb above a field of solar panels, showcasing innovation in renewable energy."),
    ("From Hive to Hive, Decentralized Energy for All.", "Bees flying between hives exchanging energy, symbolizing peer-to-peer decentralized energy trading."),
    ("Power Up Your Hive, One CPU at a Time.", "A bee installing a CPU into a hive, powering it up like a battery."),
    ("Buzz Around the World with Green Energy.", "Bees carrying a globe with solar panels covering it, representing sustainable energy."),
    ("Bee Efficient, Bee Rewarded.", "A bee mining with a pickaxe, surrounded by honeycombs that represent block rewards."),
    ("Mining for a Better Buzz.", "A bee miner with a smile, holding a chunk of honey labeled 'Green Rewards.'"),
    ("The Buzzing Network of Sustainable Growth.", "Bees flying around a blockchain, leaving behind flowers that bloom, showing sustainable growth."),
    ("Bee the Proof-of-Work in a Sustainable World.", "A bee holding up a 'Proof of Work' sign above a lush field, symbolizing energy-efficient mining."),
    ("Buzz Responsibly, Mine Sustainably.", "A bee miner next to solar panels, emphasizing environmentally friendly mining."),
    ("Hive Mind for Renewable Energy.", "A group of bees in a conference room, planning how to implement solar energy."),
    ("Buzzing Past ASICs to Bring Power to the People.", "A bee zooming past large mining machines labeled 'ASICs,' reaching the people instead."),
    ("Buzz Lightyear! From Solar to Blockchain!", "A bee dressed as Buzz Lightyear flying into the blockchain with a solar panel backpack."),
    ("Be the Buzz, Energize the Future.", "A bee buzzing around a battery icon, slowly filling it up with energy."),
    ("Hive with Us. Change the Future.", "A bee inviting others into a hive, which has a banner reading 'Welcome to the Future.'"),
    ("Green Energy? We've Got the Buzz for It!", "Bees working in a hive full of green leaves, symbolizing green energy and sustainability."),
    ("Buzz Where It's Needed – CPU Mining for All!", "A bee on a laptop, flying across a world map to represent decentralizing mining to all locations."),
    ("Hive Together, Win Together!", "Bees exchanging honey jars labeled 'Rewards,' showcasing the idea of collective benefits."),
    ("Proof of Honey, Powered by Green Energy.", "Bees producing honey in a field of solar panels, emphasizing proof-of-work tied to renewable energy."),
    ("Sweet Rewards for Green Energy Pioneers.", "A bee presenting a golden honey jar to another bee with a 'Pioneer' badge."),
    ("Bee a Pioneer, Buzz Sustainably.", "A bee explorer planting a flag that reads 'Green Energy Champion.'"),
    ("Bee Renewable, Bee Rewarded.", "A bee flying in circles around solar panels while receiving digital honey rewards."),
    ("The Hive Network Buzzing with Energy.", "A network of bees connecting their hives with electric cables representing blockchain nodes."),
    ("One Hive, One Mission – Sustainability.", "Bees carrying signs reading 'Green Future' and 'Sustainable Mining' marching together."),
    ("Hive Hard, Earn Sweet.", "A bee miner with a honeycomb backpack labeled 'Sweet Rewards,' mining on solar power."),
    ("Buzz Beyond Borders – Global Mining.", "A bee flying over a globe with countries lighting up, symbolizing the global nature of mining."),
    ("Let’s Hive to Survive.", "Bees flying with determination towards renewable energy sources to protect their hive."),
    ("Green Energy, Golden Rewards.", "A bee turning sunlight into golden honey coins, symbolizing green rewards for clean energy."),
    ("Hive Smart, Buzz Efficient.", "A bee using a laptop, generating a honeycomb full of coins, symbolizing intelligent and efficient mining."),
    ("Buzzin' Beyond ASICs – Join the Hive!", "A bee with crossed-out ASIC mining machines, showing a preference for CPU mining."),
    ("For the Planet, For the Buzz.", "Bees planting trees, with coins floating above them, representing benefits for both the hive and the planet."),
    ("Buzz Together for a Brighter Tomorrow.", "A field full of solar-powered bee hives, with rays of sunlight shining down on them."),
    ("Mining Made for Every Bee.", "Bees in different outfits (worker bee, student bee, etc.) mining with laptops, showing inclusivity."),
    ("Swarm the Future with Renewable Buzz.", "A swarm of bees flying towards a glowing future, representing a transition to sustainable energy."),
    ("Decentralized Mining – Let It Bee.", "A bee with mining gear pointing to the blockchain hive and saying 'Let it bee.'"),
    ("Renewable Energy? It’s the Bees Knees!", "A bee showing its knees while solar panels are connected to the hive, emphasizing energy."),
    ("Buzz Power, Not Fossil Power.", "Bees turning away from an oil pumpjack towards a field of solar panels."),
    ("Hive Now for a Sustainable Future.", "Bees building a hive with green leaves growing on it, representing future sustainability."),
    ("Bee the Miner the World Needs.", "A heroic-looking bee holding a CPU chip like a superhero, symbolizing energy-efficient mining."),
    ("We Bee-Lieve in Sustainable Mining.", "A group of bees cheering with a banner saying 'Sustainable Mining Rocks.'"),
    ("CPU Power is Bee Power!", "A bee holding a CPU chip, with energy radiating towards a hive."),
    ("Hive On, Shine On.", "Bees in a solar-powered hive with a sun shining above, representing the power of renewable energy."),
    ("Join the Hive, Earn the Buzz.", "A bee buzzing in a circle with coins, inviting others to join in for rewards."),
    ("Sustainable Mining is the Bees’ Buzz.", "Bees having a meeting and discussing how to keep mining sustainable."),
    ("Buzzing with Green Energy Rewards.", "A bee flying with honey pots labeled 'Green Rewards,' showing how sustainable mining pays off."),
    ("Buzz Light, Mine Right.", "Bees mining with solar-powered tools under the sunlight, showcasing responsible mining."),
    ("Together We Thrive, Together We Hive.", "Bees working in harmony, building a giant hive, representing a collaborative effort."),
    ("Power the Buzz, Protect the Hive.", "A bee guarding the hive while other bees generate power using CPUs, symbolizing community protection."),
    ("Bee Green, Bee Strong.", "Bees using renewable energy to strengthen their hive, showcasing a collective effort."),
    ("CPU Mining – Buzz for the Future.", "A bee flying through a futuristic landscape full of solar panels, representing mining for the future.")
]

# List of random capital cities
capital_cities = [
    "Nairobi", "Tokyo", "Paris", "London", "Berlin", "Brasília", "Canberra", "Ottawa", "Washington D.C.", "Beijing",
    "Moscow", "Cairo", "Buenos Aires", "New Delhi", "Rome", "Madrid", "Seoul", "Bangkok", "Jakarta", "Pretoria",
    "Helsinki", "Oslo", "Stockholm", "Lisbon", "Vienna", "Bern", "Amsterdam", "Brussels", "Dublin", "Warsaw",
    "Athens", "Havana", "Kingston", "Kigali", "Baghdad", "Tehran", "Riyadh", "Hanoi", "Manila", "Santiago",
    "Lima", "Bogotá", "Caracas", "Quito", "San José", "Panama City", "Port-au-Prince", "Kingstown", "Castries", "Nassau",
    "Georgetown", "Paramaribo", "Port of Spain", "Bridgetown", "Belmopan", "Suva", "Apia", "Wellington", "Yamoussoukro",
    "Ouagadougou", "Bamako", "Accra", "Conakry", "Freetown", "Monrovia", "Dakar", "Bissau", "Mogadishu", "Addis Ababa",
    "Asmara", "Juba", "Khartoum", "Rabat", "Algiers", "Tripoli", "Tunis", "Nouakchott", "Niamey", "Ndjamena", "Lusaka",
    "Harare", "Gaborone", "Windhoek", "Lilongwe", "Maputo", "Kampala", "Dodoma", "Antananarivo", "Victoria", "Port Louis",
    "Male", "Colombo", "Islamabad", "Kabul", "Kathmandu", "Thimphu", "Dhaka", "Bandar Seri Begawan", "Kuala Lumpur", "Singapore",
    "Rangoon", "Vientiane", "Phnom Penh", "Ulaanbaatar", "Bishkek", "Tashkent", "Dushanbe", "Ashgabat", "Astana", "Baku",
    "Yerevan", "Tbilisi", "Nicosia", "Valletta", "San Marino", "Vaduz", "Luxembourg", "Monaco", "Andorra la Vella",
    "Reykjavik", "Port Moresby", "Majuro", "Tarawa", "Ngerulmud", "Honiara", "Palikir", "Funafuti", "Nouméa", "Port Vila",
    "Pago Pago", "Saipan", "Melekeok", "Dili", "Moroni", "Djibouti", "Libreville", "Brazzaville", "Kinshasa", "Malabo",
    "Bangui", "Yaoundé", "Abuja", "Cotonou", "Lomé", "Porto-Novo", "Luanda", "Moroni", "Malé", "Vatican City", "Bratislava"
]

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def generate_meme(slogan: str, meme_idea: str) -> BytesIO:
    """
    Generate a meme image based on the given slogan and meme idea using the OpenAI API via a cURL command.
    
    Args:
        slogan (str): The slogan for the meme.
        meme_idea (str): The description for the meme.

    Returns:
        BytesIO: The generated image in a bytes buffer.
    
    Raises:
        subprocess.CalledProcessError: If an error occurs during the cURL request.
    """
    try:
        # Combine the slogan and meme idea to create the full prompt
        full_prompt = f"{slogan}\n{meme_idea}"

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
    """Handle the /meme command by generating a meme based on a random slogan and meme idea."""
    user = update.message.from_user
    username = user.username if user.username else user.first_name
    chat_type = update.message.chat.type

    if chat_type in [Chat.GROUP, Chat.SUPERGROUP]:
        # Ensure bot is mentioned in group commands
        if not context.bot.username in update.message.text:
            return

    try:
        # Randomly select a slogan, meme idea, and a capital city
        slogan, meme_idea = random.choice(slogans_and_ideas)
        capital_city = random.choice(capital_cities)

        # Append the capital city to the meme idea
        meme_idea_with_city = f"{meme_idea} The scene is set in {capital_city}."

        logger.info("Generating meme for user %s with slogan: '%s' and meme idea: '%s'", username, slogan, meme_idea_with_city)

        # Generate meme
        meme_image = generate_meme(slogan, meme_idea_with_city)
        if meme_image:
            # Send the meme back to the user with additional text
            caption = f"{slogan}\nEarn $WHIVE - http://nyukia.ai 💸"
            await update.message.reply_photo(photo=meme_image)
            await update.message.reply_text(caption)
        else:
            # Inform the user about the error
            await update.message.reply_text("Sorry, there was an error generating your meme. Please try again later.")
    except RuntimeError as e:
        if str(e) == "Billing limit reached. Cannot generate more images.":
            await update.message.reply_text("Sorry, the billing limit for image generation has been reached. Please try again later.")
        else:
            logger.error(f"Runtime error: {e}")
            await update.message.reply_text("Sorry, there was an error generating your meme. Please try again later.")
    except Exception as e:
        logger.error(f"Error generating meme: {e}")
        await update.message.reply_text("Sorry, there was an error generating your meme. Please try again later.")

async def welcome_new_member(update: Update, context: CallbackContext) -> None:
    """Welcome new members to the group and ask for their location."""
    for member in update.message.new_chat_members:
        username = member.username if member.username else member.first_name
        welcome_message = f"Welcome {username}! Type /meme to get a custom meme."
        message = await update.message.reply_text(welcome_message)

        # Wait for 15 seconds and then delete the message if no response
        await asyncio.sleep(15)
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

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
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Start the bot and run it until manually stopped
    application.run_polling()

if __name__ == '__main__':
    main()
