import logging
import os
import pdfplumber
import re
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

BOT_TOKEN = os.getenv("8081119332:AAFdVuY8pPdkcLt54jn7L8jT-nSsfhoD_2s")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📎 Send me a *rate confirmation PDF*, and I'll extract the load info.", parse_mode="Markdown")

def parse_rate_confirmation(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(page.extract_text() for page in pdf.pages)

        data = {
            "Carrier Name": re.search(r'Carrier Name\s+(.*?)\s', full_text).group(1),
            "Driver Name": re.search(r'Driver Name\s+(.*?)\s', full_text).group(1),
            "Carrier Pay": re.search(r'Carrier Pay\s+\$(\d+(?:,\d{3})*(?:\.\d{2}))', full_text).group(1),
            "Pickup": re.search(r'PRECOAT METALS\n(.*?)\n(.*?)\n', full_text),
            "Delivery": re.search(r'CARLISLE ARCHITECTURAL METALS\n(.*?)\n(.*?)\n', full_text),
            "ACE Order #": re.search(r'Ace Order #:\s*\n\s*(\d+)', full_text).group(1)
        }

        message = (
            f"🚚 *Rate Confirmation Info:*\n"
            f"Carrier: {data['Carrier Name']}\n"
            f"Driver: {data['Driver Name']}\n"
            f"Carrier Pay: ${data['Carrier Pay']}\n\n"
            f"📦 *Pickup:* PRECOAT METALS\n{data['Pickup'].group(1)}, {data['Pickup'].group(2)}\n\n"
            f"📦 *Delivery:* CARLISLE ARCHITECTURAL METALS\n{data['Delivery'].group(1)}, {data['Delivery'].group(2)}\n\n"
            f"📄 ACE Order #: {data['ACE Order #']}"
        )
        return message
    except Exception as e:
        return f"⚠️ Failed to parse the PDF. Error: {str(e)}"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file.mime_type == "application/pdf":
        await update.message.reply_text("❌ Please send a valid PDF file.")
        return

    file_path = f"/tmp/{file.file_name}"
    await file.get_file().download_to_drive(file_path)
    await update.message.reply_text("📄 Processing your file...")

    result = parse_rate_confirmation(file_path)
    await update.message.reply_text(result, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
