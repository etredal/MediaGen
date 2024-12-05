import os
import anthropic
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import re
import shutil
import transcribe
import xml.etree.ElementTree as ET
import pydub
from pydub import AudioSegment

DEBUG = True

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def GenerateAudio(text="Some Subjugates lack a proper understanding of our customs.", voice="Sarah", file_name="./Test"):
  # Load environment variables from .env file to get vars
  load_dotenv()
  client = ElevenLabs(
    api_key=os.getenv('ELEVEN_LABS_API_KEY'),
  )

  audio = client.generate(
    text=text,
    voice=voice,
    model="eleven_multilingual_v2"
  )

  save(audio, file_name)

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
  DO NOT INCLUDE ANYTHING EXCEPT THE XML.  Makesure to include the </data>
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
    model="claude-2.0",
    messages=[
        {
            "role": "user",
            "content": prompt+text,
        }
    ],
    max_tokens=500,
    temperature=0.7
  )

  if DEBUG:
     print(response.content[0].text)
  
  return response.content[0].text

def split_text(file_path, max_chunk_size=3000):
  text = read_file(file_path)

  # Define a pattern to split paragraphs, sentences, or chapters
  # Here, we'll use paragraphs as the primary split criteria
  paragraphs = re.split(r'\n\s*\n', text)
  
  chunks = []
  current_chunk = ''
  
  for paragraph in paragraphs:
      # If adding this paragraph would exceed the max chunk size, save the current chunk
      if len(current_chunk) + len(paragraph) + 1 > max_chunk_size:
          chunks.append(current_chunk.strip())
          current_chunk = paragraph
      else:
          current_chunk += '\n\n' + paragraph
  
  # Add any remaining content as the last chunk
  if current_chunk:
      chunks.append(current_chunk.strip())
  
  return chunks

def Chunk(file_path, output_folder):
  # Adjust the chunk size as needed to fit about a page
  max_chunk_size = 3000
  if DEBUG:
    max_chunk_size = 100

  chunks = split_text(file_path, max_chunk_size=max_chunk_size)

  if DEBUG:
     chunks = chunks[0:5]
  
  total = len(chunks)
  chunk_map = { "Chunk Count": total, "Chunks": [] }
  for i, chunk in enumerate(chunks):
    chunk_filename = f'chunk_{i+1}.txt'
    chunk_path = os.path.join(output_folder, chunk_filename)
    
    # Write the chunk to the output folder
    with open(chunk_path, 'w', encoding='utf-8') as file:
      file.write(chunk)

    chunk_map["Chunks"].append(chunk_path)
    
    print(f'Chunk {i+1} saved as {chunk_path}')
  
  return chunk_map

def GenerateProject(input_txt='./Small_Test.txt'):
  project_file = input_txt
  project_name = project_file.removeprefix('./').removesuffix('.txt')
  project_folder = project_name + '_mediaGen'

  if os.path.exists(project_folder):
    shutil.rmtree(project_folder)
  os.makedirs(project_folder)

  return project_file, project_name, project_folder

def SplitAndLabelTxt(project_file, project_folder):
  chunks_map = Chunk(project_file, project_folder)

  chunks_pair = []
  for chunk in chunks_map["Chunks"]:
    raw_text = read_file(chunk)
    labeled_text = LabelText(text = raw_text)
    labeled_path = os.path.join(os.path.dirname(chunk), os.path.basename(chunk).replace('.', '_labeled.')).replace('\\','/')

    chunks_pair.append((chunk, labeled_path))

    prepared_labeled_text = re.search(r'<data>(.*?)</data>', labeled_text, re.DOTALL)

    if (prepared_labeled_text):
      with open(labeled_path, 'w', encoding='utf-8') as file:
        file.write(prepared_labeled_text.group(0))
    else:
       with open(labeled_path, 'w', encoding='utf-8') as file:
        file.write("<data>"+labeled_text+"</data>")

  return chunks_pair

def XMLChunk(labeled_file_path):
  text = read_file("./" + labeled_file_path)
  print("NOTICE" + text)
  root = ET.fromstring(text)

  # Initialize the list to hold parsed data
  parsed_data = []

  # Iterate over each <voice> element
  for voice in root.findall("voice"):
      # Get the 'name' attribute
      voice_name = voice.get("name")
      # Get the text content, ignoring <sfx> tags and preserving text only
      voice_text = "".join(voice.itertext()).strip()
      # Append to parsed data list
      parsed_data.append({"voice": voice_name, "text": voice_text})

  return parsed_data

def AudioTranscribeCorrelate(chunks_pair):
  voice_lists = {}
  for chunk_pair in chunks_pair:
    xml_voice_list = XMLChunk(chunk_pair[1])
    cur_mp3 = 1

    voice_lists[chunk_pair[0]] = []
    for pair in xml_voice_list:
      voice = pair["voice"]
      voice = "Sarah"

      audio_path = "./" + chunk_pair[0].removeprefix('./').removesuffix('.txt').replace("\\","/") + "_" + str(cur_mp3) + ".mp3"

      GenerateAudio(pair["text"], voice, audio_path)
      cur_mp3 += 1

      voice_lists[chunk_pair[0]].append(audio_path)

  return voice_lists

def CombineAudio(voice_lists, project_folder):
  combined_audio_chunks = []

  cur_chunk = 1
  for key, file_paths in voice_lists.items():
      combined = AudioSegment.empty()
      for audio_clip in file_paths:
        # Load each audio file
        if (DEBUG):
          print(f"Processing key: {key}, file: {audio_clip}")
        audio = AudioSegment.from_file(audio_clip)
        combined += audio
      combined_audio_filepath = project_folder + "/chunk_" + str(cur_chunk) + "_combined" + ".mp3"
      combined.export(combined_audio_filepath, format="mp3")
      combined_audio_chunks.append(combined_audio_filepath)

      cur_chunk += 1
  
  return combined_audio_chunks

if __name__ == '__main__':
  project_file, project_name, project_folder = GenerateProject()
  chunks = SplitAndLabelTxt(project_file, project_folder)
  voice_lists = AudioTranscribeCorrelate(chunks)
  combined_audio_chunks = CombineAudio(voice_lists, project_folder)
  # Parse and generate every SFX
  # correlate
  # Add sfx to each location
  # Combine all final files for final audio