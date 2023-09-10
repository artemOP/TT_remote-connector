import asyncio
import logging

import dearpygui.dearpygui as dpg


class DpgServer:
    def __init__(self, lock: asyncio.Event):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.lock = lock

    def enter(self):
        dpg.create_context()
        dpg.create_viewport()
        dpg.setup_dearpygui()
        logging.debug("backend created")
        with dpg.window():
            dpg.add_text("Hello World Text")
            dpg.add_button(label="Button", callback=self.print_callback)
            dpg.add_input_text(label="string")
            dpg.add_slider_float(label="float")
        logging.debug("window populated")

        dpg.show_viewport()
        logging.debug("viewport displayed")
        logging.debug("gui started")

        while dpg.is_dearpygui_running() and self.lock.is_set():
            dpg.render_dearpygui_frame()
        logging.debug("lock released")
        dpg.destroy_context()
        dpg.cleanup_dearpygui()
        logging.debug("Context destroyed")

    def print_callback(self):
        logging.debug("Callback")
