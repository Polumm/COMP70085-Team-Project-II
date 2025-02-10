import os
import platform
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig
from pydantic import SecretStr

# Load API Key securely from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "API Key is missing. Set GOOGLE_API_KEY in your .env file."
    )

# Detect if running in WSL
is_wsl = (
    platform.system() == "Linux" and "microsoft" in platform.uname().release
)

# Set Chrome path correctly for WSL or Windows (If you use Mac, please ask gpt and find another way)
if is_wsl:
    chrome_path = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
else:
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

# Ensure the Chrome executable exists
if not Path(chrome_path).exists():
    raise ValueError(f"Chrome executable not found at: {chrome_path}")

# Initialize the LLM model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    api_key=SecretStr(GOOGLE_API_KEY),
)

# ✅ Use the correct way to connect to Windows Chrome from WSL
browser = Browser(
    config=BrowserConfig(
        chrome_instance_path=chrome_path  # ✅ Correct way to specify Chrome path
    )
)


# Define the async function to run the agent
async def run_agent():
    try:
        agent = Agent(
            task="Find flights on kayak.com from Zurich to Beijing.",
            llm=llm,
            browser=browser,
            use_vision=True,
            save_conversation_path="logs/conversation.json",
            planner_interval=3,
        )

        # Run the agent and capture execution history
        history = await agent.run()

        # Extract data
        extracted_content = (
            "\n".join(history.extracted_content())
            or "No extracted content found."
        )
        visited_urls = "\n".join(history.urls()) or "No visited URLs found."
        errors = "\n".join(history.errors()) or "No errors encountered."

        # Save extracted content to a file
        with open("scraped_results.txt", "w", encoding="utf-8") as file:
            file.write(extracted_content)
        print("✅ Extracted content saved to scraped_results.txt")

        # Save visited URLs to a file
        with open("visited_urls.txt", "w", encoding="utf-8") as file:
            file.write(visited_urls)
        print("✅ Visited URLs saved to visited_urls.txt")

        # Save errors (if any) to a file
        if history.errors():
            with open("errors_log.txt", "w", encoding="utf-8") as file:
                file.write(errors)
            print("⚠️ Errors encountered! Check errors_log.txt")
        else:
            print("✅ No errors encountered.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        with open("errors_log.txt", "w", encoding="utf-8") as file:
            file.write(str(e))

    finally:
        input("Press Enter to close the browser...")
        await browser.close()


# Execute the agent
if __name__ == "__main__":
    asyncio.run(run_agent())
