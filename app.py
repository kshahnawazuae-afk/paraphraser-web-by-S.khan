# app.py - Streamlit Web Version
# pip install streamlit deep-translator nltk

import streamlit as st
from deep_translator import GoogleTranslator
import random
import re
import unicodedata
import statistics
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('omw-1.4')

# ============ PAGE SETUP ============
st.set_page_config(page_title="AI Text Paraphraser", layout="wide", initial_sidebar_state="expanded")

# ============ CUSTOM CSS ============
st.markdown("""
<style>
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { text-align: center; color: #666; margin-bottom: 1.5rem; }
    .stTextArea textarea { border-radius: 8px; border: 1px solid #ddd; font-size: 14px; }
    .output-box { border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #f9f9f9; min-height: 200px; }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
if 'output_text' not in st.session_state:
    st.session_state.output_text = ""
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""

# ============ TONE PROFILES ============
TONE_CONFIGS = {
    'academic': {
        'target_sentence_length': (18, 28), 'contraction_rate': 0.05,
        'passive_rate': 0.4, 'transition_style': 'formal',
        'voice_markers': ['may suggest', 'appears to', 'indicates that', 'it is possible that'],
        'punchy_sentence_rate': 0.0, 'paragraph_style': 'long',
        'hedging': ['arguably,', 'perhaps', 'it could be argued that', 'one might say', 'to some extent,'],
        'stance': [], 'personal': [],
    },
    'journalistic': {
        'target_sentence_length': (12, 20), 'contraction_rate': 0.4,
        'passive_rate': 0.1, 'transition_style': 'direct',
        'voice_markers': ['In fact,', 'The reality is,', 'What matters is'],
        'punchy_sentence_rate': 0.3, 'paragraph_style': 'short',
        'hedging': [],
        'stance': ['This is misleading.', 'The data tells a different story.', 'That claim does not hold up.', 'The evidence suggests otherwise.'],
        'personal': [],
    },
    'conversational': {
        'target_sentence_length': (5, 22), 'contraction_rate': 0.8,
        'passive_rate': 0.0, 'transition_style': 'casual',
        'voice_markers': ['you know,', 'think about it,', 'here is the thing:', 'honestly,'],
        'punchy_sentence_rate': 0.5, 'paragraph_style': 'mixed',
        'hedging': [], 'stance': [],
        'personal': ['This caught my attention.', 'I find this interesting.', 'What strikes me is', 'If you ask me,'],
    },
}

# ============ AI BUZZWORDS ============
AI_BUZZWORDS = {
    'delve': ['explore', 'look into', 'examine', 'dig into'],
    'crucial': ['important', 'key', 'vital', 'essential'],
    'moreover': ['also', 'plus', 'besides', 'on top of that'],
    'furthermore': ['also', 'in addition', 'what is more'],
    'consequently': ['so', 'as a result', 'therefore', 'because of this'],
    'additionally': ['also', 'plus', 'in addition', 'further'],
    'significantly': ['notably', 'greatly', 'by a wide margin', 'considerably'],
    'comprehensive': ['thorough', 'detailed', 'in-depth', 'full'],
    'underscores': ['highlights', 'shows', 'points to', 'makes clear'],
    'demonstrates': ['shows', 'reveals', 'proves', 'makes clear'],
    'showcases': ['displays', 'presents', 'features', 'shows'],
    'robust': ['strong', 'solid', 'reliable', 'sturdy'],
    'paramount': ['critical', 'vital', 'essential', 'top priority'],
    'transformative': ['game-changing', 'major', 'revolutionary', 'big'],
    'dive': ['jump', 'go', 'look', 'get'],
    'ensure': ['make sure', 'guarantee', 'confirm', 'see to it'],
    'leverage': ['use', 'tap into', 'draw on', 'make use of'],
    'align': ['match', 'fit', 'line up', 'sync'],
    'foster': ['build', 'grow', 'create', 'encourage'],
    'streamline': ['simplify', 'speed up', 'smooth out'],
    'optimize': ['improve', 'boost', 'tune up', 'get the most from'],
    'facilitate': ['help', 'enable', 'make possible', 'assist'],
    'utilize': ['use', 'employ', 'apply', 'put to work'],
    'regarding': ['about', 'on', 'concerning', 'related to'],
    'therefore': ['so', 'as a result', 'thus', 'because of this'],
    'thus': ['so', 'therefore', 'as a result', 'hence'],
    'hence': ['so', 'thus', 'therefore', 'as a result'],
    'nonetheless': ['still', 'even so', 'that said', 'all the same'],
    'notably': ['importantly', 'in particular', 'especially'],
    'indeed': ['in fact', 'really', 'truly', 'actually'],
    'highlight': ['point out', 'show', 'stress', 'emphasize'],
    'emphasize': ['stress', 'highlight', 'point out', 'underline'],
    'address': ['deal with', 'tackle', 'handle', 'take on'],
    'mitigate': ['reduce', 'lessen', 'ease', 'cut'],
    'implement': ['put in place', 'carry out', 'apply', 'use'],
    'disseminate': ['spread', 'share', 'circulate', 'distribute'],
    'elucidate': ['explain', 'clarify', 'shed light on', 'spell out'],
    'endeavor': ['try', 'attempt', 'effort', 'work'],
    'commence': ['start', 'begin', 'kick off', 'launch'],
    'terminate': ['end', 'stop', 'finish', 'wrap up'],
    'ascertain': ['find out', 'determine', 'figure out', 'work out'],
    'necessitate': ['require', 'need', 'call for', 'demand'],
    'nevertheless': ['still', 'even so', 'that said', 'however'],
}

# ============ AI PHRASES ============
AI_PHRASES = {
    'dive into': 'explore', 'deep dive': 'detailed look', 'game changer': 'major shift',
    'cutting edge': 'advanced', 'state of the art': 'modern', 'paradigm shift': 'major change',
    'low hanging fruit': 'easy win', 'move the needle': 'make progress',
    'north star': 'guiding principle', 'bleeding edge': 'very advanced',
    'thought leadership': 'expertise', 'circle back': 'follow up', 'double down': 'commit to',
    'end to end': 'complete', 'plug and play': 'ready to use', 'one stop shop': 'all-in-one solution',
    'win win': 'mutually beneficial', 'out of the box': 'ready-made',
    'from the ground up': 'completely', 'soup to nuts': 'comprehensive',
    'full stack': 'complete', 'best in class': 'top quality', 'next level': 'advanced',
    'value add': 'benefit', 'pain point': 'problem', 'value proposition': 'benefit',
    'real world': 'practical', 'hands on': 'practical', 'mission critical': 'essential',
    'future proof': 'long-lasting', 'best practices': 'recommended methods',
    'holistic approach': 'complete method', 'comprehensive guide': 'full guide',
    'definitive guide': 'complete guide', 'ultimate guide': 'complete guide',
    'step by step guide': 'instructions', 'robust framework': 'strong structure',
    'robust solution': 'reliable fix', 'in today world': 'currently',
    'in today fast-paced': 'now', 'it is worth noting': 'notably', 'it worth noting': 'notably',
    'it is important to note': 'importantly', 'it important to note': 'importantly',
    'needless to say': 'clearly', 'it goes without saying': 'clearly',
    'without further ado': '', 'let me break this down': '', 'let me explain': '',
    'let me walk you through': '', 'here is the thing': '', 'here what you need to know': '',
    'here the deal': '', 'that being said': 'however', 'having said that': 'however',
    'with that in mind': '', 'it bears mentioning': 'notably', 'it should be noted': 'notably',
    'on a broader scale': 'broadly', 'in the grand scheme': 'overall',
    'the crux of the matter': 'the key point', 'by and large': 'mostly',
    'for all intents and purposes': 'essentially', 'in a nutshell': 'briefly',
    'to put it simply': 'simply', 'in essence': 'basically', 'at the heart of': 'centrally',
    'in the realm of': 'in', 'navigate the complexities': 'handle',
    'navigate the landscape': 'understand', 'ever-evolving': 'changing',
    'ever-changing': 'changing', 'fast-paced': 'quick', 'rapidly evolving': 'changing fast',
    'dynamic landscape': 'changing field', 'shifting landscape': 'changing situation',
    'a myriad of': 'many', 'a plethora of': 'many', 'not only but also': 'and',
    'while it true that': 'although', 'on the flip side': 'however',
    'by the same token': 'similarly', 'it no secret that': 'clearly',
    'the elephant in the room': 'the obvious issue', 'food for thought': 'worth considering',
    'key takeaway': 'main point', 'key takeaways': 'main points', 'wrapping up': 'finally',
    'to wrap up': 'finally', 'in summary': 'overall', 'to sum up': 'overall',
    'all in all': 'overall', 'above and beyond': 'beyond', 'serves as a testament': 'shows',
    'stands as a testament': 'shows', 'a testament to': 'proof of',
    'last but not least': 'finally', 'firstly': 'first', 'secondly': 'second',
    'thirdly': 'third', 'in this regard': 'here', 'to that end': 'for this',
    'with that being said': 'however', 'it could be argued': 'perhaps',
    'one might say': 'perhaps', 'at the end of the day': 'ultimately',
    'moving forward': 'going forward', 'when it comes to': 'regarding',
    'in light of': 'given', 'all things considered': 'overall',
    'the bottom line': 'the key point', 'at its core': 'fundamentally',
}

# ============ COLLOQUIAL MAPPING ============
HUMAN_MESSY_MAP = {
    "it is very": ["it's pretty", "it's actually quite"],
    "it is extremely": ["it's really", "it's incredibly"],
    "however": ["but then again,", "that said,", "though,"],
    "therefore": ["so basically,", "which means,"],
    "additionally": ["also,", "plus,", "not to mention"],
    "in conclusion": ["so yeah,", "at the end of the day,", "all in all,"],
    "concerning": ["about", "on the topic of"],
    "utilize": ["use", "go with"],
    "subsequently": ["after that,", "then,"],
    "nevertheless": ["still,", "even so,"],
    "furthermore": ["also,", "what's more,"],
    "consequently": ["so,", "as a result,"],
    "significantly": ["a lot", "quite a bit"],
    "approximately": ["about", "roughly"],
    "substantially": ["a great deal", "quite a lot"],
}

# ============ SAFE SYNONYM OVERRIDES ============
SAFE_SYNONYM_OVERRIDES = {
    'difficult': ['tough', 'hard', 'tricky'], 'important': ['key', 'vital', 'central'],
    'significant': ['big', 'major', 'notable'], 'interesting': ['striking', 'notable', 'compelling'],
    'large': ['sizable', 'big', 'substantial'], 'small': ['minor', 'slight', 'limited'],
    'clear': ['plain', 'obvious', 'evident'], 'complex': ['tricky', 'involved', 'detailed'],
    'effective': ['useful', 'powerful', 'strong'], 'critical': ['vital', 'key', 'central'],
    'increase': ['rise', 'grow', 'climb'], 'decrease': ['drop', 'fall', 'decline'],
    'quickly': ['fast', 'rapidly', 'swiftly'], 'slowly': ['gradually', 'bit by bit', 'steadily'],
}

# ============ TRANSLATION LANGUAGES ============
QUALITY_LANGUAGES = ['es', 'fr', 'pt', 'it']
STEALTH_LANGUAGES = ['vi', 'tr', 'is', 'th', 'id', 'tl', 'sw', 'bn', 'fa', 'et']

# ============ ALL FUNCTIONS (same logic as main.py) ============

def strip_unicode_watermarks(text):
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u2060-\u2069\uFEFF]', '', text)
    text = re.sub(r'[\uFE00-\uFE0F]', '', text)
    text = re.sub(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u0080-\u009f]', '', text)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    return text

def remove_em_dashes(text):
    text = re.sub(r'\s*—\s*', lambda m: random.choice([', ', '. ', '; ', ': ']), text)
    text = re.sub(r'\s*–\s*', lambda m: random.choice([', ', '. ', ' - ']), text)
    text = re.sub(r'\s*--\s*', lambda m: random.choice([', ', '. ', '; ']), text)
    text = re.sub(r'\s*---\s*', '. ', text)
    return text

def remove_ai_markers(text):
    ai_intros = [
        r'^Certainly[!,.]?\s*', r'^Sure[!,.]?\s*', r'^Of course[!,.]?\s*',
        r'^I\'d be happy to\s*', r'^Here is the\s*', r'^Here are the\s*',
        r'^Let me\s*', r'^I hope this\s*',
        r'^The (paper|article|review) is (best )?(characterized|described|classified) as\s*',
        r'^This (paper|article|review) (examines|explores|investigates|discusses)\s*',
        r'^Let me (explain|break this down|walk you through|be clear)\s*',
        r"^Here'?s (the thing|what|the deal|the kicker|what you need to know)\s*",
        r'^(What makes this|Why this matters|Why it matters|How this works|What this means)\s*',
        r'^In this (article|post|guide|blog|piece|section|overview)\s*',
        r"^It'?s worth (noting|mentioning|highlighting|pointing out)\s*",
        r'^(TL;?DR|Key takeaway|Bottom line|In a nutshell)\s*:?',
        r'^(To summarize|To sum up|In summary|Wrapping up|To wrap up)\s*',
        r'^(All in all|Above and beyond|Last but not least)\s*',
        r'^(Needless to say|It goes without saying|Without further ado)\s*',
        r"^(In today'?s world|In today'?s fast-paced|As we navigate)\s*",
        r'^(The bottom line|At its core|At the end of the day|At the heart of)\s*',
    ]
    for pattern in ai_intros:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s*Let me know if.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Feel free to.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*I hope this helps.*$', '', text, flags=re.IGNORECASE)
    return text.strip()

def clean_output(text):
    text = strip_unicode_watermarks(text)
    text = remove_em_dashes(text)
    text = remove_ai_markers(text)
    text = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2010-\u2015\u2018-\u2019\u201c-\u201d\u2020-\u2022\u2026\u2030-\u2033\u2039-\u203a\u2044\u20AC]', '', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', text)
    text = re.sub(r'\.\s+,', '.,', text)
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'\.{2}', '.', text)
    text = re.sub(r'\bfor\.\s+([A-Z])', r'for \1', text)
    text = re.sub(r'\bavailable for\.\s+', 'available for ', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r"\s+'\s*", "'", text)
    text = re.sub(r"\s+'", "'", text)
    text = re.sub(r'\$\s+', '$', text)
    text = re.sub(r'(\d)\s+%', r'\1%', text)
    text = re.sub(r'\bin\.\s+The\b', 'in the', text)
    text = re.sub(r'\bto\.\s+([A-Z])', lambda m: 'to ' + m.group(1).lower(), text)
    return text.strip()

def remove_ai_buzzwords(text, intensity):
    if intensity < 30: return text
    words = text.split()
    new_words = []
    for word in words:
        suffix = ''
        core_word = word
        while core_word and core_word[-1] in '.,;:!?()[]{}"\'':
            suffix = core_word[-1] + suffix
            core_word = core_word[:-1]
        clean_word = core_word.lower()
        if clean_word in AI_BUZZWORDS and random.random() < (intensity / 100) * 0.6:
            replacement = random.choice(AI_BUZZWORDS[clean_word])
            if core_word[0].isupper(): replacement = replacement[0].upper() + replacement[1:]
            new_words.append(replacement + suffix)
        else:
            new_words.append(word)
    return ' '.join(new_words)

def remove_ai_phrases(text, intensity):
    if intensity < 25: return text
    text_lower = text.lower()
    for phrase, replacement in AI_PHRASES.items():
        if phrase in text_lower and random.random() < (intensity / 100) * 0.5:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            if replacement:
                text = pattern.sub(replacement, text, count=1)
            else:
                text = pattern.sub('', text, count=1).strip()
                text = re.sub(r' {2,}', ' ', text)
    return text

def apply_colloquial_injection(text, intensity):
    if intensity < 35: return text
    for formal, informal_list in HUMAN_MESSY_MAP.items():
        if re.search(rf'\b{formal}\b', text, re.IGNORECASE) and random.random() < (intensity / 100) * 0.4:
            replacement = random.choice(informal_list)
            text = re.sub(rf'\b{formal}\b', replacement, text, count=1, flags=re.IGNORECASE)
    return text

def get_safe_synonym(word, pos_tag, intensity):
    if random.random() > (intensity / 100) * 0.15: return word
    word_lower = word.lower()
    if word_lower in SAFE_SYNONYM_OVERRIDES:
        syn = random.choice(SAFE_SYNONYM_OVERRIDES[word_lower])
        if word[0].isupper(): syn = syn[0].upper() + syn[1:]
        return syn
    tag_map = {'NN': wordnet.NOUN, 'JJ': wordnet.ADJ, 'VB': wordnet.VERB, 'RB': wordnet.ADV}
    wn_tag = tag_map.get(pos_tag[:2])
    if not wn_tag: return word
    syns = wordnet.synsets(word, pos=wn_tag)
    if not syns: return word
    lemmas = []
    for s in syns[:2]:
        for l in s.lemmas():
            lemma_name = l.name().replace('_', ' ')
            if (lemma_name.lower() != word.lower() and len(lemma_name) <= 10 and lemma_name.isalpha() and ' ' not in lemma_name):
                lemmas.append(lemma_name)
    if not lemmas: return word
    return random.choice(lemmas)

def apply_pos_jitter(text, intensity):
    if intensity < 35: return text
    try:
        tokens = word_tokenize(text)
        tagged = nltk.pos_tag(tokens)
        new_words = []
        for word, tag in tagged:
            if len(word) > 3 and tag[:2] in ['JJ', 'RB', 'VB']:
                new_word = get_safe_synonym(word, tag, intensity)
                if word[0].isupper(): new_word = new_word[0].upper() + new_word[1:]
                new_words.append(new_word)
            else:
                new_words.append(word)
        result = " ".join(new_words)
        result = re.sub(r'\s+([.,!?;:])', r'\1', result)
        result = re.sub(r'\(\s+', '(', result)
        result = re.sub(r'\s+\)', ')', result)
        result = re.sub(r"\s+'\s*", "'", result)
        result = re.sub(r"\s+'", "'", result)
        result = re.sub(r'\s+%\s*', '%', result)
        result = re.sub(r'\$\s+', '$', result)
        result = re.sub(r'(\d)\s+%', r'\1%', result)
        result = re.sub(r'\s+-\s+', '-', result)
        return result
    except:
        return text

def add_contractions(text, intensity):
    if intensity < 20: return text
    contraction_map = {
        'it is': "it's", 'that is': "that's", 'do not': "don't", 'does not': "doesn't",
        'is not': "isn't", 'are not': "aren't", 'was not': "wasn't", 'were not': "weren't",
        'has not': "hasn't", 'have not': "haven't", 'will not': "won't", 'cannot': "can't",
        'could not': "couldn't", 'would not': "wouldn't", 'should not': "shouldn't",
        'there is': "there's", 'what is': "what's",
    }
    words = text.split()
    new_words = []
    i = 0
    while i < len(words):
        if i < len(words) - 1:
            second_word = words[i+1]
            suffix = ''
            while second_word and second_word[-1] in '.,;:!?)':
                suffix = second_word[-1] + suffix
                second_word = second_word[:-1]
            clean_pair = f"{words[i].lower()} {second_word.lower()}"
            if clean_pair in contraction_map and random.random() < (intensity / 100) * 0.3:
                contracted = contraction_map[clean_pair]
                if words[i][0].isupper(): contracted = contracted[0].upper() + contracted[1:]
                new_words.append(contracted + suffix)
                i += 2
                continue
        new_words.append(words[i])
        i += 1
    return ' '.join(new_words)

def translate_text(text, intensity):
    if intensity < 50:
        lang = random.choice(QUALITY_LANGUAGES)
        hop1 = GoogleTranslator(source='en', target=lang).translate(text)
        result = GoogleTranslator(source=lang, target='en').translate(hop1)
    else:
        lang1 = random.choice(STEALTH_LANGUAGES)
        lang2 = random.choice(STEALTH_LANGUAGES)
        try:
            hop1 = GoogleTranslator(source='en', target=lang1).translate(text)
            hop2 = GoogleTranslator(source=lang1, target=lang2).translate(hop1)
            result = GoogleTranslator(source=lang2, target='en').translate(hop2)
        except:
            hop1 = GoogleTranslator(source='en', target='es').translate(text)
            result = GoogleTranslator(source='es', target='en').translate(hop1)
    return result

def humanize_text(text, intensity, tone='academic'):
    if intensity == 0: return text
    text = remove_ai_buzzwords(text, intensity)
    text = remove_ai_phrases(text, intensity)
    text = apply_colloquial_injection(text, intensity)
    text = apply_pos_jitter(text, intensity)
    text = add_contractions(text, intensity)
    text = clean_output(text)
    return text

# ============ UI ============
st.markdown('<p class="main-title">AI Text Paraphraser</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Rewrite text naturally. Bypass AI detection. 100% Free.</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Settings")
    tone = st.selectbox("Tone", ["academic", "journalistic", "conversational"], index=0)
    intensity = st.slider("Stealth Level", 0, 100, 40,
                         help="0=Clean output, 50=Balanced, 100=Max Stealth")
    
    if intensity < 20:
        st.success(f"Mode: Quality ({intensity}%)")
    elif intensity < 50:
        st.info(f"Mode: Balanced ({intensity}%)")
    else:
        st.warning(f"Mode: Stealth ({intensity}%)")
    
    st.divider()
    if st.button("Clear All", use_container_width=True):
        st.session_state.output_text = ""
        st.session_state.last_input = ""
        st.rerun()

# Main area
st.subheader("Input Text")
input_text = st.text_area("Paste your text here", height=250, key="input_text",
                          placeholder="Paste the text you want to paraphrase here...",
                          label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    paraphrase_clicked = st.button("Rewrite Text", type="primary", use_container_width=True)

if paraphrase_clicked:
    if not input_text or not input_text.strip():
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Rewriting your text... This may take a few seconds."):
            try:
                output = translate_text(input_text, intensity)
                output = humanize_text(output, intensity, tone)
                st.session_state.output_text = output
                st.session_state.last_input = input_text
            except Exception as e:
                st.error(f"Translation failed. Please check your internet connection.")
                st.error(f"Error: {str(e)}")

st.divider()
st.subheader("Paraphrased Output")

if st.session_state.output_text:
    st.markdown('<div class="output-box">' + st.session_state.output_text + '</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download as .txt", st.session_state.output_text,
                          file_name="paraphrased_text.txt", mime="text/plain",
                          use_container_width=True)
    with col2:
        if st.button("Copy to Clipboard", use_container_width=True):
            st.write("Text copied! (Use Ctrl+C to copy manually)")
else:
    st.info("Your paraphrased text will appear here.")

st.divider()
st.caption("Free to use. No installation required. Works on phone and desktop.")