# import kivy module
import kivy

# base Class of your App inherits from the App class.
# app:always refers to the instance of your application
from kivy.app import App

# The :class:`Widget` class is the base class
# required for creating Widgets.
from kivy.uix.widget import Widget

# The Label widget is for rendering text.
from kivy.uix.label import Label

# To use the checkbox must import it from this module
from kivy.uix.checkbox import CheckBox

# The GridLayout arranges children in a matrix.
# imports the GridLayout class for use in the app.
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout

from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty

from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen

import numpy as np
import ast


class payers_list(FloatLayout):

    def __init__(self, payments, **kwargs):  # payments => dict(payer: amount, ...)
        # super function can be used to gain access
        # to inherited methods from a parent or sibling class
        # that has been overwritten in a class object.
        super(payers_list, self).__init__(**kwargs)
        self.payments = payments  # dict to be provided as input
        self.payers = payments.keys()
        self.amounts = payments.values()
        self.cols_no = 2  # payer & amount
        self.rows_no = len(self.payers)
        self.result_dict = {}

        # creating payers list widget
        self.popup_grid = GridLayout(pos_hint={"x": 0, "top": 1})
        self.popup_grid.cols = self.cols_no
        self.add_widget(self.popup_grid)
        name_array = np.empty(shape=(self.rows_no, self.cols_no), dtype=object)
        for i in range(self.rows_no):
            for j in range(self.cols_no):
                name_array[i, j] = 'self.' + str(i) + '_' + str(j)

        self.dict_checkbox_instances = {}
        self.dict_names = {key: 0 for key in name_array.flatten().tolist()}
        temp_array = name_array.copy()

        i = 0
        for payer, amount in payments.items():
            temp_array[i, 0] = Label(text=payer)
            self.popup_grid.add_widget(temp_array[i, 0])
            # temp_array[i, 0].bind(text=self.on_enter)
            self.dict_checkbox_instances[temp_array[i, 0]] = temp_array[i, 0].text
            temp_array[i, 1] = TextInput(text=str(amount), multiline=False, input_filter='float')
            self.popup_grid.add_widget(temp_array[i, 1])
            temp_array[i, 1].bind(text=self.on_enter)
            self.dict_checkbox_instances[temp_array[i, 1]] = float(temp_array[i, 1].text)
            i += 1

        it = iter(self.dict_checkbox_instances.values())            # creating iterator
        self.result_dict = dict(zip(it, it))

    def on_enter(self, instance, value):
        if value == '':
            value = 0
            self.dict_checkbox_instances[instance] = value
        else:
            value = float(value)
            self.dict_checkbox_instances[instance] = value

        it = iter(self.dict_checkbox_instances.values())            # creating iterator
        self.result_dict = dict(zip(it, it))

