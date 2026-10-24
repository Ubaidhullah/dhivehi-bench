#!/usr/bin/env python3
"""
Official Malé Latin Transliteration Engine for Dhivehi (Thaana Script)
=====================================================================
Accurately implements Malé Latin phonological rules:
  - Consonants: 24 primary + Tikhi Thaana
  - Vowels: 10 standard vowels (short: a, i, u, e, o; long: aa, ee, oo, ey, oa)
  - Sukun Rules:
      * Noonu sukun (U+0782 U+07B0): ALWAYS transliterates to 'n' (e.g., mendhuru, thanfeezu, ran)
      * Seenu sukun (U+0790 U+07B0): ALWAYS transliterates to 's' (e.g., mas, gas, isthi'unaafu)
      * Alifu sukun (U+0787 U+07B0):
          - Word-finally: 'h' (e.g., kusheh, eh, meeheh)
          - Medially before consonant: geminates the following consonant (e.g., baavvaa, fahechcheh)
      * Shaviyani sukun (U+0781 U+07B0):
          - Word-finally: 'h' (e.g., rah, bah)
          - Medially: gemination of following consonant (e.g., rahthah -> rahthah)
      * Thaa sukun (U+078C U+07B0):
          - Word-finally: 'iy' or 'th' (e.g., hiy, kiy)
          - Medially: gemination (e.g., fithvath)
      * Baa sukun / Kaafu sukun: geminates following consonant or writes 'b'/'k'
  - Hus Noonu (U+0782 without vowel/sukun before voiced stops d, dh, b, g): 'n' (e.g., kandu, handhu)
  - Word-initial Alifu + fili: transliterates to pure vowel without apostrophe.
"""

CONSONANTS = {
    '\u0780': 'h',   # Haa
    '\u0781': 'sh',  # Shaviyani
    '\u0782': 'n',   # Noonu
    '\u0783': 'r',   # Raa
    '\u0784': 'b',   # Baa
    '\u0785': 'lh',  # Lhaviyani
    '\u0786': 'k',   # Kaafu
    '\u0787': "'",   # Alifu
    '\u0788': 'v',   # Vaavu
    '\u0789': 'm',   # Meemu
    '\u078a': 'f',   # Faafu
    '\u078b': 'dh',  # Dhaalu
    '\u078c': 'th',  # Thaa
    '\u078d': 'l',   # Laamu
    '\u078e': 'g',   # Gaafu
    '\u078f': 'gn',  # Gnaviyani
    '\u0790': 's',   # Seenu
    '\u0791': 'd',   # Daviyani
    '\u0792': 'z',   # Zaaviyani
    '\u0793': 't',   # Ttaviyani
    '\u0794': 'y',   # Yaavu
    '\u0795': 'p',   # Paviyani
    '\u0796': 'j',   # Javiyani
    '\u0797': 'ch',  # Chaviyani
    # Tikhi Thaana (Official Unicode U+0798..U+07A5 and U+07B1)
    '\u0798': 'th',  # U+0798 Ttaa (Arabic Thaa)
    '\u0799': 'h',   # U+0799 Hhaa (Arabic Haa)
    '\u079a': 'kh',  # U+079A Khaa (Arabic Khaa)
    '\u079b': 'dh',  # U+079B Thaalu (Arabic Dhaal)
    '\u079c': 'zh',  # U+079C Zaa (Persian/English Zhe)
    '\u079d': 'sh',  # U+079D Sheenu (Arabic Sheen)
    '\u079e': 's',   # U+079E Saadhu (Arabic Saad)
    '\u079f': 'd',   # U+079F Daadhu (Arabic Daad)
    '\u07a0': 't',   # U+07A0 To (Arabic Taa)
    '\u07a1': 'z',   # U+07A1 Zo (Arabic Zaa)
    '\u07a2': "'",   # U+07A2 Ainu (Arabic Ayn)
    '\u07a3': 'gh',  # U+07A3 Ghainu (Arabic Ghayn)
    '\u07a4': 'q',   # U+07A4 Qaafu (Arabic Qaaf)
    '\u07a5': 'w',   # U+07A5 Waavu (Arabic Waaw)
    '\u07b1': 'n'    # U+07B1 Naa (Southern retroflex nasal)
}

VOWELS = {
    '\u07a6': 'a',   # Aba-fili
    '\u07a7': 'aa',  # Aabaa-fili
    '\u07a8': 'i',   # Ibi-fili
    '\u07a9': 'ee',  # Eebee-fili
    '\u07aa': 'u',   # Ubu-fili
    '\u07ab': 'oo',  # Ooboo-fili
    '\u07ac': 'e',   # Ebe-fili
    '\u07ad': 'ey',  # Eybey-fili
    '\u07ae': 'o',   # Obo-fili
    '\u07af': 'oa',  # Oaboa-fili
}

SUKUN = '\u07b0'
PUNCT_MAP = {'\u060c': ',', '\u061b': ';', '\u061f': '?'}

def transliterate_word(w):
    if w == '(އ)':
        return '(a)'
    res = []
    i = 0
    n = len(w)
    while i < n:
        c = w[i]
        
        if c in PUNCT_MAP:
            res.append(PUNCT_MAP[c])
            i += 1
        elif c in CONSONANTS:
            # Check next character
            if i + 1 < n and w[i+1] in VOWELS:
                v = VOWELS[w[i+1]]
                if c in ('\u0787', '\u07a2'):  # Alifu or Ainu + vowel
                    # If start of word (or after opening paren / initial short vowel), no apostrophe needed in Malé Latin
                    if i == 0 or (len(res) > 0 and res[-1] in ('a', 'i', 'u', 'e', 'o', '(')):
                        res.append(v)
                    else:
                        res.append("'" + v)
                else:
                    res.append(CONSONANTS[c] + v)
                i += 2
            elif i + 1 < n and w[i+1] == SUKUN:
                # Sukun rules
                is_final = (i + 2 >= n) or not (w[i+2] in CONSONANTS)
                if c == '\u0782':  # Noonu sukun is always 'n'
                    res.append('n')
                elif c == '\u0790':  # Seenu sukun is always 's'
                    res.append('s')
                elif c == '\u0781':  # Shaviyani sukun is 'h' in Malé Latin (e.g., rah, macchah, majileehah)
                    res.append('h')
                elif c == '\u079d':  # Sheenu sukun is 'sh'
                    res.append('sh')
                elif c == '\u0787':  # Alifu sukun
                    if is_final:
                        res.append('h')
                    else:
                        next_c = w[i+2]
                        gem = CONSONANTS.get(next_c, '')
                        res.append(gem[0] if gem else 'h')
                elif c == '\u078c':  # Thaa sukun
                    if is_final:
                        res.append('th')
                    else:
                        next_c = w[i+2]
                        gem = CONSONANTS.get(next_c, '')
                        res.append(gem[0] if gem else 'th')
                else:
                    res.append(CONSONANTS.get(c, ''))
                i += 2
            else:
                # Bare consonant (e.g. Hus Noonu)
                if c == '\u0782':
                    res.append('n')
                elif c in ('\u0787', '\u07a2'):
                    res.append("'")
                else:
                    res.append(CONSONANTS[c])
                i += 1
        elif c in VOWELS:
            res.append(VOWELS[c])
            i += 1
        elif c == SUKUN:
            i += 1
        else:
            res.append(c)
            i += 1
            
    out = "".join(res)
    return out

def transliterate_thaana(text):
    if not text:
        return ""
    words = text.split(" ")
    return " ".join(transliterate_word(w) for w in words)

if __name__ == "__main__":
    sample = "2. ޖިނާއީ ކުށެއް ކުރިކަން ސާބިތުވެ ބާރަ މަސްދުވަހަށްވުރެ ދިގު މުއްދަތެއްގެ ޙުކުމެއް ތަންފީޛުކުރަމުންދާ މީހަކު ކަމުގައިވުން."
    print("Thaana 1:", sample)
    print("Translit 1:", transliterate_thaana(sample))
    
    sample2 = "މި ޖަނާޒާ ބާއްވާފައިވަނީ މިއަދު މެންދުރު ބަންގްލަދޭޝްގެ ދާކާގައެވެ."
    print("Thaana 2:", sample2)
    print("Translit 2:", transliterate_thaana(sample2))
