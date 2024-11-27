import logging
import logging.handlers
import os
import yaml
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from src.handlers import CommandHandlers
from src.meme_generator import MemeGenerator
from src.database import init_db

def setup_logging():
    """Setup rotating file handler"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        'logs/bot.log',
        maxBytes=1024*1024,
        backupCount=5
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def load_config():
    """Load configuration from YAML file"""
    with open('config/config.yml', 'r') as f:
        return yaml.safe_load(f)

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting bot...")

    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Get environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    api_key = os.getenv('OPENAI_API_KEY')

    if not token or not api_key:
        logger.error("Missing required environment variables")
        return

    # Initialize components
    meme_generator = MemeGenerator(api_key)
    handlers = CommandHandlers(meme_generator)

    # Create application
    application = ApplicationBuilder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("meme", handlers.meme_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("menu", handlers.menu_command))

    # Start the bot
    logger.info("Bot started successfully")
    application.run_polling()

if __name__ == '__main__':
    main() 