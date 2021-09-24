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

        # get screen information
        # ctypes.windll.shcore.SetProcessDpiAwareness(1)  # to fix blurry text
        #
        # user32 = ctypes.windll.user32
        self.screen_one_size = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.screen_two_size = user32.GetSystemMetrics(78) - user32.GetSystemMetrics(0), user32.GetSystemMetrics(79)
        self.screen_count = 1 if self.screen_two_size[0] == 0 else 2

        # data
        self.data = self.load_data()
        self.settings_data = self.load_settings()
        # settings
        self.show_label = tk.BooleanVar()
        self.show_label.set(True if not self.settings_data else self.settings_data["show_label"])
        self.save_path = tk.BooleanVar()
        self.save_path.set(True if not self.settings_data else self.settings_data["save_path"])
        # /settings

        self.filenames = None if (
                    not self.settings_data or not self.data or (self.settings_data and self.save_path is False)) else \
        self.data["filenames"]
        self.image_list = []
        self.current_index = 0 if (
                    not self.settings_data or not self.data or (self.settings_data and self.save_path is False)) else \
        self.data["current_index"]
        print(self.current_index)
        self.images_len = 0
        self.index_label_text = tk.StringVar()
        self.index_label_text.set("0/0")
        self.image_name = tk.StringVar()
        self.image_name.set('')

        self.slide_show_time = tk.IntVar()
        self.slide_show_time.set(3 if (not self.settings_data or "slide_show_time" not in self.settings_data)
                                 else self.settings_data["slide_show_time"])
        self.side_count = tk.IntVar()
        self.side_count.set(1 if (not self.settings_data or "side_count" not in self.settings_data)
                            else self.settings_data["side_count"])
        self.screen_dis = tk.IntVar()
        self.screen_dis.set(1 if (not self.settings_data or "screen_dis" not in self.settings_data)
                            else self.settings_data["screen_dis"])
        self.current_image = None
        self.current_image2 = None
        self.current_image3 = None
        self.scale = scale

        self.image_canvas_ss = None

        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Read from file", command=self.select_images, accelerator="Ctrl+O")
        # self.filemenu.add_command(label="Save credentials", command=self.save_data, accelerator="Ctrl+S")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Preferences", command=self.open_settings_, accelerator="Alt+P")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=root.quit, accelerator="Alt+X")
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.actionmenu = tk.Menu(self.menubar, tearoff=0)
        self.actionmenu.add_command(label="Next", command=self.next_image, accelerator="<")
        self.actionmenu.add_command(label="Previous", command=self.prev_image, accelerator=">")
        self.actionmenu.add_command(label="Start Slideshow", command=self.open_slideshow_initiator, accelerator="S")
        self.menubar.add_cascade(label="Actions", menu=self.actionmenu)

        # helpmenu
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=lambda: self.open_help_window())
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        root.config(menu=self.menubar)

        # menu popup
        self.popup = tk.Menu(tearoff=0)
        self.popup.add_separator()

        # # help frame
        # self.help_frame = ttk.LabelFrame(text="Help", width=500, height=300)
        # self.help_frame.grid_propagate(False)
        # # self.help_frame.grid(row=0, column=0)
        # self.help_label = ttk.Label(self.help_frame, text="""
        # PicturexViewer version 0.1.0
        # refer to GitHub readme.md for more information
        # """
        # self.help_label.grid(row=0, column=0)
        # self.close_frame_button = ttk.Button(master=self.help_frame, text="Close")
        # self.close_frame_button.grid(row=1, column=1)
        #
        # self.help_frame.lower()

        # main widgets
        self.image_test = Image.open("Source/Icon/gradient_less_saturated.png")

        self.image_canvas = tk.Canvas(width=500, height=768, background='#3B3D3F')
        self.image_canvas.pack(anchor='center', expand='yes')
        # self.image_canvas.place(anchor='n', relx=0.5, rely=0)
        root.update()
        self.canvas_im = self.image_canvas.create_image(
            (self.image_canvas.winfo_width() / 2, self.image_canvas.winfo_height() / 2),
            image=self.current_image, anchor='center')
        self.update_image()
        self.resizing()
        self.name_label = ttk.Label(textvariable=self.image_name) \
            .place(in_=self.image_canvas, bordermode='outside', anchor='nw', relx=0, rely=1.0, y=2, relwidth=1.0)

        self.fram = ttk.Frame()
        self.open_button = ttk.Button(self.fram, text="Open File", command=self.select_images, width=8).pack(
            side='left')
        self.prev_button = ttk.Button(self.fram, text="Prev", command=self.prev_image, width=5) \
            .place(anchor='center', relx=0.45, rely=0.5)
        self.index_label = ttk.Label(self.fram, textvariable=self.index_label_text) \
            .place(anchor='center', relx=0.5, rely=0.5)
        self.next_button = ttk.Button(self.fram, text="Next", command=self.next_image, width=5) \
            .place(anchor='center', relx=0.55, rely=0.5)
        self.slideshow_button = ttk.Button(self.fram, text="Slideshow", command=self.open_slideshow_initiator).pack(
            side='right')
        self.fram.pack(side='bottom', fill='both')

        # load data
        if self.filenames is not None:
            self.read_im(self.filenames, self.current_index)

        self.bind_keys()

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

    def open_settings_(self):
        settings = tk.Toplevel(root)
        settings.title("Settings")
        # settings.geometry(f"{600}x{450}+{int(root.winfo_width()/2)}+{int(root.winfo_height()/2)}")
        settings.minsize(300, 85)
        settings.geometry(f"+{int(root.winfo_width() / 2)}+{int(root.winfo_height() / 2)}")

        show_image_name = ttk.Checkbutton(master=settings, text="Show image label", variable=self.show_label)
        show_image_name.pack(side="left")
        save_image_path = ttk.Checkbutton(master=settings, text="Reopen images upon launch", variable=self.save_path)
        save_image_path.pack(side="left")
        apply_button = ttk.Button(master=settings, text="Apply",
                                  command=lambda: [self.apply_settings(), settings.destroy()])
        apply_button.pack(side="bottom")

    def open_help_window(self):
        help_window = tk.Toplevel(root)
        help_window.minsize(500, 200)
        help_window.geometry(f"+{int(root.winfo_width() / 2)}+{int(root.winfo_height() / 2)}")
        help_window.title("About")

        self.help_label = ttk.Label(master=help_window, text="""
                PicturexViewer version 0.1.0
                Refer to GitHub readme.md for more information.
                """)
        self.help_label.grid(row=0, column=0)
        self.close_frame_button = ttk.Button(master=help_window, text="Close", command=help_window.destroy)
        self.close_frame_button.grid(row=1, column=1)

        # self.help_frame.lower()

    def open_slideshow_initiator(self):
        if not self.image_list:  # nothing to slideshow
            return

        slideshow_indicator = tk.Toplevel(root)
        slideshow_indicator.minsize(400, 90)
        slideshow_indicator.geometry(f"+{int(root.winfo_width() / 2)}+{int(root.winfo_height() / 2)}")
        slideshow_indicator.title("Start Slideshow")
        slideshow_indicator.focus_set()

        self.timer_label = ttk.Label(master=slideshow_indicator, text="Timer (s):")
        self.timer_label.pack(side="left")
        self.timer_box = ttk.Spinbox(master=slideshow_indicator, width=6, from_=1, to=120, wrap=True,
                                     textvariable=self.slide_show_time)
        self.timer_box.pack(side="left")
        self.side_count_label = ttk.Label(master=slideshow_indicator, text="Side by side:")
        self.side_count_label.pack(side="left")
        self.side_count_box = ttk.Spinbox(master=slideshow_indicator, width=6, from_=1, to=3, wrap=True,
                                          textvariable=self.side_count)
        self.side_count_box.pack(side="left")

        if self.screen_count > 1:
            self.side_count_label = ttk.Label(master=slideshow_indicator, text="Display Monitor:")
            self.side_count_label.pack(side="left")
            self.side_count_box = ttk.Spinbox(master=slideshow_indicator, width=6, from_=1, to=self.screen_count,
                                              wrap=True,
                                              textvariable=self.screen_dis)
            self.side_count_box.pack(side="left")
        start_button = ttk.Button(master=slideshow_indicator, text="Start",
                                  command=lambda: [slideshow_indicator.destroy(), self.open_fs_slideshow(), self.save_settings()])
        start_button.pack(side="bottom")

        slideshow_indicator.bind('<Return>', lambda e: [slideshow_indicator.destroy(), self.open_fs_slideshow(), self.save_settings()])
        slideshow_indicator.bind('<Escape>', lambda e: slideshow_indicator.destroy())

    def open_fs_slideshow(self, image_count=3):
        fs_slideshow = tk.Toplevel(root)
        if self.screen_dis.get() == 1:
            fs_slideshow.geometry(f"{self.screen_one_size[0]}x{self.screen_one_size[1]}+0+0")
        else:
            fs_slideshow.geometry(f"{self.screen_one_size[0]}x{self.screen_one_size[1]}+{-self.screen_two_size[0]}+0")

        fs_slideshow.title("Settings")
        fs_slideshow.bind("<Escape>", lambda e: [fs_slideshow.destroy(), root.deiconify(), self.update_image()])
        fs_slideshow.bind("<Left>", lambda e: self.prev_image_slideshow())
        fs_slideshow.bind("<Right>", lambda e: self.next_image_slideshow())
        fs_slideshow.bind("<t>", lambda e: self.toggle_pause_slideshow())
        fs_slideshow.state('zoomed')
        fs_slideshow.overrideredirect(1)
        root.withdraw()
        root.update()

        self.image_canvas_ss = tk.Canvas(fs_slideshow, width=fs_slideshow.winfo_width(),
                                         height=fs_slideshow.winfo_height(), background='#3B3D3F')
        self.image_canvas_ss.pack(anchor='center', expand='yes')
        root.update()

        if self.image_canvas_ss is not None:
            self.image_canvas_ss.delete('all')

        if self.side_count.get() == 1:
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

        elif self.side_count.get() == 2:
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4 * 3, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

        elif self.side_count.get() == 3:
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image3 = self.resizing(self.side_count.get())
            self.canvas_im3 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image3, anchor='center')

        # if self.side_count.get() == 1:
        #     canvas_im = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image, anchor='center')
        #
        # elif self.side_count.get() == 2:
        #     canvas_im = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 4, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image, anchor='center')
        #
        #     canvas_im2 = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 4 * 3, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image2, anchor='center')
        #
        # elif self.side_count.get() == 3:
        #     canvas_im = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image, anchor='center')
        #
        #     canvas_im2 = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image2, anchor='center')
        #     canvas_im3 = self.image_canvas_ss.create_image(
        #         (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
        #         image=self.current_image3, anchor='center')

        self.last_view_time = time.time()
        self.set_timer()

    def bind_keys(self):
        # shortcuts
        # root.bind("<t>", self.toggle_fullscreen)

        root.bind('<Control-o>', lambda e: self.select_images())
        root.bind('<Control-s>', lambda e: self.save_data())

        root.bind('<Alt-p>', lambda e: self.open_settings_())
        root.bind('<Alt-x>', lambda e: root.quit())

        root.bind('<Left>', lambda e: self.prev_image())
        root.bind('<Right>', lambda e: self.next_image())

        # root.bind('<s>', lambda e: self.start_slideshow())
        # root.bind('<Alt-s>', lambda e: self.open_fs_slideshow())
        root.bind('<s>', lambda e: self.open_slideshow_initiator())
        # auto resize image
        root.bind('<Configure>', lambda e: self.resizing())

    def menu_popup(self, event):
        try:
            self.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup.grab_release()

    def resizing(self, mode=0, event=None):
        self.image_canvas.configure(width=root.winfo_height() * 0.9 * 9 / 16, height=root.winfo_height() * 0.9)
        if self.image_test:
            iw, ih = self.image_test.width, self.image_test.height
            # mw, mh = self.master.winfo_width(), self.master.winfo_height()
            if mode == 0:
                mw, mh = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
            # slideshow modes
            elif mode == 1:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.99
            elif mode == 2:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.97
                mw /= 2
            elif mode == 3:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.85
                mw /= 3

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
        self.filenames = tdialog.askopenfilenames(parent=root, filetypes=(
        ("image files", "*.jpg *.png *.jpeg"), ('All files', '*.*')),
                                                  title='Select a directory')
        self.read_im(self.filenames)

    # def read_images(self, path):
    #     self.image_list = [Image.open(item) for i in [glob.glob(path+'/*.%s' % ext)
    #                                                   for ext in ["jpg", "png", "tga"]] for item in i]
    #     self.max_index = len(self.image_list)

    def update_label(self):
        self.index_label_text.set(f"{self.current_index + 1}/{self.images_len}")
        if self.show_label.get():
            self.image_name.set(f"{self.image_test.filename.split('/')[-1]}")
        else:
            self.image_name.set("")

    def read_im(self, images, index=0):
        self.image_list = [Image.open(item) for item in images]
        self.images_len = len(self.image_list)
        self.update_label()
        self.open_image_at(index)

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
            self.next_image_slideshow()
            self.last_view_time = time.time()
        self.set_timer()

    def start_slideshow(self, img_count=1):
        # self.paused = not self.paused
        self.set_timer()

    def toggle_pause_slideshow(self):
        self.paused = not self.paused
        if self.paused is False:
            self.set_timer()

    def update_image(self):
        self.image_canvas.delete('all')
        self.current_image = self.resizing()
        self.canvas_im = self.image_canvas.create_image(
            (self.image_canvas.winfo_width() / 2, self.image_canvas.winfo_height() / 2),
            image=self.current_image, anchor='center')
        self.update_label()

    def open_image_at(self, index):
        self.image_test = self.image_list[index]
        self.update_image()

    def prev_image(self, ite=1):
        if self.current_index <= 0:
            self.current_index = self.images_len - ite
        else:
            self.current_index -= ite
        self.open_image_at(self.current_index)

    def next_image(self, ite=1):
        if self.current_index + ite >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += ite
        self.open_image_at(self.current_index)

    def next_image_slideshow(self):
        self.last_view_time = time.time()

        if self.image_canvas_ss is not None:
            self.image_canvas_ss.delete('all')

        if self.side_count.get() == 1:

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

        elif self.side_count.get() == 2:

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4 * 3, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

        elif self.side_count.get() == 3:

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image3 = self.resizing(self.side_count.get())
            self.canvas_im3 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image3, anchor='center')

        print(self.current_index)

    def prev_image_slideshow(self):
        self.last_view_time = time.time()

        if self.image_canvas_ss is not None:
            self.image_canvas_ss.delete('all')

        if self.side_count.get() == 1:
            if self.current_index == 0:
                self.current_index = self.images_len - 1
            else:
                self.current_index -= 1
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im1 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

        elif self.side_count.get() == 2:
            if self.current_index == 2:
                self.current_index = self.images_len - 1
            else:
                self.current_index -= 3
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im1 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 4 * 3, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

        elif self.side_count.get() == 3:
            if self.current_index < 5:
                self.current_index = (self.images_len - 1) + self.current_index - 4
            else:
                self.current_index -= 5
            self.image_test = self.image_list[self.current_index]
            self.current_image = self.resizing(self.side_count.get())
            self.canvas_im1 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image2 = self.resizing(self.side_count.get())
            self.canvas_im2 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image2, anchor='center')

            if self.current_index + 1 >= self.images_len:
                self.current_index = 0
            else:
                self.current_index += 1
            self.image_test = self.image_list[self.current_index]
            self.current_image3 = self.resizing(self.side_count.get())
            self.canvas_im3 = self.image_canvas_ss.create_image(
                (self.image_canvas_ss.winfo_width() / 6 * 5, self.image_canvas_ss.winfo_height() / 2),
                image=self.current_image3, anchor='center')
        print(self.current_index)


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
        self.update_label()
        self.save_settings()

    def save_settings(self):
        self.save_data()
        data = {'show_label': self.show_label.get(),
                'save_path': self.save_path.get(),
                'slide_show_time': self.slide_show_time.get(),
                'side_count': self.side_count.get(),
                'screen_dis': self.screen_dis.get()}
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
        # self.save_settings()
        if self.save_path.get() is False:
            data = {
            }
        else:
            data = {'filenames': self.filenames,
                    'current_index': self.current_index
                    }
        with open('Source/save.txt', 'wb') as file:
            pickle.dump(data, file)


root = tk.Tk()
# ttk.Style().configure("TButton", padding=6, relief="flat", foreground="#E8E8E8", background="#292929")
default_font = tk.font.nametofont("TkDefaultFont")
default_font.configure(size=11)
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # to fix blurry text
user32 = ctypes.windll.user32
sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
w, h = 1450, 950
# print(root.winfo_screenwidth())
root.geometry(f"{w}x{h}+{int(sw / 2 - w / 2)}+{int(sh / 2 - h / 2)}")
root.minsize(400, 200)
root.title("PictureXViewer v0.1.6a")
# root.iconphoto(False, tk.PhotoImage(file='Source/Icon/gradient_less_saturated.png'))
root.iconbitmap('Source/Icon/picturexviewer.ico')
root.tk.call('source', 'Source/Style/azure.tcl')
root.tk.call("set_theme", "dark")
app = Application(master=root)
app.mainloop()
