# Gno Plugin Knowledge Scrapper

This is a tool made for extracting content from Gno.land's monorepo's realms and packages. It is made as part of the soultion for registering these in one place, as asked in [this issue](https://github.com/gnolang/gno/issues/3518).

## Features

- Scrapes official [Gno realms and packages](https://github.com/gnolang/gno/tree/master/examples/gno.land/)
- Formats and cleans the extracted content for better readability
- Queries AI model for descriptions of the realms and packages
- Prepares data to be easily parsed

## Purpose

This tool is made to be used as a mapper between the realms and packages in the monorepo and their descriptions.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gno-realm-and-package-scrapper.git
cd gno-realm-and-package-scrapper
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. (Optional) Add your GitHub and OpenAI API keys to `.env` for better rate limits when scraping docs:
```
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your-api-key-here 

```

## Usage

Run any of the following commands using Poetry:

```bash
# Extract realms
poetry run extract_realms

# Extract packages
poetry run extract_packages
```

The extracted content will be saved in the `gno-realm-and-package-scrapper/artifacts` directory, organized by tool.
