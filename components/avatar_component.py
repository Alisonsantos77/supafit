import flet as ft


class AvatarComponent(ft.CircleAvatar):
    def __init__(self, image_url, radius=50, **kwargs):
        super().__init__(foreground_image_src=image_url, radius=radius, **kwargs)
        self.image_url = image_url
        self.on_click = self.handle_click

    def handle_click(self, e):
        print("Avatar clicked!")

    def build(self):
        return self
