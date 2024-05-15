import logging
import textwrap
import markdown
import shutil
import requests
import os
import PIL.Image
import google.generativeai as genai
import requests
import speech_recognition as sr
import pydub
from pydub import AudioSegment
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)
from keep_alive import keep_alive
a=[]
api_genai = os.getenv("gemini_api")
api_tele = os.getenv("tele_api")
TELEGRAM_API_TOKEN = f"{api_tele}"
genai.configure(api_key=f'{api_genai}')
keep_alive()
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
      file = update.message.photo[-1].file_id
      a.append(file)
      obj = await context.bot.getFile(file)
      
      response = requests.get(obj.file_path, stream=True)
      if response.status_code == 200:
          with open(f'{file}.png', 'wb') as file:
              file.write(response.content)
      text=None
      
    else:
      text = update.message.text


    try:
      img = PIL.Image.open(f'{a[-1]}.png')
    except:
      img=None
    
    
    if img is not None and text is not None:
      print(text,a[-1])
      model = genai.GenerativeModel('gemini-pro-vision')
      response = model.generate_content([img,text])
      await context.bot.send_message(chat_id=update.effective_chat.id, text=response.text)
      text=None
      img=None
      os.remove(f'{a[-1]}.png')
    
    if update.message.voice:
      file_aud = update.message.voice.file_id
      obj = await context.bot.getFile(file_aud)
      response = requests.get(obj.file_path, stream=True)
      if response.status_code == 200:
          with open(f'{file_aud}.ogg', 'wb') as file:
              file.write(response.content)
      audio_file = f'{file_aud}.ogg'

      # Convert the audio file to WAV format
      sound = AudioSegment.from_ogg(audio_file)
      sound.export(f'{file_aud}.wav', format="wav")

      # Initialize the recognizer
      recognizer = sr.Recognizer()

      # Load the converted audio file
      audio_file = f'{file_aud}.wav'

      with sr.AudioFile(audio_file) as source:
          audio_data = recognizer.record(source)
      text1 = recognizer.recognize_google(audio_data)
      print(text1)
      model = genai.GenerativeModel('gemini-pro')
      response = model.generate_content(text1)
      await context.bot.send_message(chat_id=update.effective_chat.id, text=response.text)
      os.remove(f'{file_aud}.wav')
      os.remove(f'{file_aud}.ogg')

    if text is not None and img is None:
      model = genai.GenerativeModel('gemini-pro')
      response = model.generate_content(text)
      r_text = response.text.replace('* ', '- ')
      #r_warp=textwrap.indent(r_text, ' `', predicate=lambda _: True)
      #r_m = markdown.markdown(r_warp)
      await context.bot.send_message(chat_id=update.effective_chat.id, text=r_text, parse_mode="MARKDOWN")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.PHOTO & (~filters.COMMAND) | filters.TEXT & (~filters.COMMAND) | 
                                  filters.VOICE & (~filters.COMMAND), echo)
    application.add_handler(start_handler)
    application.add_handler(echo_handler)

    application.run_polling()
