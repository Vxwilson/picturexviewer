import os
import pickle
import time
from PIL import Image
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import QSize

class LogicManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Internal Cache
        self._pixmap_cache = {}
        self._exif_cache = {}
        
    def load_settings(self):
        path = os.path.join(self.data_dir, 'settings.txt')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as file:
                    return pickle.load(file)
            except Exception:
                return {}
        return {}
        
    def save_settings(self, data):
        path = os.path.join(self.data_dir, 'settings.txt')
        with open(path, 'wb') as file:
            pickle.dump(data, file)
            
    def load_data(self, reopen_images_bool):
        if not reopen_images_bool:
            return {}
        path = os.path.join(self.data_dir, 'save.txt')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as file:
                    return pickle.load(file)
            except Exception:
                return {}
        return {}
        
    def save_data(self, data):
        path = os.path.join(self.data_dir, 'save.txt')
        with open(path, 'wb') as file:
            pickle.dump(data, file)
            
    def load_paths(self):
        path = os.path.join(self.data_dir, 'paths.txt')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as file:
                    return pickle.load(file).get("entry", [])
            except Exception:
                return []
        return []
        
    def save_paths(self, paths):
        path = os.path.join(self.data_dir, 'paths.txt')
        with open(path, 'wb') as file:
            pickle.dump({"entry": paths}, file)

    def get_supported_extensions(self):
        formats = QImageReader.supportedImageFormats()
        extensions = set()
        for f in formats:
            ext = f.data().decode().lower()
            extensions.add(f".{ext}")
            if ext == 'jpeg': extensions.add('.jpg')
            if ext == 'jpg': extensions.add('.jpeg')
            if ext == 'tiff': extensions.add('.tif')
            if ext == 'tif': extensions.add('.tiff')
            
        common = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.heic')
        for ext in common:
            extensions.add(ext)
        return tuple(sorted(list(extensions)))

    def clear_cache(self):
        self._pixmap_cache.clear()
        self._exif_cache.clear()

    def get_pixmap(self, filenames, index):
        if index < 0 or index >= len(filenames):
            return QPixmap()
            
        if index in self._pixmap_cache:
            return self._pixmap_cache[index]
            
        f_path = filenames[index]
        if not os.path.exists(f_path):
            return QPixmap()
            
        try:
            pixmap = QPixmap(f_path)
            if len(self._pixmap_cache) > 10:
                first_key = next(iter(self._pixmap_cache))
                del self._pixmap_cache[first_key]
            self._pixmap_cache[index] = pixmap
            return pixmap
        except Exception:
            return QPixmap()

    def get_exif(self, filenames, index):
        if index < 0 or index >= len(filenames):
            return None
            
        if index in self._exif_cache:
            return self._exif_cache[index]
            
        f_path = filenames[index]
        if not os.path.exists(f_path):
            return None
            
        try:
            with Image.open(f_path) as img:
                exif = img._getexif()
                self._exif_cache[index] = exif
                return exif
        except Exception:
            return None

    def scan_for_images(self, paths):
        all_images = []
        extensions = self.get_supported_extensions()
        paths.sort()
        
        for path in paths:
            if os.path.isdir(path):
                try:
                    folder_images = []
                    for root, dirs, files in os.walk(path):
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        for file in files:
                            if file.startswith('.'):
                                continue
                            if file.lower().endswith(extensions):
                                folder_images.append(os.path.join(root, file))
                    folder_images.sort()
                    all_images.extend(folder_images)
                except Exception:
                    pass
            elif os.path.isfile(path):
                filename = os.path.basename(path)
                if not filename.startswith('.') and path.lower().endswith(extensions):
                    all_images.append(path)
        
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                unique_images.append(img)
                seen.add(img)
        return unique_images
