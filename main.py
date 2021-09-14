import ctypes
import os
import tkinter as tk
import tkinter.filedialog as tdialog
import tkinter.ttk as ttk
import tkinter.font
import pickle
import glob
import time
from PIL import Image, ImageTk


class Application(tk.Frame):

    def __init__(self, master=None, scale: float = 1.0):
        super().__init__(master)

        self.image_list = []
        self.current_index = 0
        self.images_len = 0
        self.index_label_text = tk.StringVar()
        self.index_label_text.set("0/0")
        self.image_name = tk.StringVar()
        self.image_name.set('')
        self.slide_show_time = tk.IntVar()
        self.slide_show_time.set(3)
        self.current_image = None
        self.current_image2 = None
        self.current_image3 = None
        self.scale = scale

        self.image_canvas_ss = None

        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        # self.filemenu.add_command(label="Undo", command=self.input_text.undo, accelerator="Ctrl+Z")
        # self.filemenu.add_command(label="Redo", accelerator="Ctrl+Y")
        self.filemenu.add_command(label="Read from file", command=self.select_images, accelerator="Ctrl+O")
        # self.filemenu.add_command(label="Save credentials", command=self.save_data, accelerator="Ctrl+S")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Preferences", command=self.open_settings_, accelerator="Alt+P")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.actionmenu = tk.Menu(self.menubar, tearoff=0)
        self.actionmenu.add_command(label="Next", command=self.next_image, accelerator="Ctrl+L")
        self.actionmenu.add_command(label="Previous", command=self.prev_image, accelerator="Ctrl+J")
        self.actionmenu.add_command(label="Start Slideshow", command=self.start_slideshow, accelerator="Alt+S")
        self.menubar.add_cascade(label="Actions", menu=self.actionmenu)

        # helpmenu
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        # self.helpmenu.add_command(label="About...", command=lambda: tkinterextension.raise_frame(self.help_frame))
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        root.config(menu=self.menubar)

        # menu popup
        self.popup = tk.Menu(tearoff=0)
        self.popup.add_separator()

        # help frame
        self.help_frame = ttk.LabelFrame(text="Help", width=500, height=300)
        self.help_frame.grid_propagate(False)
        # self.help_frame.grid(row=0, column=0)
        self.help_label = ttk.Label(self.help_frame, text="""
        Cappribot version 0.1.0
        refer to GitHub readme.md for more information
        """)
        self.help_label.grid(row=0, column=0)
        self.close_frame_button = ttk.Button(master=self.help_frame, text="Close")
        self.close_frame_button.grid(row=1, column=1)

        self.help_frame.lower()

        # main widgets
        self.image_test = Image.open("Source/Icon/gradient_less_saturated.png")

        self.image_canvas = tk.Canvas(width=500, height=768, background='#3B3D3F')
        self.image_canvas.pack(anchor='center', expand='yes')
        # self.image_canvas.place(anchor='n', relx=0.5, rely=0)
        root.update()
        self.canvas_im = self.image_canvas.create_image((self.image_canvas.winfo_width()/2, self.image_canvas.winfo_height()/2),
                                                        image=self.current_image, anchor='center')
        self.update_label()
        self.resizing()
        self.name_label = ttk.Label(textvariable=self.image_name)\
            .place(in_=self.image_canvas, bordermode='outside', anchor='nw', relx=0, rely=1.0, y=2, relwidth=1.0)

        self.fram = ttk.Frame()
        self.open_button = ttk.Button(self.fram, text="Open File", command=self.select_images, width=8).pack(side='left')
        self.prev_button = ttk.Button(self.fram, text="Prev", command=self.prev_image, width=5)\
            .place(anchor='center', relx=0.45, rely=0.5)
        self.index_label = ttk.Label(self.fram, textvariable=self.index_label_text)\
            .place(anchor='center', relx=0.5, rely=0.5)
        self.next_button = ttk.Button(self.fram, text="Next", command=self.next_image, width=5)\
            .place(anchor='center', relx=0.55, rely=0.5)
        self.slideshow_button = ttk.Button(self.fram, text="Slideshow", command=self.start_slideshow).pack(side='right')
        self.timer_box = ttk.Spinbox(master=self.fram, width=6, from_=1, to=120, wrap=True,
                                     textvariable=self.slide_show_time)
        self.timer_box.pack(side='right')
        self.timer_label = ttk.Label(master=self.fram, text="Timer (s):")
        self.timer_label.pack(side='right')
        # self.page_label = ttk.Label(self.fram, textvariable=self.num_page_tv).pack(side='left')
        self.fram.pack(side='bottom', fill='both')

        self.bind_keys()
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # to fix blurry text

    last_view_time = 0
    paused = False
    timer_id = None
    # image = None

    # def toggle_fullscreen(self, event=None):
    #     root.state = not root.state  # Just toggling the boolean
    #     root.tk.attributes("-fullscreen", root.state)
    #     # root.state('zoomed', True)
    #     # print('zoomed')
    #     return "break"

    def open_fs_slideshow(self, image_count =3):
        fs_slideshow = tk.Toplevel(root)
        fs_slideshow.title("Settings")
        fs_slideshow.bind("<Escape>", lambda e: fs_slideshow.destroy())
        fs_slideshow.bind("<Left>", lambda e: self.prev_images())
        fs_slideshow.bind("<Right>", lambda e: self.next_images())
        fs_slideshow.bind("<t>", lambda e: self.toggle_pause_slideshow())
        fs_slideshow.state('zoomed')
        fs_slideshow.overrideredirect(1)

        root.update()

        self.image_canvas_ss = tk.Canvas(fs_slideshow, width=fs_slideshow.winfo_width(),
                                 height=fs_slideshow.winfo_height(), background='#3B3D3F')
        self.image_canvas_ss.pack(anchor='center', expand='yes')
        root.update()
        canvas_im = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image, anchor='center')
        canvas_im2 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image, anchor='center')
        canvas_im3 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image, anchor='center')

        # self.paused = not self.paused
        self.set_timer()

    def bind_keys(self):
        # shortcuts
        # root.bind("<t>", self.toggle_fullscreen)

        root.bind('<Control-o>', lambda e: self.select_images())
        root.bind('<Control-s>', lambda e: self.save_data())

        root.bind('<Alt-p>', lambda e: self.open_settings_())

        root.bind('<Control-j>', lambda e: self.prev_image())
        root.bind('<Control-l>', lambda e: self.next_image())

        # root.bind('<s>', lambda e: self.start_slideshow())
        root.bind('<Alt-s>', lambda e: self.open_fs_slideshow())
        # auto resize image
        root.bind('<Configure>', lambda e: self.resizing())

    def menu_popup(self, event):
        try:
            self.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup.grab_release()

    def resizing(self, mode=0, event=None):
        self.image_canvas.configure(width=root.winfo_height()*0.9*9/16, height=root.winfo_height()*0.9)
        if self.image_test:
            iw, ih = self.image_test.width, self.image_test.height
            # mw, mh = self.master.winfo_width(), self.master.winfo_height()
            if mode == 0:
                mw, mh = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
            else:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.8
            # print(f"original w: {iw}, h: {ih}")

            if iw > ih:
                ih = ih * (mw / iw)
                r = mh / ih if (ih / mh) > 1 else 1
                iw, ih = mw * r, ih * r
            else:
                iw = iw * (mh / ih)
                r = mw / iw if (iw / mw) > 1 else 1
                iw, ih = iw * r, mh * r
            return ImageTk.PhotoImage(self.image_test.resize((int(iw * self.scale), int(ih * self.scale))))

    # # select directory
    # def select_dir(self):
    #     file = tdialog.askdirectory(parent=root, initialdir='/', title='Select a directory')
    #     print("You chose %s" % file)
    #     self.read_images("%s" % file)

    # select multiple files
    def select_images(self):
        file = tdialog.askopenfilenames(parent=root, filetypes=(("image files", "*.jpg *.png *.jpeg"), ('All files', '*.*')),
                                        title='Select a directory')
        self.read_im(file)


    # def read_images(self, path):
    #     self.image_list = [Image.open(item) for i in [glob.glob(path+'/*.%s' % ext)
    #                                                   for ext in ["jpg", "png", "tga"]] for item in i]
    #     self.max_index = len(self.image_list)

    def update_label(self):
        self.index_label_text.set(f"{self.current_index+1}/{self.images_len}")
        self.image_name.set(f"{self.image_test.filename.split('/')[-1]}")

    def read_im(self, images):
        self.image_list = [Image.open(item) for item in images]
        self.images_len = len(self.image_list)
        self.update_label()
        self.open_image_at(0)

    def set_timer(self):
        if self.paused is False:
            # print("not paused")
            self.timer_id = root.after(300, self.update_clock)
        else:
            # root.after_cancel(self.timer_id)
            # print("paused")
            print("")

    def update_clock(self):
        if time.time() - self.last_view_time > self.slide_show_time.get() \
                and not self.paused:
            self.next_images()
            self.last_view_time = time.time()
        self.set_timer()

    def start_slideshow(self, img_count=1):
        # self.paused = not self.paused
        self.set_timer()

    def toggle_pause_slideshow(self):
        self.paused = not self.paused
        if self.paused is False:
            self.set_timer()


    def update_image(self, mode, ite=1):
        if mode == 0:
            self.image_canvas.delete('all')
            self.canvas_im = self.image_canvas.create_image(
                (self.image_canvas.winfo_width() / 2, self.image_canvas.winfo_height() / 2),
                image=self.current_image, anchor='center')
            self.update_label()
        else:  # mode is 1
            self.image_canvas_ss.delete('all')
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

    def open_image_at(self, index, mode=0, ite=1):
        self.image_test = self.image_list[index]
        self.current_image = self.resizing(mode)
        self.update_image(mode)

    def prev_image(self, mode=0, ite=1):
        if self.current_index <= 0:
            self.current_index = self.images_len - ite
        else:
            self.current_index -= ite
        self.open_image_at(self.current_index, mode, ite)

    def next_image(self, mode=0, ite=1):
        if self.current_index + ite >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += ite
        self.open_image_at(self.current_index, mode, ite)

    def next_images(self, mode=1, ite=1):

        self.image_canvas_ss.delete('all')

        if self.current_index + 1 >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += 1
        self.image_test = self.image_list[self.current_index]
        self.current_image = self.resizing(1)
        self.canvas_im = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image, anchor='center')
        # self.image_test = self.image_list[self.current_index]
        #         # self.current_image = self.resizing(mode)

        if self.current_index + 1 >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += 1
        self.image_test = self.image_list[self.current_index]
        self.current_image2 = self.resizing(1)
        self.canvas_im2 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image2, anchor='center')
        # self.image_test = self.image_list[self.current_index]
        # self.current_image = self.resizing(mode)

        if self.current_index + 1 >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += 1
        self.image_test = self.image_list[self.current_index]
        self.current_image3 = self.resizing(1)
        self.canvas_im3 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image3, anchor='center')

    def prev_images(self, mode=1, ite=1):

        self.image_canvas_ss.delete('all')

        if self.current_index - 5 <= 0:
            self.current_index = self.images_len - 5
        else:
            self.current_index -= 5
        self.image_test = self.image_list[self.current_index]
        self.current_image = self.resizing(1)
        self.canvas_im1 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image, anchor='center')
        # self.image_test = self.image_list[self.current_index]
        #         # self.current_image = self.resizing(mode)

        if self.current_index + 1 >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += 1
        self.image_test = self.image_list[self.current_index]
        self.current_image2 = self.resizing(1)
        self.canvas_im2 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image2, anchor='center')
        # self.image_test = self.image_list[self.current_index]
        # self.current_image = self.resizing(mode)

        if self.current_index + 1 >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += 1
        self.image_test = self.image_list[self.current_index]
        self.current_image3 = self.resizing(1)
        self.canvas_im3 = self.image_canvas_ss.create_image(
            (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
            image=self.current_image3, anchor='center')

    def open_settings_(self):
        settings = tk.Toplevel(root)
        settings.title("Settings")
        settings.geometry("550x400")

        apply_button = ttk.Button(master=settings, text="Apply", command=self.apply_settings)
        apply_button.grid(row=1, column=0, sticky="ews")

    def load_settings(self):
        if os.path.exists('Source/settings.txt'):
            try:
                with open('Source/settings.txt', 'r+b') as file:
                    return pickle.load(file)
            except EOFError:
                return {}
        else:
            return {}

    def apply_settings(self):
        self.save_settings()

    def save_settings(self):
        data = {}
        with open('Source/settings.txt', 'wb') as file:
            pickle.dump(data, file)

    def load_data(self):
        if os.path.exists('Source/save.txt'):
            try:
                with open('Source/save.txt', 'r+b') as file:
                    return pickle.load(file)
            except EOFError:
                return {}
        else:
            return {}

    def save_data(self):
        self.save_settings()
        if self.save_cred.get() is False:
            data = {
                    }
        else:
            data = {
                    }
        with open('Source/save.txt', 'wb') as file:
            pickle.dump(data, file)

root = tk.Tk()
# ttk.Style().configure("TButton", padding=6, relief="flat", foreground="#E8E8E8", background="#292929")
default_font = tk.font.nametofont("TkDefaultFont")
default_font.configure(size=11)
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
print(w, h)
root.geometry("1366x1000")
root.minsize(400, 200)
root.title("PictureXViewer v0.1.0a")
root.iconphoto(False, tk.PhotoImage(file='Source/Icon/gradient_less_saturated.png'))
root.tk.call('source', 'Source/Style/azure.tcl')
root.tk.call("set_theme", "dark")
app = Application(master=root)
app.mainloop()

