import subprocess
import tkinter as tk
from tkinter import messagebox


def download_video():
    def start_download():
        urls_input = entry_urls.get().strip()
        if not urls_input:
            messagebox.showinfo("שגיאה", "לא הוזנו קישורים.")
            return

        urls = [url.strip() for url in urls_input.split(",")]
        format_choice = var_format.get()
        quality_choice = var_quality.get()

        if format_choice == 1:  # MP4
            if quality_choice == 1:  # איכות גבוהה
                format_option = ["yt-dlp", "--no-check-certificate"]
            elif quality_choice == 2:  # איכות נמוכה
                format_option = ["yt-dlp", "--no-check-certificate", "-f", "mp4"]
            else:
                messagebox.showerror("שגיאה", "בחר איכות תקינה.")
                return
        elif format_choice == 2:  # MP3
            format_option = ["yt-dlp", "--no-check-certificate", "-x", "--audio-format", "mp3"]
        else:
            messagebox.showerror("שגיאה", "בחר פורמט תקין.")
            return

        for url in urls:
            command = format_option + [url]
            try:
                subprocess.run(command, check=True)
                messagebox.showinfo("הצלחה", f"ההורדה של {url} הושלמה בהצלחה!")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("שגיאה", f"אירעה שגיאה במהלך ההורדה של {url}.\n{e}")
            except FileNotFoundError:
                messagebox.showerror("שגיאה", "yt-dlp לא נמצא במערכת. ודא שהתקנת אותו ושהוא נגיש מ-PATH.")

    def show_about():
        about_window = tk.Toplevel(root)
        about_window.title("אודות")
        about_window.geometry("300x200")
        about_window.resizable(False, False)

        tk.Label(
            about_window,
            text="CobaltYT_dlp",
            font=("Arial", 16, "bold"),
            anchor="center"
        ).pack(pady=(20, 5))

        tk.Label(
            about_window,
            text="Ver 0.1",
            font=("Arial", 12),
            anchor="center"
        ).pack(pady=(0, 20))

        tk.Label(
            about_window,
            text="מנוע הורדה: ראובן שבתי\nממשק גרפי: אשי ורד",
            font=("Arial", 10),
            justify="right",
            anchor="e"
        ).pack()

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

    tk.Label(root, text="קישורים לסרטונים (מופרדים בפסיק):", anchor="e").pack(pady=5)
    entry_urls = tk.Entry(root, width=50, justify="right")
    entry_urls.pack(pady=5)
    create_context_menu(entry_urls)  # הוספת תפריט הקשר לשדה הטקסט

    tk.Label(root, text="בחר פורמט:", anchor="e").pack(pady=5)
    var_format = tk.IntVar(value=1)
    rb_format_1 = tk.Radiobutton(root, text="MP4 (וידאו)", variable=var_format, value=1, anchor="w", command=update_quality_visibility)
    rb_format_1.pack(anchor="w", padx=20)
    rb_format_2 = tk.Radiobutton(root, text="MP3 (אודיו)", variable=var_format, value=2, anchor="w", command=update_quality_visibility)
    rb_format_2.pack(anchor="w", padx=20)

    # מסגרת לאפשרויות איכות
    frame_quality = tk.Frame(root)
    tk.Label(frame_quality, text="בחר איכות:", anchor="e").pack()
    var_quality = tk.IntVar(value=1)
    rb_quality_1 = tk.Radiobutton(frame_quality, text="איכות גבוהה", variable=var_quality, value=1, anchor="w")
    rb_quality_1.pack(anchor="w", padx=20)
    rb_quality_2 = tk.Radiobutton(frame_quality, text="איכות נמוכה", variable=var_quality, value=2, anchor="w")
    rb_quality_2.pack(anchor="w", padx=20)

    frame_quality.pack(pady=5)

    button_width = 15
    tk.Button(root, text="התחל הורדה", command=start_download, width=button_width).pack(pady=10)
    tk.Button(root, text="אודות", command=show_about, width=button_width).pack(pady=5)

    update_quality_visibility()  # עדכון מצב התצוגה
    root.mainloop()


# קריאה לפונקציה
if __name__ == "__main__":
    download_video()
