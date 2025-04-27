import flet as ft


class CustomListTile(ft.ListTile):
    def __init__(
        self,
        leading=None,
        title=None,
        subtitle=None,
        trailing=None,
        on_click=None,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=10),
        min_leading_width=64,
        min_height=72,
    ):
        super().__init__(
            leading=leading,
            title=title,
            subtitle=subtitle,
            trailing=trailing,
            on_click=on_click,
            dense=dense,
            content_padding=content_padding,
            min_leading_width=min_leading_width,
            min_height=min_height,
        )
        if title and isinstance(title, ft.Text):
            title.no_wrap = False
            title.overflow = ft.TextOverflow.VISIBLE
        if subtitle and isinstance(subtitle, ft.Text):
            subtitle.no_wrap = False
            subtitle.overflow = ft.TextOverflow.VISIBLE
