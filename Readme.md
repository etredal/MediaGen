# MediaGen
Create full experiences with AI starting from text script.  A wrapper for ElevenLabs that also includes automatic voice choosing and sound effects.  As well as intermediatory data.

## Features
Text to speech
Label of voices in text
Correlation of text and transcription to timestamps (not as trivial as it sounds due to the need for fuzzy matching)

## How does it work
It seperates the text into chunks.  AI will label the correct voice for each section, the correct music, and the correct sfx.
Then this will be passed to eleven labs to generate the audio.  Then the sfx will be generated/pulled from a source.  Then the pieces
will be stitched together.  Then the next chunk will be operated on and at the end they will be combined into the final mp3.

## Future Features
Labelling for video
Video generation model
Chunk splitting based on context and labeled with scene emotion and other metadata