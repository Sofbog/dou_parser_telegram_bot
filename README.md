
# DOU Parser Telegram Bot

## Introduction

This project is a Telegram bot designed to parse and deliver job-related information from the DOU website. It allows users to interact with the bot to receive updates and search for job postings directly through Telegram.

## Installation

To set up this project locally, you'll need Python, pip, and a Telegram bot token. Follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/Sofbog/dou_parser_telegram_bot.git
cd dou_parser_telegram_bot
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory and add your Telegram bot token:

```plaintext
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

## Usage

To run the Telegram bot, execute:

```bash
python bot.py
```

Interact with your bot in Telegram to start receiving DOU job updates.

## Features

- **Job Search**: Users can search for jobs by keywords.
- **Subscription**: Users can subscribe to receive regular updates on new job postings.
- **Custom Alerts**: Set up alerts for specific job titles, companies, or other criteria.

## Contributions

Contributions are welcome! If you have ideas for improvements or encounter any issues, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
