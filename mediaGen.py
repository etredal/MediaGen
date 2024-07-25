import os
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

DEBUG = True

def GenerateAudio(runID=1, text="Some Subjugates lack a proper understanding of our customs.", voice="Sarah")
  # Load environment variables from .env file to get vars
  load_dotenv()
  eleven_labs_api_key = os.getenv('ELEVEN_LABS_API_KEY')

  client = ElevenLabs(
    api_key=eleven_labs_api_key, # Put your ElevenLabs API key here
  )

  audio = client.generate(
    text=text,
    voice=voice,
    model="eleven_multilingual_v2"
  )

  save(audio, str(runID) + "TestSWT.mp3")