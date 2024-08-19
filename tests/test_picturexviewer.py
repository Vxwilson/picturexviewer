import tkinter as tk
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
    assert app.current_image == 0
    assert app.image_count == 0
    assert app.image_label["text"] == "No images found"
    assert app.image_label["image"] is None
    assert app.prev_button["state"] == "disabled"
    assert app.next_button["state"] == "disabled"

def test_load_images(app, tmp_path):
    # Create some test image files 
    image1_path = tmp_path / "image1.jpg"
    image1_path.touch() 
    image2_path = tmp_path / "image2.png"
    image2_path.touch()

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    assert len(app.image_list) == 2 

def test_next_image(app, tmp_path):

    # Create some test image files 
    image1_path = tmp_path / "image1.jpg"
    image1_path.touch() 
    image2_path = tmp_path / "image2.png"
    image2_path.touch()

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    # Simulate next button click
    app.next_image()
    assert app.current_image == 1
    assert app.image_label["text"] == "image2.png"

def test_prev_image(app, tmp_path):

    # Create some test image files 
    image1_path = tmp_path / "image1.jpg"
    image1_path.touch() 
    image2_path = tmp_path / "image2.png"
    image2_path.touch()

    # Simulate loading images
    app.read_im([str(image1_path), str(image2_path)])

    # Simulate next button click
    app.next_image()
    app.prev_image()
    assert app.current_image == 0
    assert app.image_label["text"] == "image1.jpg"



