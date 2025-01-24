import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime  # Mengimpor datetime untuk mengambil timestamp
from dotenv import load_dotenv  # Untuk membaca file .env

# Load variabel dari file .env
load_dotenv()

# Mengambil variabel lingkungan
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Token bot Telegram
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  # File kredensial dari .env
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")  # Nama spreadsheet dari .env

# Konfigurasi Google Sheets
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Fungsi untuk menghubungkan ke Google Sheets
def connect_to_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1  # Menyambung ke sheet pertama
    return sheet

# Fungsi untuk menangani perintah /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Halo! Saya adalah bot. Kirimkan laporan yang dimulai dengan '/'. Ketik /help untuk melihat panduan.")

# Fungsi untuk menampilkan panduan melalui perintah /help
async def help_command(update: Update, context: CallbackContext):
    help_text = """
    **Panduan Laporan untuk Bot**:

    1. **Format laporan**:
       - Laporan dimulai dengan tanda `/`.
       - Format yang akan diproses: `/STATUS ORDER/WORK ORDER/NAME ORDER/UPDATE DETAIL/NAME TEKNISI`.
       - Setiap laporan sebaiknya dipisahkan dengan baris baru jika mengirim beberapa laporan dalam satu pesan.

    2. **Contoh Laporan**:
       - Laporan 1:
         ```
         /UPDATE/USULAN/RELOK TIANG KAPASAN/TIANG GESER 20M KEBUTUHAN MATERIAL TIANG 7 1PC, KABEL 100M, UC 2PC, AKSESORIS 4 SET/JONI
         ```
       - Laporan 2:
         ```
         /CLOSE/PREVENTIF TIS/20SBY014 - 20SBY144/DONE PREVENTIF/DIDIK
         ```

    3. **Cara Mengirimkan Laporan**:
       - Cukup kirimkan laporan dalam format di atas. Setiap laporan akan diproses dan disimpan.

    Semoga ini membantu.
    """
    await update.message.reply_text(help_text)

# Fungsi untuk menangani pesan dan menyimpan laporan ke Google Sheets
async def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text

    # Cek apakah pesan mengandung gambar (media lainnya)
    if text:  # Jika ada teks, lanjutkan untuk merekam teks
        report_text = text
    else:  # Jika tidak ada teks, tetapi ada media (gambar, dll.), ambil caption dari media
        if update.message.caption:
            report_text = update.message.caption
        else:
            return  # Jika tidak ada teks maupun caption, tidak ada yang direkam

    # Mengecek apakah pesan dimulai dengan '/'
    if report_text.startswith('/'):
        # Menghapus '/' di awal pesan dan membagi pesan berdasarkan '\n' untuk menangani laporan yang dikirimkan dalam beberapa baris
        report_parts = report_text.lstrip('/').split('\n')  # Pisahkan berdasarkan baris baru
        for report in report_parts:
            if report.strip():
                # Membagi setiap bagian laporan berdasarkan '/' dan menghapus spasi kosong di awal/akhir
                report_details = report.split('/')  # Memisahkan berdasarkan '/'
                report_details = [part.strip() for part in report_details if part.strip()]  # Menghapus spasi kosong dan bagian kosong
                
                # Menambahkan timestamp untuk laporan
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format timestamp: YYYY-MM-DD HH:MM:SS

                # Menghubungkan ke Google Sheets dan menambahkan data
                try:
                    sheet = connect_to_sheet()
                    sheet.append_row([timestamp, user.username, user.id] + report_details)  # Menambahkan laporan dalam kolom yang terpisah
                    await update.message.reply_text("Laporan Anda telah disimpan!")
                except Exception as e:
                    await update.message.reply_text(f"Terjadi kesalahan saat menyimpan laporan: {e}")
    else:
        await update.message.reply_text("Laporan harus dimulai dengan '/'.")

# Fungsi utama untuk menjalankan bot
def main():
    # Buat aplikasi bot
    application = Application.builder().token(TOKEN).build()

    # Tambahkan handler untuk perintah dan pesan
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))  # Menambahkan handler untuk /help
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, handle_message))  # Memfilter pesan teks dan media

    # Jalankan bot
    application.run_polling()

if __name__ == '__main__':
    main()
