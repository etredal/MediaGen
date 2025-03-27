import os
import anthropic
from openai import OpenAI
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

# Ms in s
SECONDS = 1000

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def GenerateAudio(text, voice, file_name):
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

def GenerateAudioSFX(text, file_name):
  # Load environment variables from .env file to get vars
  load_dotenv()
  client = ElevenLabs(
    api_key=os.getenv('ELEVEN_LABS_API_KEY'),
  )

  audio = client.text_to_sound_effects.convert(
    text=text,
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
  Here is the text to label only include the XML:

  '''

  load_dotenv()
  '''
  client = anthropic.Anthropic(
    api_key=os.getenv('CLAUDE_KEY'),
    base_url="https://api.deepseek.com"
  )

  response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
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
  '''

  client = OpenAI(api_key=os.getenv('DEEPSEEK_KEY'), base_url="https://api.deepseek.com")

  response = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
          {"role": "system", "content": "You are a helpful assistant"},
          {"role": "user", "content": prompt+text},
      ],
      stream=False
  )

  if DEBUG:
    response.choices[0].message.content

  return response.choices[0].message.content

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

def GenerateProject(input_txt='./PeterPanSmall.txt'):
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
      voice = "Brian"

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

def ProcessTranscriptions(project_folder, combined_audio_chunks, chunks):
  # List: File (Combined mp3), [List[dict(sfx,timestamp,min_dist)]]
  file_sfx_timestamps_pairs = []
  i = 0
  for audio_chunk in combined_audio_chunks:
    file_sfx_timestamps_pairs.append(transcribe.transcribeAndCorrelate(project_folder, audio_chunk, chunks[i][1]))

    i += 1
  return file_sfx_timestamps_pairs

def GenerateSFX(project_folder, file_sfx_timestamps_pairs):
  # Key: xml tag mp3, Value: file dir to mp3
  sfx_mp3_map = {}
  for sfx_time_stamp_list in file_sfx_timestamps_pairs:
     for sfx_dict in sfx_time_stamp_list:
        xml_name = sfx_dict['sfx_name']

        start_index = xml_name.find('"') + 1
        end_index = xml_name.find('"', start_index)

        # Extract the value between the quotes
        sfx_prompt_text = xml_name[start_index:end_index]

        if xml_name not in sfx_mp3_map:
          sfx_mp3_file = project_folder + "/sfx_" + sfx_prompt_text.replace(" ", "") + ".mp3"
          GenerateAudioSFX(sfx_prompt_text, sfx_mp3_file)
          sfx_mp3_map[xml_name] = sfx_mp3_file
  
  return sfx_mp3_map

def OverlaySFXList(main, sfx_timestamp_list, final_file_path):
    # Load the existing MP3 file and the SFX file
    existing_mp3 = AudioSegment.from_file(main)

    for sfx_timestamp in sfx_timestamp_list:
      sfx = AudioSegment.from_file(sfx_timestamp[0])
      sfx_adjusted = sfx.apply_gain(-20)

      # Mix the SFX into the existing MP3 file at the desired position
      # Determine the position where you want to mix the SFX (e.g., at 10 seconds)
      position = sfx_timestamp[1] * SECONDS  # Position in milliseconds
      existing_mp3 = existing_mp3.overlay(sfx_adjusted, position=position)

    # Export the mixed audio to a new file
    existing_mp3.export(final_file_path, format="mp3")

def OrchestrateOverlaySFXList(project_folder, combined_audio_chunks, file_sfx_timestamps_pairs, sfx_map):
  finalized_audio_chunks_filepaths = []

  for i in range(len(combined_audio_chunks)):
    combined_audio_path = combined_audio_chunks[i]
    sfx_list = file_sfx_timestamps_pairs[i]

    # build up new list of 
    sfx_with_mp3 = []
    for sfx in sfx_list:
      sfx_with_mp3.append(("./" + sfx_map[sfx['sfx_name']], sfx['start_time']))
    
    final_combined_file_path = "./" + combined_audio_path + "_final.mp3"
    OverlaySFXList(combined_audio_path, sfx_with_mp3, final_combined_file_path)

    finalized_audio_chunks_filepaths.append(final_combined_file_path)

  return finalized_audio_chunks_filepaths

def CombineFinalizedFiles(project_folder, combinedSFX_list, final_name):
  combined_audio = AudioSegment.empty()

  # Combine all the audio files
  for file in combinedSFX_list:
      try:
          audio = AudioSegment.from_file(file)
          combined_audio += audio
      except Exception as e:
          print(f"Error processing file {file}: {e}")

  combined_audio.export("./" + project_folder + "/" + final_name + ".mp3", format="mp3")

  print(f"Finalized audio saved to {final_name}")

if __name__ == '__main__':
  project_file, project_name, project_folder = GenerateProject()
  chunks = SplitAndLabelTxt(project_file, project_folder)
  voice_lists = AudioTranscribeCorrelate(chunks) # TODO: Add voice swapping
  combined_audio_chunks = CombineAudio(voice_lists, project_folder)
  file_sfx_timestamps_pairs = ProcessTranscriptions(project_folder, combined_audio_chunks, chunks)
  sfx_map = GenerateSFX(project_folder, file_sfx_timestamps_pairs)
  combinedSFX_list = OrchestrateOverlaySFXList(project_folder, combined_audio_chunks, file_sfx_timestamps_pairs, sfx_map)
  final_file = CombineFinalizedFiles(project_folder, combinedSFX_list, project_name + "Finalized")