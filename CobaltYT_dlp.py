import os
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox


# קובץ הגדרות
CONFIG_FILE = "config.json"


def load_config():
    """טוען את הגדרות התוכנה מקובץ."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config):
    """שומר את הגדרות התוכנה לקובץ."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def download_video():
    def start_download():
        urls_input = entry_urls.get().strip()
        if not urls_input:
            messagebox.showinfo("שגיאה", "לא הוזנו קישורים.")
            return

        urls = [url.strip() for url in urls_input.split(",")]
        format_choice = var_format.get()
        quality_choice = var_quality.get()
        ssl_option = [] if not ssl_check.get() else ["--no-check-certificate"]

        if format_choice == 1:  # MP4
            if quality_choice == 1:  # איכות גבוהה
                format_option = ["yt-dlp"] + ssl_option
            elif quality_choice == 2:  # איכות נמוכה
                format_option = ["yt-dlp"] + ssl_option + ["-f", "mp4"]
            else:
                messagebox.showerror("שגיאה", "בחר איכות תקינה.")
                return
        elif format_choice == 2:  # MP3
            format_option = ["yt-dlp"] + ssl_option + ["-x", "--audio-format", "mp3"]
        else:
            messagebox.showerror("שגיאה", "בחר פורמט תקין.")
            return

        save_directory = default_save_dir.get()
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        for url in urls:
            command = format_option + ["-o", os.path.join(save_directory, "%(title)s.%(ext)s"), url]
            try:
                subprocess.run(command, check=True)
                messagebox.showinfo("הצלחה", f"ההורדה של {url} הושלמה בהצלחה!")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("שגיאה", f"אירעה שגיאה במהלך ההורדה של {url}.\n{e}")
            except FileNotFoundError:
                messagebox.showerror("שגיאה", "yt-dlp לא נמצא במערכת. ודא שהתקנת אותו ושהוא נגיש מ-PATH.")

    def open_settings():
        settings_window = tk.Toplevel(root)
        settings_window.title("הגדרות")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)

        def select_save_directory():
            selected_dir = filedialog.askdirectory()
            if selected_dir:
                default_save_dir.set(selected_dir)
                save_config({"save_dir": selected_dir, "ssl_check": ssl_check.get()})
                messagebox.showinfo("תיקייה", f"נבחרה תיקיית ברירת מחדל חדשה:\n{selected_dir}")

        def toggle_ssl_check():
            save_config({"save_dir": default_save_dir.get(), "ssl_check": ssl_check.get()})
            if ssl_check.get():
                messagebox.showinfo("הגדרות", "בדיקת SSL כובתה.")
            else:
                messagebox.showinfo("הגדרות", "בדיקת SSL הופעלה.")

        tk.Label(settings_window, text="תיקיית ברירת מחדל לשמירה:").pack(pady=10)
        tk.Entry(settings_window, textvariable=default_save_dir, width=50).pack(pady=5)
        tk.Button(settings_window, text="בחר תיקייה", command=select_save_directory).pack(pady=5)

        tk.Label(settings_window, text="אפשרויות SSL:").pack(pady=10)
        tk.Checkbutton(settings_window, text="כבה בדיקת SSL", variable=ssl_check, command=toggle_ssl_check).pack(pady=5)

    def open_about():
        about_window = tk.Toplevel(root)
        about_window.title("אודות")
        about_window.geometry("200x200")
        about_window.resizable(False, False)

        tk.Label(about_window, text="CobaltYT_dlp", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(about_window, text="Ver. 0.2").pack(pady=5)
        tk.Label(about_window, text="").pack(pady=5)
        tk.Label(about_window, text="מנוע הורדה: ראובן שבתי", anchor="e").pack(pady=5)
        tk.Label(about_window, text="ממשק גרפי: אשי ורד", anchor="e").pack(pady=5)

    def update_quality_visibility():
        if var_format.get() == 1:  # MP4
            frame_quality.pack(pady=5)
        elif var_format.get() == 2:  # MP3
            frame_quality.pack_forget()

    def create_context_menu(widget):
        context_menu = tk.Menu(widget, tearoff=0)
        context_menu.add_command(label="העתק", command=lambda: widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="הדבק", command=lambda: widget.event_generate("<<Paste>>"))
        context_menu.add_command(label="גזור", command=lambda: widget.event_generate("<<Cut>>"))

        def show_context_menu(event):
            context_menu.post(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_context_menu)  # לחצן ימני לפתיחת התפריט

    # יצירת חלון ראשי
    root = tk.Tk()
    root.title("CobaltYT_dlp")

    config = load_config()
    ssl_check = tk.BooleanVar(value=config.get("ssl_check", False))  # מצב בדיקת SSL
    default_save_dir = tk.StringVar(value=config.get("save_dir", os.path.join(os.path.expanduser("~"), "Downloads", "CobaltYT_dlp")))

    tk.Label(root, text="קישורים לסרטונים (מופרדים בפסיק):", anchor="e").pack(pady=5)
    entry_urls = tk.Entry(root, width=50, justify="right")
    entry_urls.pack(pady=5)
    entry_urls.bind("<Control-c>", lambda event: entry_urls.event_generate("<<Copy>>"))
    entry_urls.bind("<Control-v>", lambda event: entry_urls.event_generate("<<Paste>>"))
    create_context_menu(entry_urls)

    tk.Label(root, text="בחר פורמט:", anchor="e").pack(pady=5)
    var_format = tk.IntVar(value=1)
    rb_format_1 = tk.Radiobutton(root, text="MP4 (וידאו)", variable=var_format, value=1, anchor="w", command=update_quality_visibility)
    rb_format_1.pack(anchor="w", padx=20)
    rb_format_2 = tk.Radiobutton(root, text="MP3 (אודיו)", variable=var_format, value=2, anchor="w", command=update_quality_visibility)
    rb_format_2.pack(anchor="w", padx=20)

    frame_quality = tk.Frame(root)
    tk.Label(frame_quality, text="בחר איכות:", anchor="e").pack()
    var_quality = tk.IntVar(value=1)
    rb_quality_1 = tk.Radiobutton(frame_quality, text="איכות גבוהה", variable=var_quality, value=1, anchor="w")
    rb_quality_1.pack(anchor="w", padx=20)
    rb_quality_2 = tk.Radiobutton(frame_quality, text="איכות נמוכה", variable=var_quality, value=2, anchor="w")
    rb_quality_2.pack(anchor="w", padx=20)

    frame_quality.pack(pady=5)

    # מסגרת לכפתורים
    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", pady=10)

    # לחצנים עם סמל
    img_settings = tk.PhotoImage(file="images/settings.png").subsample(8, 8)
    img_info = tk.PhotoImage(file="images/info.png").subsample(8, 8)

    # לחצני תמונה (צמודים לשמאל)
    btn_info = tk.Button(button_frame, image=img_info, command=open_about)
    btn_info.pack(side="left", padx=5)

    btn_settings = tk.Button(button_frame, image=img_settings, command=open_settings)
    btn_settings.pack(side="left", padx=5)

    # כפתור "התחל הורדה" (ממורכז)
    btn_start_download = tk.Button(button_frame, text="התחל הורדה", command=start_download, width=15)
    btn_start_download.pack(side="left", padx=35)


    update_quality_visibility()
    root.mainloop()


if __name__ == "__main__":
    download_video()
