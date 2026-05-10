import streamlit as st
from deep_translator import GoogleTranslator
import re
import random
import unicodedata
import threading


# ============ TEXT CLEANING ============
def strip_unicode_watermarks(text):
    """Remove hidden Unicode characters and AI watermarks."""
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064\u2066\u2067\u2068\u2069\u206a\u206b\u206c\u206d\u206e\u206f\uFEFF]', '', text)
    text = re.sub(r'[\uFE00-\uFE0F]', '', text)
    text = re.sub(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u0080-\u009f]', '', text)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    return text


def remove_em_dashes(text):
    """Replace em dashes with natural alternatives."""
    text = re.sub(r'\s*—\s*', lambda m: random.choice([', ', '. ', '; ', ': ']), text)
    text = re.sub(r'\s*–\s*', lambda m: random.choice([', ', '. ', ' - ']), text)
    text = re.sub(r'\s*--\s*', lambda m: random.choice([', ', '. ', '; ']), text)
    text = re.sub(r'\s*---\s*', '. ', text)
    return text


def remove_ai_markers(text):
    """Remove AI intro/outro phrases."""
    ai_intros = [
        r'^Certainly[!,.]?\s*', r'^Sure[!,.]?\s*', r'^Of course[!,.]?\s*',
        r'^I\'d be happy to\s*', r'^Here is the\s*', r'^Here are the\s*',
        r'^Let me\s*', r'^I hope this\s*',
    ]
    for pattern in ai_intros:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s*Let me know if.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Feel free to.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*I hope this helps.*$', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def clean_output(text):
    """Master cleaning function."""
    text = strip_unicode_watermarks(text)
    text = remove_em_dashes(text)
    text = remove_ai_markers(text)
    text = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2010-\u2015\u2018-\u2019\u201c-\u201d\u2020-\u2022\u2026\u2030-\u2033\u2039-\u203a\u2044\u20AC]', '', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', text)
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'\.{2}', '.', text)
    return text.strip()


# ============ TRANSLATION ENGINE ============
def translate_text(text, primary_lang, intensity):
    """Multi-hop translation based on settings."""
    secondary_lang = 'fr' if primary_lang == 'es' else 'es'
    
    if intensity < 50:
        hop1 = GoogleTranslator(source='en', target=primary_lang).translate(text)
        result = GoogleTranslator(source=primary_lang, target='en').translate(hop1)
    else:
        hop1 = GoogleTranslator(source='en', target=primary_lang).translate(text)
        hop2 = GoogleTranslator(source=primary_lang, target=secondary_lang).translate(hop1)
        result = GoogleTranslator(source=secondary_lang, target='en').translate(hop2)
    
    return result


# ============ HUMANIZATION ============
def humanize_text(text, intensity):
    """Add human-like imperfections."""
    if intensity == 0:
        return text
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    humanized_sentences = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        words = sentence.split()
        if not words:
            humanized_sentences.append(sentence)
            continue
        
        # Informal starters
        if len(words) > 8 and random.random() < (intensity / 100) * 0.3:
            informal_starts = [
                "So, ", "Now, ", "Basically, ", "In short, ",
                "Here is the thing: ", "If you think about it, ", "It turns out ",
                "Interestingly, ", "As it happens, ",
                "Look, ", "The reality is, "
            ]
            sentence = random.choice(informal_starts) + sentence[0].lower() + sentence[1:]
        
        # Casual word replacements
        formal_to_casual = {
            'approximately': 'about', 'exceeding': 'more than', 'annually': 'each year',
            'procurement': 'sourcing', 'emissions': 'output', 'significantly': 'a lot',
            'comparable': 'similar', 'mandate': 'requirement', 'objectives': 'goals',
            'reducing': 'cutting down on', 'lifecycle': 'full-life', 'transportation': 'transport',
            'subsequently': 'then', 'nevertheless': 'still', 'additional': 'extra',
            'characterized': 'described', 'methodology': 'approach', 'utilizes': 'uses',
            'demonstrates': 'shows', 'sufficient': 'enough',
            'concerning': 'on', 'therefore': 'so', 'however': 'but',
            'furthermore': 'also', 'consequently': 'so', 'evapotranspirated': 'released',
            'supplemented': 'backed up with', 'explicitly': 'clearly', 'tenable': 'defensible',
            'distinguishes': 'tells apart', 'reflects': 'shows', 'rekindled': 'brought back',
            'governance': 'management', 'depletion': 'loss', 'allocations': 'supplies',
            'peer-reviewed': 'published', 'descriptors': 'terms',
            'accounting': 'calculations', 'figure': 'number', 'narrative': 'summary',
            'virtual': 'estimated',
        }
        
        for formal, casual in formal_to_casual.items():
            if formal in sentence.lower() and random.random() < (intensity / 100) * 0.6:
                sentence = re.sub(formal, casual, sentence, count=1, flags=re.IGNORECASE)
        
        # Sentence splitting
        if len(words) > 15 and random.random() < (intensity / 100) * 0.45:
            split_point = len(words) // 2 + random.randint(-4, 4)
            part1 = ' '.join(words[:split_point])
            part2 = ' '.join(words[split_point:])
            if part2:
                if random.random() < 0.3:
                    part2 = part2.lower()
                else:
                    part2 = part2[0].upper() + part2[1:]
            humanized_sentences.append(part1.rstrip() + '.')
            if part2:
                humanized_sentences.append(part2)
            continue
        
        # Fillers
        if len(words) > 10 and random.random() < (intensity / 100) * 0.3:
            fillers = [
                "essentially,", "basically,", "in effect,", "more or less,",
                "you know,", "in other words,", "put simply,", "for the most part,"
            ]
            insertion_point = random.randint(len(words)//3, 2*len(words)//3)
            words.insert(insertion_point, random.choice(fillers))
            sentence = ' '.join(words)
        
        # Conjunction starts
        if random.random() < (intensity / 100) * 0.3 and len(humanized_sentences) > 0:
            conjunctions = ["And ", "But ", "So ", "Yet ", "Because ", "While "]
            sentence = random.choice(conjunctions) + sentence[0].lower() + sentence[1:]
        
        humanized_sentences.append(sentence)
    
    result = ' '.join(humanized_sentences)
    
    # Varied punctuation (no em dashes)
    result = re.sub(r'\.\s+([A-Z])',
                    lambda m: ('... ' + m.group(1)) if random.random() < (intensity / 100) * 0.1
                    else '. ' + m.group(1),
                    result)
    
    # Semicolon merging
    sentences = re.split(r'(?<=[.!?])\s+', result)
    merged = []
    skip_next = False
    for i in range(len(sentences)):
        if skip_next:
            skip_next = False
            continue
        if (i < len(sentences) - 1 
            and len(sentences[i].split()) < 12 
            and len(sentences[i+1].split()) < 12
            and random.random() < (intensity / 100) * 0.2):
            merged.append(sentences[i].rstrip() + '; ' + sentences[i+1][0].lower() + sentences[i+1][1:])
            skip_next = True
        else:
            merged.append(sentences[i])
    result = ' '.join(merged)
    
    return result


def add_personal_asides(text, intensity):
    """Add conversational asides (no em dashes)."""
    if intensity < 40 or random.random() > (intensity / 100):
        return text
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    asides = [
        "and this matters because",
        "which is worth paying attention to",
        "something often overlooked",
        "and that is not a small detail",
        "a point that deserves attention",
        "worth keeping in mind",
    ]
    
    if len(sentences) > 2:
        num_asides = 1 if intensity < 70 else 2
        used_indices = set()
        
        for _ in range(num_asides):
            available = [i for i in range(len(sentences)) if i not in used_indices]
            if not available:
                break
            idx = random.choice(available)
            used_indices.add(idx)
            words = sentences[idx].split()
            if len(words) > 10:
                insert_pos = len(words) // 2 + random.randint(-2, 2)
                aside = random.choice(asides)
                words.insert(insert_pos, ', ' + aside + ',')
                sentences[idx] = ' '.join(words)
    
    return ' '.join(sentences)


def introduce_typos(text, intensity):
    """Rare typos at high intensity."""
    if intensity < 80:
        return text
    
    words = text.split()
    num_typos = max(1, int(len(words) * (intensity / 100) * 0.02))
    
    for _ in range(num_typos):
        idx = random.randint(0, len(words) - 1)
        word = words[idx]
        if len(word) > 4 and word.isalpha():
            pos = random.randint(0, len(word) - 2)
            word_list = list(word)
            word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
            words[idx] = ''.join(word_list)
    
    return ' '.join(words)


# ============ MAIN PROCESSING ============
def process_text(input_text, primary_lang, intensity, sentence_mode):
    """Process text with all transformations."""
    lang_name = "Spanish" if primary_lang == 'es' else "French"
    
    if not sentence_mode:
        # All at once
        result = translate_text(input_text, primary_lang, intensity)
        result = humanize_text(result, intensity)
        result = add_personal_asides(result, intensity)
        result = introduce_typos(result, intensity)
        result = clean_output(result)
        return result, f"Done! | {lang_name}"
    else:
        # Sentence by sentence
        sentences = re.split(r'(?<=[.!?])\s+', input_text)
        sentences = [s for s in sentences if s.strip()]
        
        if intensity > 40 and len(sentences) >= 3:
            num_swaps = max(1, int(len(sentences) * (intensity / 100) * 0.15))
            for _ in range(num_swaps):
                idx = random.randint(0, len(sentences) - 2)
                if len(sentences[idx]) > 20 and len(sentences[idx+1]) > 20 and random.random() < 0.4:
                    sentences[idx], sentences[idx+1] = sentences[idx+1], sentences[idx]
        
        paraphrased_sentences = []
        for i, sentence in enumerate(sentences):
            result = translate_text(sentence, primary_lang, intensity)
            result = humanize_text(result, intensity)
            result = add_personal_asides(result, intensity)
            result = introduce_typos(result, intensity)
            result = clean_output(result)
            paraphrased_sentences.append(result)
        
        full_result = ' '.join(paraphrased_sentences)
        full_result = clean_output(full_result)
        return full_result, f"Done! {len(sentences)} sentences | {lang_name}"


# ============ STREAMLIT UI ============
st.set_page_config(
    page_title="AI Text Paraphraser By S.Khan",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .output-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        min-height: 200px;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-title">AI Text Paraphraser By S.Khan</p>', unsafe_allow_html=True)
st.caption("Rewrite text naturally. No command line needed.")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Language
    language = st.selectbox(
        "Primary Language",
        ["Spanish", "French"],
        index=0,
        help="Spanish gives more structural changes. French preserves more terminology."
    )
    
    # Intensity
    intensity = st.slider(
        "Stealth Level",
        min_value=0,
        max_value=100,
        value=40,
        help="0 = Clean output, 100 = Maximum AI detection bypass"
    )
    
    # Intensity label
    if intensity < 20:
        st.success(f"Mode: Quality ({intensity}%)")
    elif intensity < 50:
        st.info(f"Mode: Balanced ({intensity}%)")
    elif intensity < 80:
        st.warning(f"Mode: Stealth ({intensity}%)")
    else:
        st.error(f"Mode: Max Stealth ({intensity}%)")
    
    # Processing mode
    sentence_mode = st.checkbox(
        "Sentence-by-Sentence mode",
        value=False,
        help="Process each sentence separately for more variation"
    )
    
    st.divider()
    
    # Clear button
    if st.button("Clear All", use_container_width=True):
        st.session_state.input_text = ""
        st.session_state.output_text = ""
        st.rerun()

# Main area - Input
st.subheader("Input Text")
input_text = st.text_area(
    "Paste your text here",
    height=250,
    key="input_text",
    placeholder="Paste the text you want to paraphrase here...",
    label_visibility="collapsed"
)

# Paraphrase button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    paraphrase_clicked = st.button(
        "Rewrite Text",
        type="primary",
        use_container_width=True
    )

# Processing
if paraphrase_clicked:
    if not input_text or not input_text.strip():
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Rewriting your text... This may take a few seconds."):
            try:
                lang_code = 'es' if language == 'Spanish' else 'fr'
                output, status = process_text(
                    input_text, lang_code, intensity, sentence_mode
                )
                st.session_state.output_text = output
                st.session_state.status = status
            except Exception as e:
                st.error(f"Translation failed. Please check your internet connection.")
                st.error(f"Error details: {str(e)}")

# Output area
st.divider()
st.subheader("Paraphrased Output")

if "output_text" in st.session_state and st.session_state.output_text:
    st.success(st.session_state.get("status", "Done!"))
    st.markdown('<div class="output-box">' + st.session_state.output_text + '</div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Copy to Clipboard", use_container_width=True):
            # JavaScript to copy
            st.markdown(f"""
            <script>
                navigator.clipboard.writeText({st.session_state.output_text!r});
            </script>
            """, unsafe_allow_html=True)
            st.toast("Copied!")
    
    with col2:
        # Download as text file
        st.download_button(
            label="Download as .txt",
            data=st.session_state.output_text,
            file_name="paraphrased_text.txt",
            mime="text/plain",
            use_container_width=True
        )
else:
    st.info("Your paraphrased text will appear here.")

# Footer
st.divider()
st.caption("Free to use. No installation required. Works on phone and desktop.")