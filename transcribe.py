import whisper
from pydub import AudioSegment
from lxml import etree
import re

DEBUG = True

# Ms to s
SECONDS = 1000

# Load the Whisper model
model = whisper.load_model("base")

# Transcribe the audio file with word-level timestamps
def transcribe_audio(file_path):
    result = model.transcribe(file_path, task="transcribe", language="en", word_timestamps=True)
    return result

# Process the transcription to include timestamps for each word
def process_transcription(transcription):
    words_with_timestamps = []
    for segment in transcription['segments']:
        for word_info in segment['words']:
            words_with_timestamps.append({
                "word": word_info['word'],
                "start": word_info['start'],
                "end": word_info['end']
            })
    return words_with_timestamps

def overlay(main="./1James.mp3", sfx="./blaster.mp3", mixedName="mixed"):
    # Load the existing MP3 file and the SFX file
    existing_mp3 = AudioSegment.from_file(main)
    sfx = AudioSegment.from_file(sfx)

    # Determine the position where you want to mix the SFX (e.g., at 10 seconds)
    position = 0.5 * SECONDS  # Position in milliseconds

    sfx_adjusted = sfx.apply_gain(-20)

    # Mix the SFX into the existing MP3 file at the desired position
    mixed = existing_mp3.overlay(sfx_adjusted, position=position)

    # Export the mixed audio to a new file
    mixed.export("./" + mixedName + ".mp3", format="mp3")

# Function to get the text content of an element including its children
def get_element_text(element):
    text = element.text if element.text else ''
    for child in element:
        text += f' <{child.tag} name="{child.attrib["name"]}"/> ' + (child.tail if child.tail else '')
    return text.strip()

def normalize(text):
    """Strips all non-letter characters from a string and converts to lowercase."""
    return re.sub(r"[^a-zA-Z]+", "", text).lower()  # Lowercase added

# General runner: Takes file and generates xml, transcription, mp3, correlation sfx to mp3, final audio
def run(file_name = "1James"):
    file_name = "1James"
    file_path = "./" + file_name + ".mp3"
    transcription = transcribe_audio(file_path)
    words_with_timestamps = process_transcription(transcription)

    # Print the result
    if DEBUG:
        for item in words_with_timestamps:
            print(f"{item['word']} (Start: {item['start']}s, End: {item['end']}s)")

    # Write transcription to file
    with open(file_name + "TranscriptionOutput.txt", "w") as file:
        # Iterate through each item in the list
        for item in words_with_timestamps:
            # Write the item to the file
            file.write(f"{item['word']} (Start: {item['start']}s, End: {item['end']}s)\n")

    tree = etree.parse('./LabeledText.xml')
    notags = etree.tostring(tree, encoding='utf8', method='text').decode('utf8')
    stripped_xml = notags.replace("\n", "").replace("\t", "").split(" ")
    filtered_list = [item for item in stripped_xml if item]

    print(filtered_list)
    print(words_with_timestamps)

# Main function
if __name__ == "__main__":
    run()