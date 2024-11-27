from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
import random
from .analytics import stats
from .database import log_meme_generation
from .meme_generator import MemeGenerator

logger = logging.getLogger(__name__)

# Store user cooldowns
user_cooldowns = {}
COOLDOWN_MINUTES = 5

class CommandHandlers:
    def __init__(self, meme_generator: MemeGenerator):
        self.meme_generator = meme_generator

    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        if user_id in user_cooldowns:
            last_use = user_cooldowns[user_id]
            if datetime.now() - last_use < timedelta(minutes=COOLDOWN_MINUTES):
                return False
        user_cooldowns[user_id] = datetime.now()
        return True

    async def meme_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /meme command"""
        user_id = update.effective_user.id
        
        if not await self.check_rate_limit(user_id):
            await update.message.reply_text(
                f"Please wait {COOLDOWN_MINUTES} minutes between meme generations!"
            )
            return

        status_message = await update.message.reply_text("🐝 Generating your meme... Please wait!")
        
        try:
            # Get quality setting from command args
            quality = "standard"
            if context.args and context.args[0] in ["hd", "standard"]:
                quality = context.args[0]

            # Generate meme
            slogan, meme_idea = random.choice(SLOGANS_AND_IDEAS)
            meme_image = self.meme_generator.generate_meme(slogan, meme_idea, quality)

            if meme_image:
                caption = f"{slogan}\nEarn $WHIVE - http://nyukia.ai 💸"
                await update.message.reply_photo(photo=meme_image)
                await update.message.reply_text(caption)
                
                # Track success
                stats.track_usage(user_id, True)
                log_meme_generation(user_id, slogan, True)
            else:
                await update.message.reply_text("Sorry, failed to generate meme. Please try again.")
                stats.track_usage(user_id, False)
                log_meme_generation(user_id, slogan, False)

        except Exception as e:
            logger.error(f"Error in meme command: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again later.")
            stats.track_usage(user_id, False)
        finally:
            await status_message.delete()

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show bot statistics"""
        await update.message.reply_text(
            f"📊 Bot Statistics:\n"
            f"Total Memes: {stats.total_memes}\n"
            f"Success Rate: {stats.success_rate:.1f}%\n"
            f"Unique Users: {len(stats.unique_users)}"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message"""
        await update.message.reply_text(
            "🐝 Available Commands:\n"
            "/meme - Generate a bee meme\n"
            "/meme hd - Generate a high-quality meme\n"
            "/stats - View bot statistics\n"
            "/help - Show this message\n"
            "/menu - Show interactive menu"
        )

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show interactive menu"""
        keyboard = [
            [InlineKeyboardButton("Generate Meme", callback_data='generate')],
            [InlineKeyboardButton("Generate HD Meme", callback_data='generate_hd')],
            [InlineKeyboardButton("View Stats", callback_data='stats')],
            [InlineKeyboardButton("Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Choose an option:', reply_markup=reply_markup) 