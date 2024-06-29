import re
from Levenshtein import distance as levenshtein_distance

# > S1 Output: xml with just the sfx
# > S2 input xml with sfx and words, output list  of the tuple of sfx and words to left and right
# > S3 lievschtein matching, sliding window where i compare each word, then i get the timestamp of the middle word

DEBUG = False

def get_sfx_words(xml_string):
    # Regular expression to match tags including <sfx>
    tag_pattern = re.compile(r'<[^>]+>|[^<]+')

    # Find all tags including <sfx>
    tags = tag_pattern.findall(xml_string)

    # Initialize list for words
    words = []

    # Iterate through tags and split words outside tags
    for tag in tags:
        if tag.startswith('<'):
            # If it's a tag, check if it's <sfx>
            if tag.startswith('<sfx'):
                words.append(tag)  # Append <sfx> tags as they are
        else:
            # Split non-tag parts by spaces and add to words
            words.extend(tag.split())

    sfx_positions = [i for i, word in enumerate(words) if word.startswith('<sfx')]
    closest_words = []

    for pos in sfx_positions:
        left_words = words[max(0, pos-5):pos]
        right_words = words[pos+1:pos+6]

        left_words = [word for word in left_words if not word.startswith('<sfx')]
        right_words = [word for word in right_words if not word.startswith('<sfx')]

        closest_words.append((words[pos], left_words, right_words))

    return closest_words

def sliding_window_match(sfx_words, timestamped_words):
    best_matches = []

    for tuple in sfx_words:
        combined_sfx_words = tuple[1] + tuple[2]
        combined_sfx_text = " ".join(combined_sfx_words).lower()

        min_distance = float('inf')
        start_time = None

        window_size = len(combined_sfx_words)
        for i in range(len(timestamped_words) - window_size + 1):
            window_words = [timestamped_words[j] for j in range(i, i + window_size)]
            window_text = " ".join([word["word"] for word in window_words]).lower()

            current_distance = levenshtein_distance(combined_sfx_text, window_text)

            if DEBUG:
                print("------------------------------")
                print(combined_sfx_text)
                print(window_text)
                print(current_distance)
            
            if current_distance < min_distance:
                min_distance = current_distance
                
                # Find the start time of the first word in the "after" list that matches right_words
                start_time = window_words[len(tuple[1])]["start"]

        if start_time is not None and min_distance < 25:
            best_matches.append({
                "sfx_name": tuple[0],
                "start_time": start_time,
                "min_dist_lev": min_distance
            })

    return best_matches

def convert_to_dict(text):
    pattern = re.compile(r'(\w+)\s*\(Start:\s*([\d.]+)s,\s*End:\s*([\d.]+)s\)')
    matches = pattern.findall(text)

    word_list = []
    for match in matches:
        word_dict = {
            "word": match[0],
            "start": float(match[1]),
            "end": float(match[2])
        }
        word_list.append(word_dict)
    
    return word_list

def main():
    xml_string = """
    <data>
        <voice name="Narrator">
            LORD SCOURGE RAISED <sfx name="hello">the hood of his cloak as he stepped off the<sfx name="shuttle"> shuttle, a shield against the wind and pelting rain. Storms were common here on Dromund Kaas; dark clouds perpetually blocked out the sun, rendering terms like day and night meaningless. The only natural illumination came from the frequent bursts of <sfx name="Lightning Crackle"/> lightning arcing across the sky, but the glow from the spaceport and nearby Kaas City provided more than enough light to see where he was going.

            Lord Scourge, I am Sechel. Welcome to Dromund Kaas.
        </voice>
        <voice name="Narrator">
            The powerful electrical storms were a physical manifestation of the dark side power that engulfed the entire planet—a power that had brought the Sith back here a millennium before, when their very survival had been in doubt.
            After a crushing defeat in the Great Hyperspace War, the Emperor had risen up from the tattered ranks of the remaining Sith Lords to lead his followers on a desperate exodus to the farthest reaches of the galaxy. Fleeing the Republic armies and the relentless revenge of the Jedi, they eventually resettled far beyond the borders of Republic-charted space on their long-lost ancestral homeworld.
            There, safely hidden from their enemies, the Sith began to rebuild their Empire. Under the guidance of the Emperor—the immortal and all-powerful savior who still reigned over them even after a thousand years—they abandoned the hedonistic lifestyles of their barbaric ancestors.
            Instead they created a near-perfect society in which the Imperial military operated and controlled virtually every aspect of daily life. Farmers, mechanics, teachers, cooks, janitors—all were part of the great martial machine, each individual a cog trained to perform his or her duties with maximum discipline and efficiency. As a result, the Sith had been able to conquer and enslave world after world in the unexplored regions of the galaxy, until their power and influence rivaled those of their glorious past.
        </voice>
        <voice name="Narrator">
            Scourge corrected as the man dropped to one knee and bowed his head in a gesture of respect. This is not my first time on this world.
            Sechel’s hood was pulled up against the rain, covering his features, but during his approach Scourge had noticed the red skin and dangling cheek tendrils that marked him as a pureblood Sith, just like Lord Scourge himself. But while Scourge was an imposing figure, tall and broad-shouldered, this man was small and slight. Reaching out, Scourge sensed only the faintest hint of the Force in the other, and his features twisted into a sneer of revulsion.
            Unlike the humans that made up the bulk of the Empire’s population, the Sith species were all blessed with the power of the Force to varying degrees. It marked them as the elite; it elevated them above the lower ranks of Imperial society. And it was a legacy that was fervently protected.
            A pureblood born without any connection to the Force was an abomination; by custom such a creature could not be suffered to live. During his time at the Academy, Lord Scourge had encountered a handful of Sith whose power in the Force was noticeably weak. Hampered by their failing, they relied on the influence of their high-ranking families to find them postings as low-level aids or administrative officials at the Academy, where their handicap would be least noticed. Spared from the lower castes only by their pureblood heritage, in Scourge’s eyes they were barely better than slaves, though he did have to admit that the more competent ones could have their uses.
            But never before had he encountered one of his own kind with as feeble an attunement to the Force as the man huddled at his feet. The fact that Darth Nyriss had sent someone so vile and unworthy to greet him was unsettling. He’d expected a more substantial and impressive welcome.
            <sfx name="Scourge Laugh"/>
            Welcome back.
            <sfx name="Scourge Laugh"/>
            Welcome back again.
        </voice>
    </data>
    """

    text_timestamps = """
    Lord (Start: 0.0s, End: 0.24s)
    Scourge (Start: 0.24s, End: 0.76s)
    raised (Start: 0.76s, End: 1.0s)
    the (Start: 1.0s, End: 1.24s)
    hood (Start: 1.24s, End: 1.38s)
    of (Start: 1.38s, End: 1.52s)
    his (Start: 1.52s, End: 1.66s)
    cloak (Start: 1.66s, End: 1.94s)
    as (Start: 1.94s, End: 2.54s)
    he (Start: 2.54s, End: 2.68s)
    stepped (Start: 2.68s, End: 2.94s)
    off (Start: 2.94s, End: 3.2s)
    the (Start: 3.2s, End: 3.36s)
    shuttle (Start: 3.36s, End: 3.7s)
    a (Start: 4.24s, End: 4.34s)
    shield (Start: 4.34s, End: 4.76s)
    against (Start: 4.76s, End: 5.14s)
    the (Start: 5.14s, End: 5.38s)
    wind (Start: 5.38s, End: 5.58s)
    and (Start: 5.58s, End: 5.92s)
    pelting (Start: 5.92s, End: 6.38s)
    rain (Start: 6.38s, End: 6.86s)
    Storms (Start: 7.88s, End: 8.4s)
    were (Start: 8.4s, End: 8.48s)
    common (Start: 8.48s, End: 8.8s)
    here (Start: 8.8s, End: 9.12s)
    on (Start: 9.12s, End: 9.34s)
    Drummond (Start: 9.34s, End: 9.72s)
    Casse (Start: 9.72s, End: 10.18s)
    dark (Start: 10.9s, End: 11.18s)
    clouds (Start: 11.18s, End: 11.7s)
    perpetually (Start: 11.7s, End: 12.4s)
    blocked (Start: 12.4s, End: 12.72s)
    out (Start: 12.72s, End: 12.98s)
    the (Start: 12.98s, End: 13.18s)
    sun (Start: 13.18s, End: 13.56s)
    rendering (Start: 14.18s, End: 14.36s)
    terms (Start: 14.36s, End: 14.92s)
    like (Start: 14.92s, End: 15.26s)
    day (Start: 15.26s, End: 15.58s)
    and (Start: 15.58s, End: 15.86s)
    night (Start: 15.86s, End: 16.14s)
    meaningless (Start: 16.14s, End: 17.06s)
    The (Start: 18.32s, End: 18.66s)
    only (Start: 18.66s, End: 18.88s)
    natural (Start: 18.88s, End: 19.32s)
    illumination (Start: 19.32s, End: 20.06s)
    came (Start: 20.06s, End: 20.7s)
    from (Start: 20.7s, End: 21.0s)
    the (Start: 21.0s, End: 21.12s)
    frequent (Start: 21.12s, End: 21.52s)
    bursts (Start: 21.52s, End: 21.9s)
    of (Start: 21.9s, End: 22.28s)
    lightning (Start: 22.28s, End: 22.58s)
    arcing (Start: 22.58s, End: 23.5s)
    across (Start: 23.5s, End: 23.84s)
    the (Start: 23.84s, End: 24.1s)
    sky (Start: 24.1s, End: 24.46s)
    but (Start: 24.46s, End: 25.44s)
    the (Start: 25.44s, End: 25.56s)
    glow (Start: 25.56s, End: 25.8s)
    from (Start: 25.8s, End: 26.02s)
    the (Start: 26.02s, End: 26.18s)
    spaceport (Start: 26.18s, End: 26.86s)
    and (Start: 26.86s, End: 27.34s)
    nearby (Start: 27.34s, End: 27.64s)
    Car (Start: 27.64s, End: 28.06s)
    City (Start: 28.06s, End: 28.48s)
    provided (Start: 28.48s, End: 29.24s)
    more (Start: 29.24s, End: 29.6s)
    than (Start: 29.6s, End: 29.72s)
    enough (Start: 29.72s, End: 29.98s)
    light (Start: 29.98s, End: 30.26s)
    to (Start: 30.26s, End: 30.84s)
    see (Start: 30.84s, End: 31.06s)
    where (Start: 31.06s, End: 31.26s)
    he (Start: 31.26s, End: 31.38s)
    was (Start: 31.38s, End: 31.54s)
    going. (Start: 31.54s, End: 31.9s)
    """

    print(correlate_sfx_times(xml_string, text_timestamps))

def correlate_sfx_times(xml_string, text_timestamps):
    sfx_near_words = get_sfx_words(xml_string)
    text_timestamp_info = convert_to_dict(text_timestamps)
    return sliding_window_match(sfx_near_words, text_timestamp_info)

if __name__ == "__main__":
    main()
