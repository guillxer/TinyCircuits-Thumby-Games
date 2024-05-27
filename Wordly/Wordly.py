import random
from thumbyGraphics import display
from thumbySprite import Sprite
import thumbyButton as buttons
from thumbyAudio import audio
import time
import thumby

random.seed(time.ticks_ms())

_recent_key = None
_recent_words = set()

def simple_hash(word):
    hash_val = 0
    for char in word:
        hash_val = (hash_val * 31 + ord(char)) % 256
    return f"{hash_val:02x}"

def load_words_by_key(file_path, key):
    global _recent_key, _recent_words
    if key == _recent_key:
        return _recent_words
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith(key):
                _, words_str = line.strip().split(':', 1)
                _recent_key = key
                _recent_words = set(words_str.split(','))
                return _recent_words
    _recent_key = key
    _recent_words = set()
    return _recent_words

words_file_path = '/Games/Wordly/words.txt'
easy_words_file_path = '/Games/Wordly/easywords.txt'

def select_random_key():
    return f"{random.randint(0, 255):02x}"

def select_random_word(file_path):
    key = select_random_key()
    words_set = load_words_by_key(file_path, key)
    if words_set:
        return random.choice(list(words_set))
    return None

def is_valid_word(word):
    if not word:
        return False
    key = simple_hash(word)
    words_set = load_words_by_key(words_file_path, key)
    return word in words_set

thumby.saveData.setName("Wordly")
stats = {f"attempts_{i}": thumby.saveData.getItem(f"attempts_{i}") if thumby.saveData.hasItem(f"attempts_{i}") else 0 for i in range(1, 7)}
stats["fails"] = thumby.saveData.getItem("fails") if thumby.saveData.hasItem("fails") else 0

def save_stats():
    for key in stats:
        thumby.saveData.setItem(key, stats[key])
    thumby.saveData.save()

def update_stats(attempts):
    if 1 <= attempts <= 6:
        stats[f"attempts_{attempts}"] += 1
    else:
        stats["fails"] += 1
    save_stats()

def show_stats_screen():
    display.fill(0)
    display.drawText("Stats:", 0, 0, 1)
    chart_top, chart_bottom, chart_height, chart_width, bar_spacing = 10, 32, 22, 58, 2
    num_bars, max_value = len(stats), max(stats.values())
    bar_width = (chart_width - (num_bars - 1) * bar_spacing) // num_bars
    stat_keys, labels = ['attempts_1', 'attempts_2', 'attempts_3', 'attempts_4', 'attempts_5', 'attempts_6', 'fails'], ["1", "2", "3", "4", "5", "6", "X"]
    steps = [0, max_value // 2, max_value] if max_value > 1 else [0, 1]
    for step in steps:
        if step <= max_value:
            y = chart_bottom - int((step / max_value) * chart_height)
            display.drawLine(5, y, 7, y, 1)
            display.drawText(str(step), 0, y - 3, 1)
    display.drawLine(7, chart_bottom, 72, chart_bottom, 1)
    for i, key in enumerate(stat_keys):
        value, bar_height = stats[key], int((stats[key] / max_value) * chart_height) if max_value > 0 else 0
        x, y = 9 + i * (bar_width + bar_spacing), chart_bottom - bar_height
        display.drawFilledRectangle(x, y, bar_width, bar_height, 1)
        display.drawText(labels[i], x + (bar_width - 4) // 2, chart_bottom + 1, 1)
    display.update()
    while not buttons.buttonA.justPressed() and not buttons.buttonB.justPressed():
        buttons.buttonA.update()
        buttons.buttonB.update()

ALPHABET, MAX_TRIES, WORD_LENGTH, SCREEN_WIDTH = 'abcdefghijklmnopqrstuvwxyz', 6, 5, 72
tries, incorrect_letters, current_guess = [], set(), ""
selector_x, selector_y, view_offset = 0, 0, 0
word_to_guess = select_random_word(easy_words_file_path)
Selector = Sprite(9, 9, bytearray([198,1,1,0,0,0,1,1,198, 0,1,1,0,0,0,1,1,0]), 0, 0)
Selector_mask = Sprite(9, 9, bytearray([199,1,1,0,0,0,1,1,199, 1,1,1,0,0,0,1,1,1]), 0, 0)

def draw_game():
    display.fill(0)
    draw_slider()
    y = 0
    combined_list = tries + [current_guess]
    for i in range(view_offset, min(view_offset + 2, len(combined_list))):
        draw_word(i + 1, combined_list[i], y * 8)
        y += 1
    draw_keyboard()
    draw_selector()
    display.update()

def draw_word(guess_number, word, y, shownum=True):
    if shownum:
        display.drawText(f"{guess_number}:", 0, y, 1)
    x_offset = len(f"{guess_number}:") * 8
    for i, letter in enumerate(word[:WORD_LENGTH]):
        x = x_offset + i * 8
        if len(word) > WORD_LENGTH and word[WORD_LENGTH + i] == '2':
            display.drawFilledRectangle(x - 1, y, 7, 8, 1)
            display.drawText(letter, x, y, 0)
        elif len(word) > WORD_LENGTH and word[WORD_LENGTH + i] == '1':
            display.drawText(letter, x, y, 1)
            display.drawLine(x, y + 7, x + 5, y + 7, 1)
        else:
            display.drawText(letter, x, y, 1)

def draw_keyboard():
    for row in range(3):
        for col in range(9):
            index = row * 9 + col
            if index < len(ALPHABET):
                letter = ALPHABET[index]
                if letter not in incorrect_letters:
                    display.drawText(letter, col * 8+2, 17 + row * 8, 1)

def draw_selector():
    Selector.x, Selector.y = selector_x * 8, 17 + selector_y * 8
    display.drawSpriteWithMask(Selector, Selector_mask)

def draw_slider():
    total_rows = len(tries) + 1
    if total_rows > 2:
        display.drawLine(SCREEN_WIDTH - 2, 0, SCREEN_WIDTH - 2, 15, 1)
        slider_height = max(2, 15 * 2 // total_rows)
        max_offset = total_rows - 2
        slider_y = (16 - slider_height) * view_offset // max_offset if max_offset > 0 else 0
        slider_y = min(slider_y, 15 - slider_height)
        display.drawFilledRectangle(SCREEN_WIDTH - 3, slider_y, 2, slider_height, 1)
        display.drawRectangle(SCREEN_WIDTH - 4, slider_y - 1, 4, slider_height + 2, 1)

def evaluate_guess(guess):
    feedback = ["0"] * WORD_LENGTH
    target_letter_count = {letter: word_to_guess.count(letter) for letter in word_to_guess}
    for i, letter in enumerate(guess):
        if letter == word_to_guess[i]:
            feedback[i] = "2"
            target_letter_count[letter] -= 1
    for i, letter in enumerate(guess):
        if feedback[i] == "0" and target_letter_count.get(letter, 0) > 0:
            feedback[i] = "1"
            target_letter_count[letter] -= 1
    for letter in set(guess):
        if all(feedback[i] == "0" for i in range(WORD_LENGTH) if guess[i] == letter):
            incorrect_letters.add(letter)
    return guess + "".join(feedback)

def handle_input():
    global current_guess, selector_x, selector_y, view_offset
    combined_list_length = len(tries) + 1
    if buttons.buttonL.pressed():
        selector_x = selector_x - 1 if selector_x > 0 else 8
        time.sleep_ms(150)
    if buttons.buttonR.pressed():
        selector_x = selector_x + 1 if selector_x < 8 else 0
        time.sleep_ms(150)
    if buttons.buttonU.pressed():
        if selector_y == 0 and view_offset > 0:
            view_offset -= 1
        elif selector_y > 0:
            selector_y -= 1
        time.sleep_ms(150)
    if buttons.buttonD.pressed():
        if selector_y == 2 and view_offset + 2 < combined_list_length:
            view_offset += 1
        elif selector_y < 2:
            selector_y += 1
        time.sleep_ms(150)
    letter_index = selector_y * 9 + selector_x
    if buttons.buttonA.justPressed() and letter_index < len(ALPHABET):
        letter = ALPHABET[letter_index]
        if letter not in incorrect_letters:
            current_guess += letter
            audio.playBlocking(1000, 100)
            audio.playBlocking(1250, 100)
            view_offset = max(0, combined_list_length - 2)
    if buttons.buttonB.justPressed() and current_guess:
        current_guess = current_guess[:-1]
        audio.playBlocking(500, 50)
        view_offset = max(0, combined_list_length - 2)

def play_audio_sequence(sequence):
    for freq, duration in sequence:
        audio.playBlocking(freq, duration)

def show_message_and_play_audio(message_lines, audio_sequence, rectangle_coords=(0, 16, 72, 24)):
    display.drawFilledRectangle(*rectangle_coords, 0)
    for i, line in enumerate(message_lines):
        display.drawText(line, 0, 20 + i * 10, 1)
    display.update()
    play_audio_sequence(audio_sequence)

win_audio_sequence = [(1000, 100), (1250, 100), (1500, 100), (2000, 200)]
game_over_audio_sequence = [(2000, 200)]
unlisted_word_audio_sequence = [(2000, 100), (1000, 100), (1500, 100), (1000, 100), (1250, 100), (1000, 200)]

display.setFPS(30)
WORD_LENGTH = 6
words = ["thumby000002", "slowly001122", "wordly222222"]
y_position = 10
display.fill(0)
for word in words:
    draw_word(1, word, y_position, shownum=False)
    y_position += 10
WORD_LENGTH = 5
display.update()
play_audio_sequence(win_audio_sequence)

while True:
    if buttons.buttonA.justPressed():
        break
    elif buttons.buttonB.justPressed():
        show_stats_screen()

play_audio_sequence(win_audio_sequence)

while True:
    handle_input()
    draw_game()
    if len(current_guess) == WORD_LENGTH:
        if is_valid_word(current_guess):
            evaluated_guess = evaluate_guess(current_guess)
            tries.append(evaluated_guess)
            if current_guess == word_to_guess:
                update_stats(len(tries))
                current_guess = ""
                draw_game()
                show_message_and_play_audio(["You Win!", f"Score: {len(tries)}"], win_audio_sequence)
                time.sleep(2)
                break
            if len(tries) >= MAX_TRIES:
                update_stats(0)
                draw_game()
                show_message_and_play_audio(["Game over!", f"it was {word_to_guess}"], game_over_audio_sequence)
                time.sleep(2)
                break
            audio.playBlocking(1500, 100)
            current_guess = ""
            if len(tries) > 2:
                view_offset = len(tries) - 2
        else:
            show_message_and_play_audio(["Unlisted", "word"], unlisted_word_audio_sequence)
            time.sleep(1)
            current_guess = ""

show_stats_screen()