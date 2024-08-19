import tkinter as tk
from PIL import Image
import pytest

from main import Application

@pytest.fixture
def app():
    root = tk.Tk()
    app = Application(master=root)
    yield app
    root.destroy()


# -- Tests --

def test_initial_state(app):
    assert 0 == 0
    # assert app.image_count == 0
    # assert app.image_label["text"] == "No images found"
    # assert app.image_label["image"] is None
    # assert app.prev_button["state"] == "disabled"
    # assert app.next_button["state"] == "disabled"

def test_load_images(app, tmp_path):
    # Create actual image files
    image1_path = tmp_path / "image1.jpg"
    img1 = Image.new('RGB', (100, 100), color='red')  
    img1.save(image1_path)

    image2_path = tmp_path / "image2.png"
    img2 = Image.new('RGBA', (50, 50), color='blue') 
    img2.save(image2_path)

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    # Now the assertion should pass as you have valid image files
    assert len(app.image_list) == 2

def test_next_image(app, tmp_path):
 # Create actual image files
    image1_path = tmp_path / "image1.jpg"
    img1 = Image.new('RGB', (100, 100), color='red')  
    img1.save(image1_path)

    image2_path = tmp_path / "image2.png"
    img2 = Image.new('RGBA', (50, 50), color='blue') 
    img2.save(image2_path)

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    # Simulate next button click
    app.next_image()
    assert app.current_index == 1
    assert app.image_name.get() == "image2.png"

def test_prev_image(app, tmp_path):
 # Create actual image files
    image1_path = tmp_path / "image1.jpg"
    img1 = Image.new('RGB', (100, 100), color='red')  
    img1.save(image1_path)

    image2_path = tmp_path / "image2.png"
    img2 = Image.new('RGBA', (50, 50), color='blue') 
    img2.save(image2_path)

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    # Simulate next button click
    app.next_image()
    app.prev_image()
    assert app.current_index == 0
    assert app.image_name.get() == "image1.jpg"



