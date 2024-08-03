import os
import anthropic
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

DEBUG = True

def GenerateAudio(runID=1, text="Some Subjugates lack a proper understanding of our customs.", voice="Sarah"):
  # Load environment variables from .env file to get vars
  load_dotenv()
  client = ElevenLabs(
    api_key=os.getenv('ELEVEN_LABS_API_KEY'), # Put your ElevenLabs API key here
  )

  audio = client.generate(
    text=text,
    voice=voice,
    model="eleven_multilingual_v2"
  )

  save(audio, str(runID) + "TestSWT.mp3")

def LabelText(text='''
              Without, the night was cold and wet, but in the small parlour of Laburnum villa the blinds were drawn and the fire burned brightly. Father and son were at chess; the former, who possessed ideas about the game involving radical chances, putting his king into such sharp and unnecessary perils that it even provoked comment from the white-haired old lady knitting placidly by the fire.
              "Hark at the wind," said Mr. White, who, having seen a fatal mistake after it was too late, was amiably desirous of preventing his son from seeing it.
              '''
              ):
  prompt='''
  Add xml to this book text.  Always put sfx inside a voice tag.  You can only use voice and sfx tags.
  Here is the library of sfx.  Always use the same voice for the same character.
  You can insert sfx anywhere between words but inside of a voice tag.  Be creative.
  Remember to split up the xml for the right voices here, the character speaking needs to be in voice,
  but narration text needs to be split up back to the narrator voice.  It should be split by quotes!
  For example, from the raw data we create this:
  <data>
      <voice name="Narrator">
          Unfortunately, Scourge had no proof to back his theory. Yet even exiled to the uncivilized sectors on the farthest borders of the Empire, he had still managed to forge his reputation. His martial skills and <sfx name="Sword Slash"/> ruthless pursuit of the rebel leaders caught the notice of several prominent military leaders. Now, <sfx name="Whoosh"/> two years after leaving the Academy, he had returned to Dromund Kaas as a newly anointed Lord of the Sith. More important, he was here at the personal request of Darth Nyriss, one of the most senior members of the Emperor’s Dark Council.
      </voice>
      <voice name="Sechel">
        <sfx name="Footsteps Approaching"/>“Lord Scourge,” 
      </voice>
      <voice name="Narrator">
        a figure called out over the wind, running up to greet him. 
      </voice>
      <voice name="Sechel">
        “I am Sechel. Welcome to Dromund Kaas.”
      </voice>
      <voice name="Scourge">
          “Welcome back,” 
      </voice>
      <voice name="Narrator">
          Scourge corrected as the man dropped to one knee and bowed his head in a gesture of respect. 
      </voice>
      <voice name="Scourge">
          “This is not my first time on this world.”<sfx name="Bowing sound"/>
      </voice>
  </data>
  -----------------------------------
  Here is the text to label:

  '''

  load_dotenv()
  client = anthropic.Anthropic(
    api_key=os.getenv('CLAUDE_KEY')
  )

  response = client.messages.create(
    model="claude-1.3",
    messages=[
        {
            "role": "user",
            "content": prompt+text,
        }
    ],
    max_tokens=500,
    temperature=0.7
  )

  print(response.content)

if __name__ == '__main__':
  LabelText()