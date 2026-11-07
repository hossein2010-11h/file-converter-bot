import os
import asyncio
import tempfile
import traceback
import subprocess
from pdf2docx import Converter
from pypdf import PdfReader
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


TOKEN = os.getenv("BOT_TOKEN")


# PDF to Word
def convert_pdf_to_word(pdf_path, docx_path):
    cv = Converter(pdf_path)

    try:
        cv.convert(docx_path)
    finally:
        cv.close()


def convert_word_to_pdf(docx_path, pdf_path):
    output_dir = os.path.dirname(os.path.abspath(pdf_path))

    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            os.path.abspath(docx_path)
        ],
        check=True,
        capture_output=True,
        text=True
    )

    generated_pdf = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    )

    os.replace(generated_pdf, pdf_path)

def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or""


return text

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to File Converter Bot!\n\n"
        "📁 Send me a PDF or Word file.\n\n"
        "⚡️ Fast and easy file conversion!"
    )


# Receive and convert files
async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = update.message.document
    filename = (file.file_name or "").lower()

    if filename.endswith(".pdf"):
        input_name = "input.pdf"
        output_name = "converted.docx"
        output_type = "docx"

    elif filename.endswith(".docx"):
        input_name = "input.docx"
        output_name = "converted.pdf"
        output_type = "pdf"

    else:
        await update.message.reply_text(
            "❌ Please send a PDF or DOCX file."
        )
        return

    await update.message.reply_text(
        "⏳ Converting your file..."
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:

            input_path = os.path.join(temp_dir, input_name)
            output_path = os.path.join(temp_dir, output_name)

            new_file = await context.bot.get_file(file.file_id)

            await new_file.download_to_drive(
                custom_path=input_path
            )

            if output_type == "docx":

                await asyncio.to_thread(
                    convert_pdf_to_word,
                    input_path,
                    output_path
                )

            else:

                await asyncio.to_thread(
                    convert_word_to_pdf,
                    input_path,
                    output_path
                )

            with open(output_path, "rb") as output_file:

                await update.message.reply_document(
                    document=output_file,
                    filename=output_name
                )

    except Exception as e:

        print("ERROR:", repr(e))
        traceback.print_exc()

        await update.message.reply_text(
            "❌ Conversion failed. Please try another file."
        )


# Main application
if not TOKEN:
    raise ValueError("Bot Token not found!")

app = (
    Application.builder()
    .token(TOKEN)
    .connect_timeout(60)
    .read_timeout(60)
    .build()
)

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    MessageHandler(filters.Document.ALL, receive_file)
)

print("Bot is running...")

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
    url_path=TOKEN,
    webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
)
