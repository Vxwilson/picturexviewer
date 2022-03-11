import ctypes
import math
import os
import tkinter as tk
import tkinter.filedialog as tdialog
import tkinter.ttk as ttk
import tkinter.font
import pickle
import glob
import time
from functools import partial

from PIL import Image, ImageTk, ExifTags, ImageOps


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
        self.paths = self.load_paths()
        # settings
        self.show_label = tk.BooleanVar()
        self.show_label.set(True if not self.settings_data else self.settings_data["show_label"])
        self.reopen_images_bool = tk.BooleanVar()
        self.reopen_images_bool.set(True if not self.settings_data else self.settings_data["reopen_images"])
        self.save_paths = tk.BooleanVar()
        self.save_paths.set(True if not self.settings_data else self.settings_data["save_paths"])
        self.save_zoom = tk.BooleanVar()
        self.save_zoom.set(True if not self.settings_data else self.settings_data["save_zoom"])
        # /settings
        self.exif = None
        self.filenames = None if (
                    not self.settings_data or not self.data or (self.settings_data and self.reopen_images_bool is False)) else \
        self.data["filenames"]
        self.image_list = []
        self.current_index = 0 if (
                    not self.settings_data or not self.data or (self.settings_data and self.reopen_images_bool is False)) else \
        self.data["current_index"]
        # print(self.current_index)
        self.images_len = 0
        self.index_label_text = tk.StringVar()
        self.index_label_text.set("0/0")
        self.image_name = tk.StringVar()
        self.image_name.set('')

        self.ss_label = tk.StringVar()
        self.ss_label.set("0/0")

        self.zoom_label_text = tk.StringVar()
        self.zoom_label_text.set("100%")

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
        self.actionmenu.add_command(label="Next", command=self.next_image, accelerator=">")
        self.actionmenu.add_command(label="Previous", command=self.prev_image, accelerator="<")
        self.actionmenu.add_command(label="Start Slideshow", command=self.open_slideshow_initiator, accelerator="S")
        self.menubar.add_cascade(label="Actions", menu=self.actionmenu)

        # helpmenu
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=lambda: self.open_help_window())
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        root.config(menu=self.menubar)

        # menu popup
        self.popup = tk.Menu(tearoff=0)
        self.popup.add_command(label="Show Exif", command=self.show_exif, accelerator="Ctrl+E")
        self.popup.add_separator()

        # main widgets
        self.image_test = Image.open("Source/Icon/gradient_less_saturated.png")

        self.image_canvas = tk.Canvas(width=1200, height=800, background='#3B3D3F')
        self.image_canvas.pack(anchor='center', expand='yes')
        # self.image_canvas.place(anchor='n', relx=0.5, rely=0)
        self.imscale = 1.0
        self.delta = 0.75

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
        self.index_label = ttk.Label(self.fram, textvariable=self.index_label_text, background="#333333", foreground="#81878B") \
            .place(anchor='center', relx=0.5, rely=0.5)
        self.next_button = ttk.Button(self.fram, text="Next", command=self.next_image, width=5) \
            .place(anchor='center', relx=0.55, rely=0.5)
        self.zoom_label = ttk.Label(self.fram, textvariable=self.zoom_label_text, background="#333333", foreground="#81878B") \
            .place(anchor='center', relx=0.597, rely=0.5)
        self.resize_button = ttk.Button(self.fram, text="Reset Zoom", command=self.reset_zoom, width=10) \
            .place(anchor='center', relx=0.645, rely=0.5)
        self.slideshow_button = ttk.Button(self.fram, text="Slideshow", command=self.open_slideshow_initiator).pack(
            side='right')
        self.fram.pack(side='bottom', fill='both')

        # load data
        if self.filenames is not None:
            try:
                self.read_im(self.filenames, self.current_index)
            except Exception as e:
                print(e)

        self.refresh_paths()

        self.bind_keys()
        self.resizer = None


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
        settings.focus_set()

        show_image_name = ttk.Checkbutton(master=settings, text="Show image label", variable=self.show_label)
        show_image_name.pack(side="left")
        reopen_images = ttk.Checkbutton(master=settings, text="Reopen images upon launch", variable=self.reopen_images_bool)
        reopen_images.pack(side="left")
        save_paths_button = ttk.Checkbutton(master=settings, text="Save opened file path", variable=self.save_paths)
        save_paths_button.pack(side="left")
        save_zoom_setting = ttk.Checkbutton(master=settings, text="Save zoom resolution", variable=self.save_zoom)
        save_zoom_setting.pack(side="left")

        reset_path_button = ttk.Button(master=settings, text="Reset History", command=lambda:[self.add_path(clear=True)])
        reset_path_button.pack(side="bottom")

        apply_button = ttk.Button(master=settings, text="Apply",
                                  command=lambda: [self.apply_settings(), settings.destroy()])
        apply_button.pack(side="bottom")

        settings.bind('<Escape>', lambda e: settings.destroy())

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
        # self.help_frame.lower()
        self.close_frame_button.grid(row=1, column=1)


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

    def open_fs_slideshow(self):
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
        fs_slideshow.bind("<Control-MouseWheel>", self.slideshow_wheel)
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
            self.image_canvas_ss.create_line(self.image_canvas_ss.winfo_width() / 2, 0,
                                             self.image_canvas_ss.winfo_width() / 2, self.image_canvas_ss.winfo_height(),
                                             fill='#3F4344', width=3, dash=(4, 2))

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
            self.image_canvas_ss.create_line(self.image_canvas_ss.winfo_width() / 3, 0,
                                             self.image_canvas_ss.winfo_width() / 3,
                                             self.image_canvas_ss.winfo_height(),
                                             fill='#3F4344', width=3, dash=(4, 2))
            self.image_canvas_ss.create_line(self.image_canvas_ss.winfo_width() / 3 * 2, 0,
                                             self.image_canvas_ss.winfo_width() / 3 * 2,
                                             self.image_canvas_ss.winfo_height(),
                                             fill='#3F4344', width=3, dash=(4, 2))
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
        self.last_view_time = time.time()
        self.set_timer()

        self.index_label = ttk.Label(self.image_canvas_ss, textvariable=self.ss_label, background="#3B3D3F", foreground="#81878B") \
            .place(anchor='center', relx=0.5, rely=0.95)

        self.update_label(1)

    def show_exif(self):
        exif_window = tk.Toplevel(root)
        exif_window.title("EXIF")
        exif_window.minsize(250, 50)
        exif_window.geometry(f"+{int(root.winfo_width() / 2)}+{int(root.winfo_height() / 2)}")
        exif_window.focus_set()
        exif_window.resizable(False, False)
        # exif_window.overrideredirect(True)

        exif_frame = ttk.LabelFrame(exif_window, text="")
        exif_frame.pack()
        dimension_label = ttk.Label(master=exif_frame, text="Dimensions:")
        dimension_text = ttk.Label(exif_frame, text="-")
        model_label = ttk.Label(master=exif_frame, text="Model:")
        model_text = ttk.Label(exif_frame, text="-")
        date_label = ttk.Label(master=exif_frame, text="Date taken:")
        date_text = ttk.Label(exif_frame, text="-")
        focal_length_label = ttk.Label(master=exif_frame, text="Focal length(mm):")
        focal_length_text = ttk.Label(exif_frame, text="-")
        misc_label = ttk.Label(master=exif_frame, text="Misc:")
        misc_text = ttk.Label(exif_frame, text="-")
        if self.exif and self.exif[self.current_index]:
            if 256 in self.exif[self.current_index]:
                dimension_text['text'] = f"{self.exif[self.current_index][256]}x{self.exif[self.current_index][257]}"
            else:
                dimension_text['text'] = f"{self.image_list[self.current_index].size[0]}x" \
                                         f"{self.image_list[self.current_index].size[1]}"
            if 272 in self.exif[self.current_index]:
                model_text['text'] = f"{self.exif[self.current_index][272]}"
            if 306 in self.exif[self.current_index]:
                date_text['text'] = f"{self.exif[self.current_index][306]}"
            elif 36867 in self.exif[self.current_index]:
                date_text['text'] = f"{self.exif[self.current_index][36867]}"
            if 37386 in self.exif[self.current_index]:
                focal_length_text['text'] = f"{self.exif[self.current_index][37386]}"
            if 39321 in self.exif[self.current_index]:
                misc_text['text'] = f"{self.exif[self.current_index][39321]}"


        dimension_label.grid(row=0, column=0, sticky="w", ipadx=15, padx=5, pady=5)
        dimension_text.grid(row=0, column=1, sticky="w", ipadx=15, padx=5, pady=5)
        model_label.grid(row=1, column=0, sticky="w", ipadx=15, padx=5, pady=5)
        model_text.grid(row=1, column=1, sticky="w", ipadx=15, padx=5, pady=5)
        date_label.grid(row=2, column=0, sticky="w", ipadx=15, padx=5, pady=5)
        date_text.grid(row=2, column=1, sticky="w", ipadx=15, padx=5, pady=5)
        focal_length_label.grid(row=3, column=0, sticky="w", ipadx=15, padx=5, pady=5)
        focal_length_text.grid(row=3, column=1, sticky="w", ipadx=15, padx=5, pady=5)
        misc_label.grid(row=4, column=0, sticky="w", ipadx=15, padx=5, pady=5)
        misc_text.grid(row=4, column=1, sticky="w", ipadx=15, padx=5, pady=5)


        exif_frame.grid_rowconfigure([0, 1, 2, 3], weight=1)
        exif_frame.grid_columnconfigure([0, 1], weight=1)

        exif_window.bind('<Escape>', lambda e: exif_window.destroy())

    def bind_keys(self):
        self.image_canvas.bind('<MouseWheel>', self.wheel)  # TODO add control-mousewheel to navigate images

        # shortcuts
        root.bind("<Button-3>", self.menu_popup)


        root.bind('<Control-o>', lambda e: self.select_images())
        root.bind('<Control-s>', lambda e: self.save_data())

        #popup menu
        root.bind('<Control-e>', lambda e: self.show_exif())

        root.bind('<Alt-p>', lambda e: self.open_settings_())
        root.bind('<Alt-x>', lambda e: root.quit())

        root.bind('<Left>', lambda e: self.prev_image())
        root.bind('<Right>', lambda e: self.next_image())

        root.bind('<s>', lambda e: self.open_slideshow_initiator())

        # auto resize image
        root.bind('<Configure>', self.check_image_resize)

    def check_image_resize(self, event):
        # print(event.width)   # unreliable as final width is not correct
        if self.resizer is not None:
            root.after_cancel(self.resizer)
        self.resizer = root.after(400, self.update_image)


    def menu_popup(self, event):
        try:
            self.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup.grab_release()


    def slideshow_wheel(self, event):
        if event.delta > 0:
            self.prev_image_slideshow()
        elif event.delta < 0:
            self.next_image_slideshow()


    def wheel(self, event):
        scale = 1.0
        print(event.delta)  # multiples of 120  # TODO: scroll size based on delta
        # if event.delta == -120:
        if event.delta < 0:
            scale *= self.delta
            self.imscale *= self.delta
            print('zooming out')
            scale = max(scale, 0.1)
            self.imscale = max(self.imscale, 0.1)
        # if event.delta == 120:
        elif event.delta > 0:
            scale /= self.delta
            self.imscale /= self.delta
            print('zooming in')

            scale = min(scale, 2.25)
            self.imscale = min(self.imscale, 2.25)

        x = self.image_canvas.canvasx(event.x)
        y = self.image_canvas.canvasy(event.y)
        # self.image_canvas.scale('all', x, y, scale, scale)
        self.image_canvas.scale('all', self.image_canvas.winfo_width()/2, self.image_canvas.winfo_height()/2, scale, scale)
        # self.image_canvas.config(width=self.image_canvas.winfo_width()*scale, height=self.image_canvas.winfo_height()*scale)

        self.update_zoom()
        self.update_image()

    def reset_zoom(self):
        self.imscale = 1
        self.update_image()
        self.update_zoom()


    def resizing(self, mode=0, event=None):
        # self.image_canvas.configure(width=root.winfo_height() * 0.9 * 9 / 16, height=root.winfo_height() * 0.9)
        if self.image_test:  # true in most times
            # print(f"width, height: {self.image_test.width}, {self.image_test.height}")
            iw, ih = self.image_test.width, self.image_test.height
            new_size = int(1), int(1)
            # mw, mh = self.master.winfo_width(), self.master.winfo_height()
            if mode == 0:
                mw, mh = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()

            # slideshow modes
            elif mode == 1:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.99
            elif mode == 2:
                mw, mh = self.image_canvas_ss.winfo_width(), self.image_canvas_ss.winfo_height() * 0.98
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

            # test
            if mode == 0:
                im1 = ImageTk.PhotoImage(self.image_test.resize((int(iw * self.scale * self.imscale), int(ih * self.scale * self.imscale))))
                return im1
            else:
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
        if self.filenames:
            if self.save_paths.get():
                self.add_path(self.filenames)
            self.refresh_paths()
            self.read_im(self.filenames)

    def add_path(self, filename="", clear=False):
        if clear:
            print('clear')
            data = {}
            with open('Source/paths.txt', 'wb') as file:
                pickle.dump(data, file)
            self.paths = self.load_paths()
        else:
            if self.paths:
                self.paths.append({'path': filename})
                data = {'entry': self.paths}
            else:
                data = {"entry": [{"path": filename}]}
            with open('Source/paths.txt', 'wb') as file:
                pickle.dump(data, file)
            self.paths = self.load_paths()

    def refresh_paths(self):  # TODO maybe remove middle part of a path, making path easier to recognize
        try:
            self.filemenu.delete("Open recent")
        except:
            pass

        if not self.save_paths.get():
            self.add_path(clear=True)

        if self.paths and bool(self.paths) and self.save_paths.get() is True:
            nested_menu = tk.Menu(self.filemenu)

            for index, profile in enumerate(reversed(self.paths)):  # limit entries to 15
                if index == 15:
                    break
                nested_menu.add_command(label=f"{(index+1)}: {profile['path'][0][0:100]}...", command=partial(self.read_im, profile["path"]))
            # self.filemenu.add_cascade(label="Open recent", menu=nested_menu, index=1)
            self.filemenu.insert_cascade(label="Open recent", menu=nested_menu, index=1)

    def load_paths(self):
        if os.path.exists('Source/paths.txt'):
            try:
                with open('Source/paths.txt', 'r+b') as file:
                    return pickle.load(file)["entry"]
            except (EOFError, KeyError) as e:
                print(e)
                return {}
        else:
            return {}

    def read_im(self, images, index=0):
        try:
            self.image_list = [Image.open(item) for item in images]
            self.images_len = len(self.image_list)
        except AttributeError:  # image not found
            print("error")
            pass

        try:
            # tags
            # 256: width; 257: height; 271: brand; 272: model; 274: orientation; 37386: focal length; 306: date
            self.exif = [image._getexif() for image in self.image_list]

            # for e in self.exif:
            #         print(e)
        except AttributeError:
            print("no exif detected")


        self.current_index = 0
        self.save_settings()
        self.update_label()
        self.open_image_at(index)

    def update_label(self, mode=0):
        if mode == 0:
            self.index_label_text.set(f"{self.current_index + 1}/{self.images_len}")
            if self.show_label.get():
                self.image_name.set(f"{self.image_test.filename.split('/')[-1]}")
            else:
                self.image_name.set("")
        elif mode == 1:  # slideshow label
            self.ss_label.set(f"{self.current_index + 1}/{self.images_len}")

    def update_zoom(self):
        x = "{:.0f}".format(self.imscale * 100)
        self.zoom_label_text.set(f"{x}%")
        # if self.show_label.get():
        #     self.image_name.set(f"{self.image_test.filename.split('/')[-1]}")
        # else:
        #     self.image_name.set("")

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
        if self.save_zoom.get() is False:
            self.reset_zoom()

    def next_image(self, ite=1):
        if self.current_index + ite >= self.images_len:
            self.current_index = 0
        else:
            self.current_index += ite
        self.open_image_at(self.current_index)
        if self.save_zoom.get() is False:
            self.reset_zoom()

    def next_image_slideshow(self):
        self.last_view_time = time.time()

        # if self.image_canvas_ss is not None:
        #     # self.image_canvas_ss.delete('all')

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

            self.update_label(1)

    def prev_image_slideshow(self):
        self.last_view_time = time.time()

        # if self.image_canvas_ss is not None:
        #     self.image_canvas_ss.delete('all')

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
            self.update_label(1)


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
        self.refresh_paths()
        self.save_settings()

    def save_settings(self):
        self.save_data()
        data = {'show_label': self.show_label.get(),
                'reopen_images': self.reopen_images_bool.get(),
                'save_paths' : self.save_paths.get(),
                'save_zoom' : self.save_zoom.get(),
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
        if self.reopen_images_bool.get() is False:
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
root.title("PictureXViewer v0.2.0a")
# root.iconphoto(False, tk.PhotoImage(file='Source/Icon/gradient_less_saturated.png'))
root.iconbitmap('Source/Icon/picturexviewer.ico')
root.tk.call('source', 'Source/Style/azure.tcl')
root.tk.call("set_theme", "dark")
app = Application(master=root)
app.mainloop()
