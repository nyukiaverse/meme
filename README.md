
# Telegram Meme Generator Bot

This repository contains a Telegram bot script that generates symbolic memes of a busy bee mining coins using a CPU computer based on user input. The bot uses OpenAI's image generation capabilities to create the memes.

## Features

- Generate symbolic memes without any text.
- Combine user input with a bee template image.
- Uses OpenAI's DALL-E API for image generation.
- Provides feedback to users if their input is rejected or if there is an error.

## Prerequisites

- Ubuntu server (e.g., provided by DigitalOcean)
- Python 3.x
- Telegram bot token
- OpenAI API key
- `git`, `python3`, `python3-pip` installed on the server

## Setup Instructions

### 1. Create and Set Up Your DigitalOcean Droplet

1. Log in to your DigitalOcean account.
2. Create a new Droplet with Ubuntu as the operating system.
3. Note the IP address, username (usually `root`), and password or SSH key for access.

### 2. Access Your Server

Open a terminal on your local machine and run:
```sh
ssh root@your_droplet_ip
```
Replace `your_droplet_ip` with the actual IP address of your Droplet.

### 3. Update Your Server
Update the package lists and upgrade any existing packages:
```sh
apt update
apt upgrade -y
```

### 4. Install Required Packages
Install git, python3, python3-pip, and other necessary packages:
```sh
apt install git python3 python3-pip -y
```

### 5. Clone Your GitHub Repository
Clone your private GitHub repository containing the script:
```sh
git clone https://github.com/your_username/your_repo.git
```
Replace `your_username` and `your_repo` with your GitHub username and repository name. If your repository is private, set up SSH keys or use a personal access token for authentication.

### 6. Navigate to the Script Directory
Change into the directory where the script is located:
```sh
cd your_repo
```

### 7. Install Python Dependencies
Install the required Python libraries:
```sh
pip3 install -r requirements.txt
```
If you don't have a `requirements.txt` file, install the necessary packages individually:
```sh
pip3 install python-telegram-bot openai pillow requests tenacity
```

### 8. Set Environment Variables
Set the environment variables for the OpenAI API key and Telegram bot token. Add these to your shell configuration file (e.g., `.bashrc` or `.bash_profile`) for persistence:
```sh
echo 'export OPENAI_API_KEY="your_openai_api_key"' >> ~/.bashrc
echo 'export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"' >> ~/.bashrc
source ~/.bashrc
```

### 9. Run the Script
Run your Python script:
```sh
python3 your_script.py
```

### 10. Keep the Script Running
To keep the script running even after you log out, use screen or tmux, or set up a systemd service.

**Using screen**

Install screen:
```sh
apt install screen -y
```
Start a new screen session and run the script:
```sh
screen -S meme_bot
python3 your_script.py
```
Detach from the screen session by pressing `Ctrl+A`, then `D`. To reattach to the session:
```sh
screen -r meme_bot
```

**Using systemd**

Create a systemd service file to manage your bot as a service:
```sh
nano /etc/systemd/system/meme_bot.service
```
Add the following content, adjusting paths as necessary:
```ini
[Unit]
Description=Telegram Meme Bot
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/your_repo
ExecStart=/usr/bin/python3 /path/to/your_repo/your_script.py
Environment="OPENAI_API_KEY=your_openai_api_key"
Environment="TELEGRAM_BOT_TOKEN=your_telegram_bot_token"
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```sh
systemctl enable meme_bot
systemctl start meme_bot
```

## Security Considerations

- Store your API keys securely and avoid hardcoding them in your scripts.
- Use environment variables or secrets management tools like AWS Secrets Manager, Azure Key Vault, or Google Cloud Secret Manager.

## Contributing

Feel free to open issues or submit pull requests with improvements or bug fixes. Ensure any contributions adhere to the project's coding standards and include appropriate tests.

## License

This project is licensed under the MIT License.
