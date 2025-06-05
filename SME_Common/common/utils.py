import re
import os

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0:1]:
        return _pathname
    else:
        dir = os.path.dirname(__file__)
        return os.path.join(f"{dir}/..", _pathname)

# Utility function to create full file paths
def is_file_in_use(file_path):
    try:
        # Attempt to open the file in 'r+' mode (read/write mode)
        with open(file_path, 'r+'):
            result = 'OK'
    except PermissionError:
        # 'PermissionError' indicates the file is in use by another process
        print(f"The file {file_path} is in use.")
        result = 'IN_USE'
    except FileNotFoundError:
        # If the file does not exist, create it
        print(f"The file {file_path} does not exist. Creating new file...")
        try:
            # Open the file in 'w+' mode to create it if it doesn't exist
            with open(file_path, 'w+') as new_file:
                pass # Creating the file
            result = 'CREATED'
            print(f"File {file_path} has been created.")
        except Exception as e:
            print(f"Error while creating file: {e}")
            result = 'ERROR_CREATING_FILE'
    return result


    term = re.sub(r'[!"#$%&\'()=~|\\^\-@`\[\]{}:;+*/?,.<>\_]', '', term)

    def abbreviate_word(word):
        if len(word) <= 3:
            return word  # already short
        chars = [word[0]]  # keep first character
        # include non-vowels from rest, skipping first vowel if it's the first char
        first_vowel_found = word[0] in vowels
        for c in word[1:]:
            if c.lower() not in vowels:
                chars.append(c)
            elif not first_vowel_found:
                chars.append(c)
                first_vowel_found = True
        abbr = ''.join(chars)
        # If abbreviation is still too long, remove all vowels
        if len(abbr) >= 6:
            # Keep the first vowel
            first_vowel_index = next(
                (i for i, c in enumerate(abbr) if c.lower() in vowels), None
            )
            if first_vowel_index is not None:
                first_vowel = abbr[first_vowel_index]
                abbr_chars = [
                    abbr[i]
                    for i in range(len(abbr))
                    if abbr[i].lower() not in vowels or i == first_vowel_index
                ]
                abbr = "".join(abbr_chars)
                # If the first character is a vowel and the abbreviation is still long,
                # trim to the first 5 characters and append the last character to shorten
                # while preserving the start and end of the word
                if abbr and abbr[0].lower() in vowels and len(abbr) > 5:
                    abbr = abbr[:5] + abbr[-1]
        # Final fallback: truncate if still too long
        return abbr if len(abbr) < len(word) else word # must be shorter

def abbreviate_term(term):
    """
    Abbreviates each word in the input term according to the following rules:

    - Remove common stop_words (e.g., to, with, on, of, etc.).
    - Remove any symbol characters: !"#$%&'()=~|\^-@`[]{}:;+*/?.,<>\_
    - Capitalize the first letter of each remaining word.
    - Keep the first vowel of each word, remove all other vowels.
    - If the abbreviation is 6 characters or more:
        - Keep only the first vowel and remove the rest.
        - If the first character is a vowel and the result is still long,
        remove the 5th character (index 4) to shorten further.
    - Ensure the abbreviated word is shorter than the original word.
    - Words of length 3 or less are returned unchanged.
    """
    stop_words = {
        'a', 'an', 'the',
        'to', 'with', 'on', 'of', 'in', 'for', 'at', 'by', 'from', 'as',
        'about', 'into', 'over', 'after', 'under', 'above', 'below'
    }
    vowels = 'aeiouAEIOU'
    # Remove symbols
    term = re.sub(r'[!"#$%&\'()=~|\\^\-@`\[\]{}:;+*/?,.<>\_]', '', term)

    def abbreviate_word(word):
        if len(word) <= 3:
            return word  # already short
        chars = [word[0]]  # keep first character
        # include non-vowels from rest, skipping first vowel if it's the first char
        first_vowel_found = word[0] in vowels
        for c in word[1:]:
            if c.lower() not in vowels:
                chars.append(c)
            elif not first_vowel_found:
                chars.append(c)
                first_vowel_found = True
        abbr = ''.join(chars)
        # If abbreviation is still too long, remove all vowels
        if len(abbr) >= 6:
            # Keep the first vowel
            first_vowel_index = next(
                (i for i, c in enumerate(abbr) if c.lower() in vowels), None
            )
            if first_vowel_index is not None:
                first_vowel = abbr[first_vowel_index]
                abbr_chars = [
                    abbr[i]
                    for i in range(len(abbr))
                    if abbr[i].lower() not in vowels or i == first_vowel_index
                ]
                abbr = "".join(abbr_chars)
                # If the first character is a vowel and the abbreviation is still long,
                # trim to the first 5 characters and append the last character to shorten
                # while preserving the start and end of the word
                if abbr and abbr[0].lower() in vowels and len(abbr) > 5:
                    abbr = abbr[:5] + abbr[-1]
        # Final fallback: truncate if still too long
        return abbr if len(abbr) < len(word) else word # must be shorter
    # Tokenize and filter stop_words
    words = re.findall(r'\w+', term)
    filtered = [w.capitalize() for w in words if w.lower() not in stop_words]
    # Abbreviate remaining words
    abbreviated = [abbreviate_word(w) for w in filtered]
    return ' '.join(abbreviated)

def LC3(term):
    """
    Lower camel case converter (e.g., 'Entity Phone Number' → 'entityPhoneNumber')
    """
    parts = re.split(r'\s+', term.strip())
    return parts[0].lower() + ''.join(p.title() for p in parts[1:])

def split_camel_case(identifier):
    """
    Split camelCase or CamelCase into a list of words,
    allowing numbers and symbols to remain within each chunk.
    Splitting occurs at capital letters.
    """
    term = re.findall(r'[^A-Z]*[A-Z][^A-Z]*', identifier)
    if not term:
        term = [identifier]
    return term

# lower camel case concatenate
def LC3(term):
    if not term:
        return ''
    terms = term.split(' ')
    name = ''
    for i in range(len(terms)):
        if i == 0:
            if 'TAX' == terms[i]:
                name += terms[i].lower()
            elif len(terms[i]) > 0:
                name += terms[i][0].lower() + terms[i][1:]
        else:
            name += terms[i][0].upper() + terms[i][1:]
    return name


def titleCase(text):
    text = text.replace('ID', 'Identification Identifier')
    # ChatGPT 2023-04-10 modified by Nobu
    # Example Camel case string
    camel_case_str = text # "exampleCamelCaseString"
    # Use regular expression to split the string at each capital letter
    split_str = re.findall('[A-Z][a-z]*[_]?', camel_case_str)
    # Join the split string with a space and capitalize each word
    title_case_str = ' '.join([x.capitalize() for x in split_str])
    title_case_str = title_case_str.replace('Identification Identifier','ID')
    return title_case_str


# snake concatenate
def SC(term):
    if not term:
        return ''
    terms = term.split(' ')
    name = '_'.join(terms)
    return name


def normalize_text(text):
    # Remove (choice) or (sequence), including preceding space
    text = re.sub(r'\s*\((choice|sequence)\)', '', text, flags=re.IGNORECASE)
    # Replace /, _, -, (, ) with spaces
    text = re.sub(r'[\/_\-\(\)]', ' ', text)
    # Replace multiple spaces with a single space and trim leading/trailing spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text