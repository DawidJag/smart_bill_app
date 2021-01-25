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
from kivy.graphics import Color, Rectangle
from kivy.graphics.instructions import Canvas
from kivy.clock import Clock

from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen

import numpy as np
import ast


class check_box_matrix(FloatLayout):
    # matrix = ObjectProperty(None)

    def __init__(self, rows_no, cols_no, exp_split_matrix, **kwargs):
        # super function can be used to gain access
        # to inherited methods from a parent or sibling class
        # that has been overwritten in a class object.
        super(check_box_matrix, self).__init__(**kwargs)
        self.cols_no = cols_no + 2  # first two columns: item_name, amount
        self.rows_no = rows_no + 1
        # self.labels = ['Item', 'Amount'] + labels  # columns names          @@@@@ tutaj wczytać pierwszy wiersz nowej macierzy exp_split_matrix z db
        self.labels = np.array(ast.literal_eval(exp_split_matrix))[0,:]
        # print(type(self.labels))

        self.result_matrix = np.empty(shape=(self.rows_no, self.cols_no), dtype=object)   # matrix returned with values from all children widgets

        # preparation of input_matrix
        items = ['item ' + str(x) for x in range(1, 11)]  # fixed no. of rows => 10
        items = np.array(items).reshape((-1, 1))
        zeros = np.zeros((10, 1))
        checks = np.ones((10, cols_no))
        tmp_default_array = np.concatenate((items, zeros, checks), axis=1)
        if exp_split_matrix:
            tmp_input_array = np.array(ast.literal_eval(exp_split_matrix))[1:, :]  # exp_split_matrix => string
            row = tmp_input_array.shape[0]
            col = tmp_input_array.shape[1]
            tmp_default_array[0:row, 0:col] = tmp_input_array
        input_matrix = tmp_default_array
        # print('input matrix')
        # print(input_matrix)

        # creating checkbox matrix widget
        self.popup_grid = GridLayout(pos_hint={"x": 0, "top": 1})
        self.popup_grid.bind(minimum_height=self.popup_grid.setter('height'))
        self.popup_grid.cols = self.cols_no
        self.add_widget(self.popup_grid)

        name_array = np.empty(shape=(self.rows_no, self.cols_no), dtype=object)
        for i in range(self.rows_no):
            for j in range(self.cols_no):
                name_array[i, j] = 'self.' + str(i) + '_' + str(j)

        self.dict_checkbox_instances = {}
        self.dict_names = {key: 0 for key in name_array.flatten().tolist()}

        temp_array = name_array.copy()

        for label in self.labels:
            k=0
            # self.popup_grid.add_widget(Label(text=label, color=[0.031, 0.792, 0.945, 1]))
            temp_array[0,k] = Label(text=label, color=[1, 1, 1, 1], bold=True)
            self.popup_grid.add_widget(temp_array[0, k])
            self.dict_checkbox_instances[temp_array[0, k]] = label
            k += 1
            # print('label: ' + label)
            # print(type(label))
            # print('label string: ' + str(label))
            # print(type(str(label)))
            # print(self.dict_checkbox_instances[temp_array[0, k]])
        # print('dict_checkbox_instances: ' + str(self.dict_checkbox_instances))

        for i in range(1, self.rows_no):

            # temp_array[i, 0] = TextInput(text='item ' + str(i + 1))
            # temp_array[i, 0] = TextInput(text=input_matrix[i, 0])
            temp_array[i, 0] = TextInput(text=input_matrix[i-1, 0])
            self.popup_grid.add_widget(temp_array[i, 0])  # !!! change label text to something different
            temp_array[i, 0].bind(text=self.on_enter, focus=self.on_focus)
            self.dict_checkbox_instances[temp_array[i, 0]] = (temp_array[i, 0].text)

            # temp_array[i, 1] = TextInput(text='0', multiline=False, input_filter='float')
            # temp_array[i, 1] = TextInput(text=input_matrix[i, 1], multiline=False, input_filter='float', halign='right')
            temp_array[i, 1] = TextInput(text=input_matrix[i-1, 1], multiline=False, input_filter='float', halign='right')
            self.popup_grid.add_widget(temp_array[i, 1])  # !!! change label text to something different
            temp_array[i, 1].bind(text=self.on_enter, focus=self.on_focus)
            self.dict_checkbox_instances[temp_array[i, 1]] = (temp_array[i, 1].text)

            for j in range(2, self.cols_no):
                # checked = bool(input_matrix[i, j].astype(np.float))
                checked = bool(input_matrix[i-1, j].astype(np.float))
                temp_array[i, j] = CheckBox(active=checked, color=[0, 0, 0, 0.6])

                self.popup_grid.add_widget(temp_array[i, j])
                temp_array[i, j].bind(active=self.on_checkbox_Active)
                self.dict_checkbox_instances[temp_array[i, j]] = int(temp_array[i, j].active)

        # print(self.dict_checkbox_instances)
        # print(np.array(list(self.dict_checkbox_instances.values())).shape)
        self.result_matrix = np.array(list(self.dict_checkbox_instances.values())).reshape((self.rows_no, self.cols_no))

    def on_checkbox_Active(self, checkboxInstance, isActive):

        if isActive:
            self.dict_checkbox_instances[checkboxInstance] = 1
            for key_a, key_b in zip(self.dict_names, self.dict_checkbox_instances):
                self.dict_names[key_a] = self.dict_checkbox_instances[key_b]

            self.result_matrix = np.array(list(self.dict_checkbox_instances.values())).reshape(
                (self.rows_no, self.cols_no))
        else:
            self.dict_checkbox_instances[checkboxInstance] = 0
            for key_a, key_b in zip(self.dict_names, self.dict_checkbox_instances):
                self.dict_names[key_a] = self.dict_checkbox_instances[key_b]

            self.result_matrix = np.array(list(self.dict_checkbox_instances.values())).reshape(
                (self.rows_no, self.cols_no))

    def on_enter(self, instance, value):
        self.dict_checkbox_instances[instance] = value
        self.result_matrix = np.array(list(self.dict_checkbox_instances.values())).reshape((self.rows_no, self.cols_no))

    def on_focus(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: instance.select_all())


# class CheckBoxApp(App):
#     def build(self):
#         # build is a method of Kivy's App class used
#         # to place widgets onto the GUI.
#
#         return check_box_matrix(rows_no=4, cols_no=5)
#
#     # Run the app
#
#
# if __name__ == '__main__':
#     CheckBoxApp().run()