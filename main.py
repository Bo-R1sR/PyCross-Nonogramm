import _thread
import random
import sqlite3
import time
from tkinter import *

import simpleaudio as sa

# outsource riddles to seperate file
import riddles

# assign values from seperate file
text_riddle = riddles.text_riddle
pictures_riddle = riddles.weitere_bilder
riddle_0 = riddles.riddle_0

# number play field
NUMBER_ROWS = NUMBER_COLUMNS = 10
# set to 1 for display of frame borders
FRAME_BORDER = 0
# button settings
BUTTON_WIDTH = 20
BUTTON_FONT = 'Verdana 10'
BUTTON_RELIEF = 'groove'
BUTTON_BORDER = 3
# start values
elapsed_time = 0
start_time = 0
is_running = False
is_sound_muted = False
is_music_muted = False
is_restarted = False
is_paused = False
# sounds
music = "sounds/musik.wav"
music_wav_obj = sa.WaveObject.from_wave_file(music)
music_play_obj = music_wav_obj.play()
music_play_obj.stop()
click = "sounds/click.wav"
click_wav_obj = sa.WaveObject.from_wave_file(click)
error = "sounds/error.wav"
error_wav_obj = sa.WaveObject.from_wave_file(error)
win = "sounds/win.wav"
win_wav_obj = sa.WaveObject.from_wave_file(win)
# database
db = sqlite3.connect('bestenliste.sqlite')
cursor = db.cursor()

minutes_str = ""
seconds_str = ""


# executed when button "Spiel starten" is pressed
def start_game():
    initialize_new_game()
    help_button.config(state="normal")
    pause_button.config(state="normal")
    start_timer()

    global is_running
    is_running = True
    if is_restarted:
        start_button.configure(text="Spiel starten")
    else:
        start_button.configure(text="Spiel neu starten")


# helper function to calculate labels for rows
def calculate_row_labels():
    """
    depending on the marked fields in the riddle the label will be calculated.
    It will loop through the rows and a sequence of [1, 0, 0, 0, 0, 0, 0, 1, 0, 1] will lead
    to a label of 1 1 1
    """
    labels = []
    array_row = []
    for ii in range(NUMBER_ROWS):
        summe_row = 0
        for jj in range(NUMBER_COLUMNS):
            summe_row += riddle_0[ii][jj]
            if (riddle_0[ii][jj] == 0 or jj == NUMBER_COLUMNS - 1) and summe_row != 0:
                array_row.append(summe_row)
                summe_row = 0
        new_array = array_row.copy()
        if not new_array:
            new_array.append(0)
        labels.append(new_array)
        array_row.clear()
    return labels


# helper function to calculate labels for columns
def calculate_column_labels():
    array_column = []
    labels = []
    for ii in range(NUMBER_COLUMNS):
        summe_column = 0
        for jj in range(NUMBER_ROWS):
            summe_column += riddle_0[jj][ii]
            if (riddle_0[jj][ii] == 0 or jj == NUMBER_ROWS - 1) and summe_column != 0:
                array_column.append(summe_column)
                summe_column = 0
        new_array = array_column.copy()
        if not new_array:
            new_array.append(0)
        labels.append(new_array)
        array_column.clear()
    return labels


# executed when button "Spiel pausieren" is pressed
def pause_game():
    global is_paused
    if not is_paused:
        is_paused = True
        pause_button.configure(text="Spiel fortsetzen")
        help_button.config(state="disabled")
    else:
        is_paused = False
        start_timer()
        pause_button.configure(text="Spiel pausieren")
        help_button.config(state="normal")
        error_label.configure(text="")


# executed when button "Hilfe" is pressed
def help_game():
    if not is_paused and is_running:
        hilfe_felder = []
        # check which fields are currently wrong and save them
        for ii in range(NUMBER_ROWS):
            for jj in range(NUMBER_COLUMNS):
                if (riddle_0[ii][jj] == 0 and all_buttons[ii][jj].cget("background") == "white") or (
                        riddle_0[ii][jj] == 1 and all_buttons[ii][jj].cget("background") == "black"):
                    pass
                else:
                    hilfe_felder.append([ii, jj])

        # if there are any errors then select one randomly and show the correct color for this field on the screen
        if hilfe_felder:
            rand_index = random.randrange(len(hilfe_felder))
            x, y = hilfe_felder[rand_index]
            change_color(all_buttons[x][y])
            # increase time by 15
            global elapsed_time
            elapsed_time += 15


# executed when button "Spiel lösen" is pressed
def solve_game():
    initialize_new_game()
    pause_game()
    pause_button.configure(text="Spiel pausieren")
    check_solution_button.config(state="disabled")
    elapsed_time_label.configure(text="00:00")
    if len(pictures_riddle) == 0:
        switch_game_button.configure(state="disabled")
    # display all fields with the correct color
    for ii in range(NUMBER_ROWS):
        for jj in range(NUMBER_COLUMNS):
            if riddle_0[ii][jj] == 0:
                all_buttons[ii][jj].configure(bg="white")
            else:
                all_buttons[ii][jj].configure(bg="black")


# executed when button "Neues Rätsel" is pressed
def switch_game():
    initialize_new_game()
    pause_game()
    pause_button.configure(text="Spiel pausieren")
    if len(pictures_riddle) > 0:
        random_number = random.randint(0, len(pictures_riddle) - 1)
        global riddle_0
        riddle_0 = pictures_riddle[random_number]
        pictures_riddle.pop(random_number)
        riddle_name_label.configure(text=f'Hinweis: {text_riddle[random_number]}')
        # Wenn keine Bilder mehr vorhanden
        if len(pictures_riddle) == 0:
            switch_game_button.configure(text="Keine weiteren Bilder")
            switch_game_button.configure(state="disabled")
        # Wenn es Bilder gibt
        else:
            switch_game_button.configure(text=f"Neues Rätsel (Noch {len(pictures_riddle)})")
        update_column_labels()
        update_row_labels()
        text_riddle.pop(random_number)


# Muten/Unmuten der Sounds
def change_sound():
    global is_sound_muted
    if is_sound_muted:
        is_sound_muted = False
        sound_button.configure(image=icon_sound_on)
    else:
        is_sound_muted = True
        sound_button.configure(image=icon_sound_off)


# Muten/Unmuten der Musik
def change_music():
    global is_music_muted
    global music_play_obj
    if is_music_muted:
        is_music_muted = False
        music_button.configure(image=icon_music_on)
    else:
        if music_play_obj.is_playing():
            music_play_obj.stop()
        is_music_muted = True
        music_button.configure(image=icon_music_off)


# Loop um zu überprüfen, ob noch Musik spielt
def loop_music():
    global music_play_obj
    if not is_music_muted and not music_play_obj.is_playing():
        music_play_obj = music_wav_obj.play()
    root.after(1000, loop_music)


# Bestenlisten-Fenster
def open_bestenliste():
    # Falls noch nicht pausiert, pausiere das Spiel
    if not is_paused and is_running:
        pause_game()
    # Konfiguration des neuen Fensters
    bestenliste = Toplevel(root)

    bestenliste.title('PyCross Bestenliste')
    bestenliste.geometry("300x550")
    bestenliste.resizable(False, False)
    bestenliste.iconbitmap('icons/Logo.ico')

    bestenliste_title_label = Label(bestenliste, text="PyCross", font='Verdana 20 bold')
    bestenliste_title_label.pack(pady=(30, 10))
    bestenliste_label = Label(bestenliste, text="Bestenliste", font='Verdana 14 bold')
    bestenliste_label.pack(pady=(0, 30))

    listen_frame = Frame(bestenliste, highlightbackground="black", highlightthickness=FRAME_BORDER)
    listen_frame.pack()

    # SQLite
    # Datenbank kann beliebig voll sein, es werden nur die schnellsten 10 Datensätze übernommen
    sqlite_select_query = """SELECT * from scores ORDER BY zeit LIMIT 10"""
    cursor.execute(sqlite_select_query)
    records = cursor.fetchall()

    # Frame Einteilung
    platz_frame = Frame(listen_frame, highlightbackground="black", highlightthickness=FRAME_BORDER)
    platz_frame.pack(side=LEFT)
    name_frame = Frame(listen_frame, highlightbackground="black", highlightthickness=FRAME_BORDER)
    name_frame.pack(side=LEFT, padx=15)
    zeit_frame = Frame(listen_frame, highlightbackground="black", highlightthickness=FRAME_BORDER)
    zeit_frame.pack(side=LEFT)
    # Überschriften
    platz_label = Label(platz_frame, font='Verdana 10 bold', text="Platz")
    name_label = Label(name_frame, font='Verdana 10 bold', text="Name")
    zeit_label = Label(zeit_frame, font='Verdana 10 bold', text="Zeit")
    platz_label.pack()
    name_label.pack()
    zeit_label.pack()

    # Liste ausgeben
    counter = 1
    for row in records:
        minutes_to_show = str(row[2]).zfill(2)
        seconds_to_show = str(row[3]).zfill(2)
        row_platz = Label(platz_frame, font='Verdana 10', text=counter)
        row_platz.pack()
        row_name = Label(name_frame, font='Verdana 10', text=row[0])
        row_name.pack()
        row_zeit = Label(zeit_frame, font='Verdana 10', text=f"{minutes_to_show}:{seconds_to_show}")
        row_zeit.pack()
        counter += 1

    # Schließen Button
    schliessen_button = Button(bestenliste, text="Bestenliste schließen", command=lambda: close_window(bestenliste),
                               width=BUTTON_WIDTH,
                               font=BUTTON_FONT,
                               relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
    schliessen_button.pack(pady=30)


# closes modal window bestenlisten
def close_window(window):
    window.destroy()


# executed when button "Spiel überprüfen" is pressed
def check_game():
    if not is_paused:
        pause_game()
    check_result()


# helper function to calculate labels for columns
# called when riddle changes
def update_column_labels():
    new_labels = calculate_column_labels()

    for ii in range(NUMBER_COLUMNS):
        all_column_labels[NUMBER_COLUMNS - 1 - ii].configure(text=new_labels[ii])


# helper function to calculate labels for rows
# called when riddle changes
def update_row_labels():
    new_labels = calculate_row_labels()

    for ii in range(NUMBER_ROWS):
        all_row_labels[ii].configure(text=new_labels[ii])


# function to switch button background and play sound
# called every time a button is pressed
def change_color(input_button):
    if is_running and not is_paused:
        orig_color = input_button.cget("background")
        if orig_color == "white":
            input_button.configure(bg="black")
        else:
            input_button.configure(bg="white")
        if not is_sound_muted:
            _thread.start_new_thread(click_wav_obj.play, ())


# function to initialize a new game
def initialize_new_game():
    global elapsed_time
    elapsed_time = 0
    global start_time
    start_time = 0
    global is_paused
    is_paused = False
    global is_running
    is_running = False
    global is_restarted
    is_restarted = False

    start_button.configure(text="Spiel starten", state="normal")
    help_button.config(state="disabled")
    pause_button.config(text="Spiel pausieren", state="disabled")
    check_solution_button.config(state="normal")
    solve_button.config(state="normal")
    if len(pictures_riddle) == 0:
        switch_game_button.configure(state="disabled")
    else:
        switch_game_button.config(state="normal")
    name_entry.delete(0, END)
    elapsed_time_label.configure(text="00:00")
    error_label.configure(text="")
    all_buttons_white()


# helper function to set background of all buttons to white
def all_buttons_white():
    for button_row in all_buttons:
        for button in button_row:
            button.configure(bg="white")


# function to restart game
def restart_game():
    global is_running
    is_running = True
    start_timer()
    for ii in range(NUMBER_ROWS):
        for jj in range(NUMBER_COLUMNS):
            all_buttons[ii][jj].configure(bg="white")


result = [[0 for column in range(NUMBER_COLUMNS)] for row in range(NUMBER_ROWS)]


# helper function to check if result is correct
def check_result():
    anz_fehler = 0
    for ii in range(NUMBER_ROWS):
        for jj in range(NUMBER_COLUMNS):
            if (riddle_0[ii][jj] == 0 and all_buttons[ii][jj].cget("background") == "white") or (
                    riddle_0[ii][jj] == 1 and all_buttons[ii][jj].cget("background") == "black"):
                result[ii][jj] = 1
            else:
                anz_fehler += 1
    if anz_fehler == 0:
        error_label.configure(
            text=f"Herzlichen Glückwunsch! \n Du hast alles richtig. \n Bitte trage Deinen Namen (max. 10 Zeichen) "
                 f"ein und klicke auf Speichern")
        name_entry.pack(pady=(0, 10))
        name_submit_button.pack()
        if not is_sound_muted:
            _thread.start_new_thread(win_wav_obj.play, ())
        start_button.config(state="disabled")
        pause_button.config(state="disabled")
        help_button.config(state="disabled")
        solve_button.config(state="disabled")
        switch_game_button.config(state="disabled")
        check_solution_button.config(state="disabled")

    else:
        if not is_sound_muted:
            _thread.start_new_thread(error_wav_obj.play, ())
        error_label.configure(text=f"Es gibt noch {anz_fehler} Fehler")


# helper function to start timer
def start_timer():
    globals()['start_time'] = time.perf_counter()
    update_clock()


# helper function to update visible timer
def update_clock():
    global elapsed_time
    global start_time
    global minutes_str
    global seconds_str
    if is_paused:
        elapsed_time = round(time.perf_counter() - start_time) + elapsed_time
    else:
        total_time = round(time.perf_counter() - start_time) + elapsed_time
        minutes = total_time // 60
        seconds = total_time - (minutes * 60)

        minutes_str = str(minutes).zfill(2)
        seconds_str = str(seconds).zfill(2)

        elapsed_time_label.configure(text=f"{minutes_str}:{seconds_str}")
        root.after(100, update_clock)


# helper function to submit data to database after game was solved
def submit_name():
    name = name_entry.get()
    cursor.execute("INSERT INTO scores VALUES (?, ?, ?, ?)", (name, elapsed_time, minutes_str, seconds_str))
    db.commit()
    name_entry.pack_forget()
    name_submit_button.pack_forget()
    initialize_new_game()


# building of main window
root = Tk()
root.title('PyCross')
root.geometry("600x730")
root.resizable(False, False)
root.iconbitmap('icons/Logo.ico')

pixel = PhotoImage(width=1, height=1)
icon_sound_on = PhotoImage(file="icons/Sound_Unmute.png")
icon_sound_off = PhotoImage(file="icons/Sound_Mute.png")
icon_music_on = PhotoImage(file="icons/Musik_Unmute.png")
icon_music_off = PhotoImage(file="icons/Musik_Mute.png")

game_title_label = Label(root, text="PyCross", font='Verdana 20 bold')
game_title_label.pack(pady=30)

header_frame = Frame(root, highlightbackground="black", highlightthickness=FRAME_BORDER)
header_frame.pack(side='top')

start_button = Button(header_frame, text="Spiel starten", command=start_game, width=BUTTON_WIDTH, font=BUTTON_FONT,
                      relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
start_button.pack(side='left', padx=10)

pause_button = Button(header_frame, text="Spiel pausieren", command=pause_game, width=BUTTON_WIDTH, font=BUTTON_FONT,
                      relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER, state="disabled")
pause_button.pack(side='left', padx=10)

elapsed_time_label = Label(root, font='Verdana 25', text="00:00")
elapsed_time_label.pack(pady=5)

riddle_name_label = Label(root, font='Verdana 15', text=f'Hinweis: ?')
riddle_name_label.pack(pady=5)

main_frame = Frame(root, highlightbackground="black", highlightthickness=FRAME_BORDER)
main_frame.pack(side='top', padx=(0, 40))

game_frame = Frame(main_frame, highlightbackground="yellow", highlightthickness=FRAME_BORDER)
game_frame.pack(side='left', padx=(0, 0))

top_frame = Frame(game_frame, highlightbackground="red", highlightthickness=FRAME_BORDER, width=400, height=60)
top_frame.pack(side='top', fill='both')

column_label_frame = Frame(top_frame, highlightbackground="magenta", highlightthickness=FRAME_BORDER, width=210,
                           height=100)
column_label_frame.pack(side='right')
column_label_frame.pack_propagate(0)

all_column_labels = []
labels_column = calculate_column_labels()
for i in range(NUMBER_COLUMNS):
    new_frame = Frame(column_label_frame, highlightbackground="black", highlightthickness=0, width=21)
    new_frame.pack(side='right', fill='y')
    new_frame.pack_propagate(0)
    new_label = Label(new_frame, font='Verdana 10', text=labels_column[NUMBER_COLUMNS - 1 - i], wraplength=1, width=1)
    new_label.pack(side='bottom')
    all_column_labels.append(new_label)

bottom_frame = Frame(game_frame, highlightbackground="black", highlightthickness=FRAME_BORDER, width=400, height=208)
bottom_frame.pack(side='bottom')

button_frame = Frame(bottom_frame, highlightbackground="cyan", highlightthickness=FRAME_BORDER)
button_frame.pack(side='right', fill='both')

frames_buttons = []
for i in range(NUMBER_ROWS + 1):
    frames_buttons.append(Frame(button_frame))
    frames_buttons[i].pack(side='top')

all_buttons = []
for i in range(NUMBER_ROWS):
    row = []
    for j in range(NUMBER_COLUMNS):
        row.append(Button(frames_buttons[i + 1], image=pixel, height=15, width=15, bg="white",
                          command=lambda c=i, d=j: change_color(all_buttons[c][d])))
    all_buttons.append(row)

for i in range(NUMBER_ROWS):
    for j in range(NUMBER_COLUMNS):
        all_buttons[i][j].pack(side=LEFT)

row_label_frame = Frame(bottom_frame, highlightbackground="magenta", highlightthickness=FRAME_BORDER, width=100,
                        height=210)
row_label_frame.pack(padx=4, side='right')
row_label_frame.pack_propagate(0)

all_row_labels = []
labels_row = calculate_row_labels()
for i in range(NUMBER_ROWS):
    new_frame = Frame(row_label_frame, highlightbackground="black", highlightthickness=0, height=21)
    new_frame.pack(side='top', fill='x')
    new_frame.pack_propagate(0)
    new_label = Label(new_frame, font='Verdana 10', text=labels_row[i])
    new_label.pack(side='right')
    all_row_labels.append(new_label)

side_menu_frame = Frame(main_frame, highlightbackground="black", highlightthickness=FRAME_BORDER)
side_menu_frame.pack(side='left', padx=(50, 0), pady=(105, 0))

help_button = Button(side_menu_frame, text="Hilfe (+15 Sekunden)", command=help_game, width=BUTTON_WIDTH,
                     font=BUTTON_FONT,
                     relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER, state="disabled")
help_button.pack(pady=(0, 10))

solve_button = Button(side_menu_frame, text="Spiel lösen und beenden", command=solve_game, width=BUTTON_WIDTH,
                      font=BUTTON_FONT,
                      relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
solve_button.pack(pady=(0, 10))

switch_game_button = Button(side_menu_frame, text=f"Neues Rätsel (Noch {len(pictures_riddle)})", command=switch_game,
                            width=BUTTON_WIDTH,
                            font=BUTTON_FONT,
                            relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
switch_game_button.pack(pady=(0, 10))

bestenliste_button = Button(side_menu_frame, text="Bestenliste anzeigen", command=open_bestenliste, width=BUTTON_WIDTH,
                            font=BUTTON_FONT,
                            relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
bestenliste_button.pack(pady=(0, 10))

sound_button = Button(side_menu_frame, text="Geräusche deaktivieren", image=icon_sound_on, command=change_sound,
                      width=40, height=40, font='Verdana 10',
                      relief='groove', borderwidth=3)
sound_button.pack(side=LEFT)

music_button = Button(side_menu_frame, text="Musik deaktivieren", image=icon_music_on, command=change_music,
                      width=40, height=40, font='Verdana 10',
                      relief='groove', borderwidth=3)
music_button.pack(padx=(75, 0), side=LEFT)

footer_frame = Frame(root, highlightbackground="black", highlightthickness=FRAME_BORDER)
footer_frame.pack(side='top', pady=(20, 0))

check_solution_button = Button(footer_frame, text="Spiel überprüfen", command=check_game, width=BUTTON_WIDTH,
                               font=BUTTON_FONT,
                               relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
check_solution_button.pack()

error_label = Label(footer_frame, text="", font='Verdana 10')
error_label.pack()

entry_text = StringVar()
name_entry = Entry(footer_frame, width=30, font='Verdana 10', relief='groove', borderwidth=3, justify='center',
                   textvariable=entry_text)


# limit name to 10 characters
def character_limit(entry_text_input):
    if len(entry_text_input.get()) > 0:
        entry_text_input.set(entry_text_input.get()[:10])


entry_text.trace("w", lambda *args: character_limit(entry_text))

name_submit_button = Button(footer_frame, text="Speichern", command=submit_name, width=BUTTON_WIDTH, font=BUTTON_FONT,
                            relief=BUTTON_RELIEF, borderwidth=BUTTON_BORDER)
if not is_music_muted and not music_play_obj.is_playing():
    loop_music()

root.mainloop()
