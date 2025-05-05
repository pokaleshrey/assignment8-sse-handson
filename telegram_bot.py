from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from dotenv import load_dotenv
import os
from agent import AgentLoop, MultiMCP
import asyncio
import yaml
import logging

load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

# Create application
application = Application.builder().token(TELEGRAM_API_KEY).build()

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(
        "Hello sir, Welcome to the Bot. Please write /help to see the commands available.") 

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text("""Available Commands:- 
    /start - To start the bot
    /help - To see the available commands
    /agent - To ask a query to the agent""") 

async def agent_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log("info", f"Received query: {update.message.text}")
    final_response = await main(update.message.text)
    await update.message.reply_text(final_response) 

async def main(user_input: str) -> str:
    """Main function to run the agent loop."""
    print("🧠 Cortex-R Agent Ready")
    # user_input = input("🧑 What do you want to solve today? → ")

    # Load MCP server configs from profiles.yaml
    with open("config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers = profile.get("mcp_servers", [])

    multi_mcp = MultiMCP(server_configs=mcp_servers)
    print("Agent before initialize")
    await multi_mcp.initialize()

    agent = AgentLoop(
        user_input=user_input,
        dispatcher=multi_mcp  # now uses dynamic MultiMCP
    )

    try:
        final_response = await agent.run()
        print("\n💡 Final Answer:\n", final_response.replace("FINAL_ANSWER:", "").strip())
        return final_response.replace("FINAL_ANSWER:", "").strip()

    except Exception as e:
        log("fatal", f"Agent failed: {e}")
        raise

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text) 

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(
        "Sorry I can't recognize you , you said '%s'" % update.message.text) 

# Add handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('help', help))
application.add_handler(CommandHandler('agent', agent_query))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
application.add_handler(MessageHandler(filters.COMMAND, unknown))

# Run the bot
if __name__ == '__main__':
    application.run_polling()
