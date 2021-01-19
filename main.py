import kivy
import numpy as np
import ast
from database import DataBase
from checkbox_matrix import check_box_matrix
from payers_list import payers_list
from app_engine import Settlement, Receipt
from pdf_creator import save_report
import os.path
from os import listdir
from os.path import dirname
import webbrowser
# from android.storage import primary_external_storage_path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, CardTransition
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

# from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView


# from kivy.properties import NumericProperty


class MainWindow(Screen):
    sett_list = BoxLayout()

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

    def on_enter(self):
        self.sett_list.clear_widgets()
        self.show_RV()

    def show_RV(self):  # items
        self.sett_names = db.get_settlements_list()

        self.sett_amounts = []
        for settlement in self.sett_names:
            self.sett_amounts.append(db.get_settlement_amount(settlement))

        # input list to create recycle view with settlements
        self.items = []
        for name, amount in zip(self.sett_names, self.sett_amounts):
            temp_dict = {}
            temp_dict = {'col_1': name, 'col_2': amount, 'col_3': name, 'col_4': name, 'col_5': name}
            self.items.append(temp_dict)

        # self.sett_list.bind(minimum_height=self.sett_list.setter('height'))
        self.recycle_view = RV(items=self.items)

        self.sett_list.add_widget(self.recycle_view)

    def addSettBtn(self):
        AddSettlementWindow.s_name = ""
        AddSettlementWindow.part_list = ""
        AddSettlementWindow.prev_screen = "main"

    # settlement's list
    def addRecBtn(self, settlement):
        participants = db.get_settlement_participants(settlement)
        if participants:
            rows = 10
            cols = len(participants.split(','))
            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            array_converted = str(array.tolist())
            AddReceiptWindow.r_exp_split = array_converted

        AddReceiptWindow.s_name = settlement
        AddReceiptWindow.part_list = str(participants.split(','))
        AddReceiptWindow.prev_screen = "main"

    def editSettBtn(self, settlement):
        AddSettlementWindow.s_name = settlement
        AddSettlementWindow.part_list = db.get_settlement_participants(settlement)
        AddSettlementWindow.prev_screen = "main"

    def delSettBtn(self, settlement):
        DelSettConfWindow.s_name = settlement
        DelSettConfWindow.prev_screen = "main"

    def youtubeBtn(self):
        webbrowser.open('http://youtube.com')


class DelSettConfWindow(Screen):
    sett_name = ObjectProperty(None)
    s_name = ""

    def on_enter(self):
        self.sett_name.text = self.s_name

    def delSett(self):
        db.delete_settlement(self.s_name)



class DelRecConfWindow(Screen):
    sett_name = ObjectProperty(None)
    rec_name = ObjectProperty(None)
    s_name = ""
    r_name = ""

    # def on_enter(self):
    #     self.rec_name.text = self.r_name
    #     self.sett_name.text = self.s_name

    def delRec(self):
        db.delete_record(self.s_name, self.r_name)
        app = App.get_running_app()
        screen_manager = app.root.ids['screen_manager']
        screen_manager.current = 'add_settl'


class UpdateSettConfWindow(Screen):
    pass


class ReportsWindow(Screen):
    sett_list = BoxLayout()

    def __init__(self, **kwargs):
        super(ReportsWindow, self).__init__(**kwargs)

    def on_enter(self):
        self.sett_list.clear_widgets()
        self.show_RV_rep()

    def show_RV_rep(self):  # items
        self.sett_names = db.get_settlements_list()

        # input list to create recycle view with settlements
        self.items = []
        for name in self.sett_names:
            temp_dict = {}
            temp_dict = {'col_1_rep': name, 'col_2_rep': name, 'col_3_rep': name}
            self.items.append(temp_dict)

        # self.sett_list.bind(minimum_height=self.sett_list.setter('height'))
        recycle_view = RV_rep(items=self.items)
        self.sett_list.add_widget(recycle_view)

    def show(self, settlement_name):
        report = run_settlement(settlement_name)
        settl_report(report)  # popup window with final report

    def pdfReport(self, settlement_name):
        payments = run_settlement(settlement_name)
        save_report(settlement_name, payments)
        # popup window
        label = Label(text='Report has been saved in:\n\n internal_storage/Sm@rt_Bill/reports', halign='center',
                      size_hint=(1, 0.8), pos_hint={"x": 0, "top": 1})
        box = FloatLayout(cols=1)
        box.add_widget(label)
        backBtn = Button(text='OK', size_hint=(0.4, 0.15), pos_hint={"x": 0.3, "top": 0.2})
        box.add_widget(backBtn)

        pop = Popup(title='Payments', content=box, size_hint=(0.8, 0.4), )
        backBtn.bind(on_press=pop.dismiss)
        pop.open()


def run_settlement(settlement_name):
    # load data from db to the engine
    participants = db.get_settlement_participants(settlement_name).split(',')
    receipts_list = db.get_receipts_list(settlement_name)

    settlement = Settlement(participants, settlement_name)

    for receipt_name in receipts_list:
        record = db.get_record_data(settlement_name, receipt_name)
        if receipt_name:
            receipt = Receipt(participants, float(record['amount']), ast.literal_eval(record['payments']),
                              record['exp_split_matrix'],
                              record['category'], record['date'], record['remarks'])
            settlement.add_receipt_to_settlement(receipt)

    report = settlement.final_payments_report()
    return report


def settl_report(payments):  # payments => dict
    # dodac wyliczanie defualt height
    default_height = 50
    layout_popup = GridLayout(cols=1, spacing=5, size_hint_y=None, row_default_height=default_height,
                              row_force_default=True)  # gridlayout do dodania do scrollview
    layout_popup.bind(minimum_height=layout_popup.setter('height'))

    for payer, transfers in payments.items():
        # box = BoxLayout(orientation='vertical', spacing=10, size_hint_y='200dp')            # size_hint_y=Non           # box dla danego płacącego
        # layout_popup.add_widget(box)
        # box.add_widget(Label(text= str(payer) + ' should make below transfers:\n'))                 # etykieta kto płaci

        layout_popup.add_widget(Label(text=str(payer) + ' should make below transfers:'))

        for receiver, amount in transfers.items():
            inside_box = GridLayout(cols=2, spacing=10)  # linia płatności
            label_rec = Label(text=receiver + ': ')
            label_amt = Label(text=str(amount))
            inside_box.add_widget(label_rec)
            inside_box.add_widget(label_amt)

            # box.add_widget(inside_box)
            layout_popup.add_widget(inside_box)

    # scroll_rep = ScrollView(size=(Window.width, Window.height), pos_hint={"x":0, "top":1})        # size_hint=(1, 0.8),
    scroll_rep = ScrollView(size_hint=(1, 0.8), pos_hint={"x": 0, "top": 1})
    scroll_rep.add_widget(layout_popup)
    box = FloatLayout(cols=1)
    box.add_widget(scroll_rep)
    backBtn = Button(text='Back', size_hint=(0.4, 0.15), pos_hint={"x": 0.3, "top": 0.2})
    box.add_widget(backBtn)

    pop = Popup(title='Payments', content=box, size_hint=(0.9, 0.9))
    backBtn.bind(on_press=pop.dismiss)
    pop.open()


class AddSettlementWindow(Screen):
    particip_list = ObjectProperty(None)
    settl_name = ObjectProperty(None)
    rec_list = BoxLayout()
    part_list = ""
    s_name = ""
    prev_screen = ""
    s_name_old = ""
    part_list_old = ""

    def on_enter(self):
        app = App.get_running_app()
        app.root.ids.settl_name.text = self.s_name
        self.particip_list.text = self.part_list  # string
        self.rec_list.clear_widgets()
        self.show_rec_RV()
        self.s_name_old = self.s_name
        self.part_list_old = self.part_list
        # print(self.s_name)

    # ******************* Receipts list
    def show_rec_RV(self):  # items
        if self.s_name:
            receipts = list(filter(None, db.get_receipts_list(self.s_name)))
            receipts = sorted(receipts, key=str.lower)
            self.rec_names = receipts
        else:
            self.rec_names = []

        self.rec_amounts = []
        if self.rec_names:
            for receipt in self.rec_names:
                self.rec_amounts.append(db.get_receipt_amount(self.s_name, receipt))

        # input list to create recycle view with receipts
        self.items = []
        for name, amount in zip(self.rec_names, self.rec_amounts):
            temp_dict = {}
            temp_dict = {'col_1_rec': name, 'col_2_rec': amount, 'col_3_rec': name, 'col_4_rec': name,
                         'col_5_rec': name}
            self.items.append(temp_dict)

        # self.rec_list.bind(minimum_height=self.rec_list.setter('height'))
        recycle_view = RV_rec(items=self.items)
        self.rec_list.add_widget(recycle_view)

    def editRecBtn(self, receipt):
        record = db.get_record_data(self.s_name, receipt)
        exp_matrix = db.get_exp_split_matrix(self.s_name, receipt)
        AddReceiptWindow.r_exp_split = exp_matrix
        AddReceiptWindow.editPressed = 1
        AddReceiptWindow.s_name = self.s_name
        AddReceiptWindow.r_name = receipt
        AddReceiptWindow.part_list = record['participants']
        AddReceiptWindow.r_amount = record['amount']
        AddReceiptWindow.r_date = record['date']
        AddReceiptWindow.r_category = record['category']
        AddReceiptWindow.r_remarks = record['remarks']
        AddReceiptWindow.prev_screen = "add_settl"

        # print('edit pressed: ' + str(AddReceiptWindow.editPressed))

    def delRecBtn(self, receipt):
        DelRecConfWindow.s_name = self.s_name
        DelRecConfWindow.r_name = receipt
        DelRecConfWindow.prev_screen = "add_settl"

    # ****************************************

    # def updateBtn(self):
    #     receipts_list = db.get_receipts_list(self.s_name_old)
    #     self.s_name = self.settl_name.text
    #     self.part_list = self.particip_list.text
    #     for receipt in receipts_list:
    #         db.update_record(old_settlement=self.s_name_old, new_settlement=self.s_name,
    #                          participants=str(self.part_list.split(',')),
    #                          old_receipt=receipt, new_receipt=receipt)

    def updateSett(self):
        receipts_list = db.get_receipts_list(self.s_name_old)
        AddSettlementWindow.s_name = self.settl_name.text
        AddSettlementWindow.part_list = self.particip_list.text
        for receipt in receipts_list:
            db.update_record(old_settlement=self.s_name_old, new_settlement=self.s_name,
                             participants=str(self.part_list.split(',')),
                             old_receipt=receipt, new_receipt=receipt)

        if self.s_name_old != self.settl_name.text:
            db.delete_settlement(self.s_name_old)

    def updateDismiss(self):
        self.particip_list.text = self.part_list_old
        self.settl_name.text = self.s_name_old

    def addRecBtn(self):
        AddReceiptWindow.s_name = self.settl_name.text
        AddReceiptWindow.part_list = str(self.particip_list.text.split(','))
        AddSettlementWindow.s_name = self.settl_name.text
        AddSettlementWindow.part_list = self.particip_list.text

        if self.particip_list.text:
            rows = 10
            cols = len(self.particip_list.text.split(','))
            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            array_converted = str(array.tolist())
            AddReceiptWindow.r_exp_split = array_converted

        AddReceiptWindow.prev_screen = "add_settl"

    # def addSettleBtn(self):         # dodać zapisywanie, jeśli nic sie nie zmieniło !!!!!!!!!!!!!
    #     if self.settl_name.text != "" and self.particip_list.text != "":
    #         db.add_record(settlement=self.settl_name.text, participants=str(self.particip_list.text.split(',')))
    #         self.reset()
    #     else:
    #         invalidForm()

    def addSettleBtn(self):
        # adding new settlement
        if (self.s_name_old == "" and self.part_list_old == ""):
            if self.settl_name.text != "" and self.particip_list.text != "":
                db.add_record(settlement=self.settl_name.text, participants=str(self.particip_list.text.split(',')))
                self.reset()
            else:
                invalidForm()
        # saving after change of sett. name or participants list
        elif self.s_name_old != self.settl_name.text or self.part_list_old != self.particip_list.text:
            self.updateSett()
        else:
            pass

    def cancelBtn(self):
        self.reset()

    def reset(self):
        self.particip_list.text = ''
        self.settl_name.text = ''


class AddReceiptWindow(Screen):
    sett_name = ObjectProperty(None)
    rec_name = ObjectProperty(None)
    amount = ObjectProperty(None)
    date = ObjectProperty(None)
    category = ObjectProperty(None)
    remarks = ObjectProperty(None)
    payers_list = ObjectProperty(None)

    s_name = ""
    r_name = ""
    s_name_old = ""
    r_name_old = ""
    r_amount = ""
    r_date = ""
    r_category = ""
    r_remarks = ""
    r_payments = ""
    r_payments_tmp = ""
    part_list = ""
    r_exp_split = ""  # string

    editPressed = ""
    prev_screen = ""

    def on_enter(self, *args):
        self.sett_name.text = self.s_name
        self.rec_name.text = self.r_name
        self.amount.text = self.r_amount
        self.date.text = self.r_date
        self.category.text = self.r_category
        self.remarks.text = self.r_remarks
        self.s_name_old = self.s_name  # saving old settlement name in separate variable
        self.r_name_old = self.r_name

    def exp_split(self, screen_name):
        # add to db or update
        if AddReceiptWindow.editPressed:
            self.dbUpdateRec()
        else:
            self.dbAddRec()

        ExpSplitWindow.s_name = self.sett_name.text
        ExpSplitWindow.r_name = self.rec_name.text
        ExpSplitWindow.r_amount = self.amount.text
        ExpSplitWindow.r_date = self.date.text
        ExpSplitWindow.r_category = self.category.text
        ExpSplitWindow.r_remarks = self.remarks.text

        rows = 10  # to be change to dynamic
        labels = ast.literal_eval(self.part_list)
        cols = len(labels)

        if not self.r_exp_split:  # self.r_exp_split => string
            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            self.r_exp_split = str(array.tolist())

        app = App.get_running_app()
        screen_manager = app.root.ids['screen_manager']
        screen = screen_manager.get_screen(screen_name)

        ExpSplitWindow.input_exp_matrix = self.r_exp_split
        ExpSplitWindow.show_exp_split(screen, rows, cols, labels)

    def payersBtn(self):
        try:
            record = db.get_record_data(self.s_name, self.r_name)
            r_payments = ast.literal_eval(record['payments'])
            if self.r_payments_tmp:
                r_payments = self.r_payments_tmp
        except:
            r_payments = {}
            for participant in ast.literal_eval(self.part_list):
                r_payments[participant] = 0

        app = App.get_running_app()
        screen_manager = app.root.ids['screen_manager']
        screen = screen_manager.get_screen('payers_list')
        PayersWindow.amount = self.amount.text
        PayersWindow.show_pay_list(screen, r_payments)

        AddReceiptWindow.r_name = self.rec_name.text
        AddReceiptWindow.r_amount = self.amount.text
        AddReceiptWindow.r_date = self.date.text
        AddReceiptWindow.r_category = self.category.text
        AddReceiptWindow.r_remarks = self.remarks.text

    def cancelBtn(self):
        self.reset()
        app = App.get_running_app()
        screen_manager = app.root.ids['screen_manager']
        screen_manager.current = self.prev_screen

    def addRecBtn(self):
        # print('edit button :' + str(AddReceiptWindow.editPressed))
        if AddReceiptWindow.editPressed:
            self.dbUpdateRec()
            self.reset()
        else:
            self.dbAddRec()
            self.reset()

    def dbAddRec(self):
        if not self.r_exp_split:  # self.r_exp_split => string
            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            self.r_exp_split = str(array.tolist())

        if self.amount.text != "" and self.rec_name.text != "":
            result = db.add_record(settlement=self.sett_name.text, participants=self.part_list,
                                   receipt=self.rec_name.text,
                                   amount=self.amount.text, date=self.date.text, category=self.category.text,
                                   remarks=self.remarks.text,
                                   payments=str(self.r_payments), exp_split_matrix=self.r_exp_split)
            # self.reset()
            if result == -1:
                invalidReceipt()
            else:
                app = App.get_running_app()
                screen_manager = app.root.ids['screen_manager']
                screen_manager.current = self.prev_screen
        else:
            invalidForm()

    def dbUpdateRec(self):
        if self.amount.text != "" and self.rec_name.text != "":
            db.update_record(old_settlement=self.s_name_old, old_receipt=self.r_name_old,
                             new_settlement=self.sett_name.text,
                             new_receipt=self.rec_name.text, participants=self.part_list, amount=self.amount.text,
                             date=self.date.text, category=self.category.text, remarks=self.remarks.text,
                             payments=str(self.r_payments), exp_split_matrix=self.r_exp_split)
            # self.reset()
            app = App.get_running_app()
            screen_manager = app.root.ids['screen_manager']
            screen_manager.current = self.prev_screen
        else:
            invalidForm()

    def reset(self):  # nie rozumiem dlaczego nie działa dobrze z 'self' zamiast 'AddReceiptWindow'
        AddReceiptWindow.r_name = ""
        AddReceiptWindow.r_amount = ""
        AddReceiptWindow.r_date = ""
        AddReceiptWindow.r_category = ""
        AddReceiptWindow.r_remarks = ""
        AddReceiptWindow.r_payments_tmp = ""
        AddReceiptWindow.editPressed = 0


class PayersWindow(Screen):
    pay_list = ObjectProperty(None)
    amount = ""

    def __init__(self, **kwargs):
        super(PayersWindow, self).__init__(**kwargs)
        # self.pay_list.bind(minimum_height=self.pay_list.setter('height'))

    def show_pay_list(self, payments):
        self.p_list = payers_list(payments=payments)
        self.pay_list.add_widget(self.p_list)

    def OKBtn(self):
        if float(self.amount) == sum(self.p_list.result_dict.values()):
            AddReceiptWindow.r_payments = self.p_list.result_dict
            AddReceiptWindow.r_payments_tmp = self.p_list.result_dict
            app = App.get_running_app()
            screen_manager = app.root.ids['screen_manager']
            screen_manager.current = 'add_receipt'
            self.pay_list.clear_widgets()

        elif float(self.amount) > sum(self.p_list.result_dict.values()):
            missing_amount = round(float(self.amount) - sum(self.p_list.result_dict.values()), 2)
            message = 'Invalid total amount, please correct.\n\nMissing payment of: ' + str(missing_amount) + ' PLN'

            pop = Popup(title='Invalid Amount',
                        content=Label(text=message, halign='center'),
                        size_hint=(0.8, 0.4))
            pop.open()
        else:
            surplus_amount = abs(round(float(self.amount) - sum(self.p_list.result_dict.values()), 2))
            message = 'Invalid total amount, please correct.\n\n ' \
                      'Sum of amounts paid by all people is higher than total receipt amount by:\n\n ' + str(
                surplus_amount) + ' PLN'

            label = Label(text=message, halign='center', text_size=(self.width, None))
            label.texture_update()
            label.texture_size = label.size
            pop = Popup(title='Invalid Amount', content=label, size_hint=(0.8, 0.4))
            pop.open()


class ExpSplitWindow(Screen):
    s_name = ""
    r_name = ""
    r_amount = ""
    r_date = ""
    r_category = ""
    r_remarks = ""
    # grid = ObjectProperty(None)
    # grid = GridLayout(cols=1)
    grid = FloatLayout()
    input_exp_matrix = ""  # string

    def __init__(self, **kwargs):
        super(ExpSplitWindow, self).__init__(**kwargs)
        # self.grid.bind(minimum_height=self.grid.setter('height'))

    def show_exp_split(self, rows, cols, labels):
        self.expenses_grid = check_box_matrix(rows_no=rows, cols_no=cols, labels=labels,
                                              exp_split_matrix=self.input_exp_matrix)
        self.grid.add_widget(self.expenses_grid)

    def OKBtn(self):
        array_converted = str(self.expenses_grid.result_matrix.tolist())
        db.update_record(self.s_name, self.r_name, self.s_name, self.r_name,
                         exp_split_matrix=array_converted)  # sprawdzić czy działa
        AddReceiptWindow.r_exp_split = array_converted
        AddReceiptWindow.s_name = self.s_name
        AddReceiptWindow.r_name = self.r_name
        AddReceiptWindow.r_amount = self.r_amount
        AddReceiptWindow.r_date = self.r_date
        AddReceiptWindow.r_category = self.r_category
        AddReceiptWindow.r_remarks = self.r_remarks
        AddReceiptWindow.editPressed = 1
        self.grid.clear_widgets()

    def CancelBtn(self):
        AddReceiptWindow.s_name = self.s_name
        AddReceiptWindow.r_name = self.r_name
        AddReceiptWindow.r_amount = self.r_amount
        AddReceiptWindow.r_date = self.r_date
        AddReceiptWindow.r_category = self.r_category
        AddReceiptWindow.r_remarks = self.r_remarks
        self.grid.clear_widgets()


def invalidForm():
    pop = Popup(title='Invalid Form',
                content=Label(text='Please fill in all inputs with valid information.'),
                size_hint=(0.8, 0.4))
    pop.open()


def invalidReceipt():
    pop = Popup(title='Invalid Receipt',
                content=Label(text='Receipt already exists. Please correct data.'),
                size_hint=(0.8, 0.4))
    pop.open()


# ********************* Recycle view - settlements
# class MainTable(BoxLayout):
class MainTable(FloatLayout):

    def add_rec(self, data):
        MainWindow.addRecBtn(MainWindow, data)

    def edit_sett(self, data):
        MainWindow.editSettBtn(MainWindow, data)

    def delete_sett(self, data):
        MainWindow.delSettBtn(MainWindow, data)


Builder.load_string('''
<MainTable>:
    #orientation: 'horizontal'
    rv_sett_name: 'col_1_text'                           
    rv_sett_amount: 'col_2_text'
    rv_add_rec: 'col_3_text'
    rv_edit_sett: 'col_4_text'
    rv_del_sett: 'col_5_text'
    cols: 4

    BoxLayout:
        pos_hint: {"x":0, "top":1}
        size_hint: 0.3, 1
        orientation: 'vertical'
        Label:
            id: col_1
            text: root.rv_sett_name

        Label:
            id: col_2
            text: root.rv_sett_amount + ' PLN'
            color: 1,1,1,0.5

    RoundedLeftTopButton:
        id: col_3
        text: 'Add Receipt'
        pos_hint: {"x":0.3, "top":1}
        size_hint: 0.29, 0.98
        on_release:
            root.add_rec(root.rv_add_rec)
            app.root.ids['screen_manager'].current = 'add_receipt'
    RectangleButton:
        id: col_4
        text: 'Edit'
        pos_hint: {"x":0.6, "top":1}
        size_hint: 0.19, 0.98
        on_release:
            root.edit_sett(root.rv_edit_sett)
            app.root.ids['screen_manager'].current = 'add_settl'
    RoundedRightBottomButton:
        id: col_5
        text: 'Delete'
        pos_hint: {"x":0.8, "top":1}
        size_hint: 0.2, 0.98
        on_release:
            root.delete_sett(root.rv_del_sett)
            app.root.ids['screen_manager'].current = 'del_conf_sett'

<RV>:
    viewclass: 'MainTable'
    RecycleBoxLayout:
        default_size: None, dp(50)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
''')


class RV(RecycleView):
    def __init__(self, items, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.items = items
        self.data = [{'rv_sett_name': str(x['col_1']), 'rv_sett_amount': str(x['col_2']),
                      'rv_add_rec': str(x['col_3']), 'rv_edit_sett': str(x['col_4']), 'rv_del_sett': str(x['col_5'])}
                     for x in self.items]


# ********************

# ********************* Recycle view - receipts
class MainTable_rec(BoxLayout):

    def edit_rec(self, data):
        AddSettlementWindow.editRecBtn(AddSettlementWindow, data)

    def delete_rec(self, data):  # dodac nazwę settlement
        AddSettlementWindow.delRecBtn(AddSettlementWindow, data)


Builder.load_string('''
<MainTable_rec>:
    orientation: 'horizontal'
    rv_rec_name: 'col_1_rec_text'                           
    rv_rec_amount: 'col_2_rec_text'
    rv_add_rec: 'col_3_rec_text'
    rv_edit_rec: 'col_4_rec_text'
    rv_del_rec: 'col_5_rec_text'
    spacing: 3
    padding: 1

    Label:
        id: col_1_rec
        text: root.rv_rec_name
    Label:
        id: col_2_rec
        text: root.rv_rec_amount + ' PLN'
    RoundedLeftTopButton:
        id: col_4_rec
        text: 'Edit'
        on_release:
            root.edit_rec(root.rv_edit_rec)
            app.root.ids['screen_manager'].current = "add_receipt"
    RoundedRightBottomButton:
        id: col_5_rec
        text: 'Delete'
        on_release:
            root.delete_rec(root.rv_del_rec)
            app.root.ids['screen_manager'].current = "del_conf_rec"

<RV_rec>:
    viewclass: 'MainTable_rec'
    RecycleBoxLayout:
        default_size: None, dp(40)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
''')


class RV_rec(RecycleView):
    def __init__(self, items, **kwargs):
        super(RV_rec, self).__init__(**kwargs)
        self.items = items
        self.data = [{'rv_rec_name': str(x['col_1_rec']), 'rv_rec_amount': str(x['col_2_rec']),
                      'rv_add_rec': str(x['col_3_rec']), 'rv_edit_rec': str(x['col_4_rec']),
                      'rv_del_rec': str(x['col_5_rec'])}
                     for x in self.items]


# ********************

class MainTable_rep(BoxLayout):

    def pdfBtn(self, data):
        ReportsWindow.pdfReport(ReportsWindow, data)

    def showBtn(self, data):  # dodac nazwę settlement
        ReportsWindow.show(ReportsWindow, data)


Builder.load_string('''
<MainTable_rep>:
    orientation: 'horizontal'
    rv_s_name_rep: 'col_1_rep_text'                           
    rv_pdf_rep: 'col_2_rep_text'
    rv_show_rep: 'col_3_rep_text'
    spacing: 3
    padding: 1

    Label:
        id: col_1_rep
        text: root.rv_s_name_rep

    RoundedLeftTopButton:
        id: col_2_rep
        text: 'PDF'
        on_release:
            root.pdfBtn(root.rv_pdf_rep)
    RoundedRightBottomButton:
        id: col_3_rep
        text: 'Show'
        on_release:
            root.showBtn(root.rv_show_rep)

<RV_rep>:
    viewclass: 'MainTable_rep'
    RecycleBoxLayout:
        default_size: None, dp(40)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
''')


class RV_rep(RecycleView):
    def __init__(self, items, **kwargs):
        super(RV_rep, self).__init__(**kwargs)
        self.items = items
        self.data = [{'rv_s_name_rep': str(x['col_1_rep']), 'rv_pdf_rep': str(x['col_2_rep']),
                      'rv_show_rep': str(x['col_3_rep'])} for x in self.items]


# ********************


# class WindowManager(ScreenManager):
#     pass

# !!!!!!!!!!!!!
# kv = Builder.load_file("smart_bill.kv")

# sm = WindowManager()
db = DataBase("db.txt")

# screens = [MainWindow(name="main"), PayersWindow(name='payers_list'), ExpSplitWindow(name="expense_split"),
#            ReportsWindow(name='reports'), AddSettlementWindow(name='add_settl'), AddReceiptWindow(name='add_receipt'),
#            DelSettConfWindow(name='del_conf_sett'), DelRecConfWindow(name='del_conf_rec')]
#
# for screen in screens:
#     sm.add_widget(screen)
#
# sm.current = "main"


GUI = Builder.load_file("smart_bill_GUI.kv")


class smart_billApp(App):
    # manager = ObjectProperty()

    def build(self):
        # TO BE UNCOMMENTED BEFORE COMPILATION
        self.bind(on_start=self.post_build_init)

        if platform == 'android':
            from android.storage import primary_external_storage_path
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

            primary_storage = primary_external_storage_path()

            PATH = os.path.join(primary_storage, 'Sm@rt_Bill/reports')
            os.makedirs(PATH, exist_ok=True)

        return GUI

    def on_start(self):
        self.root.ids['main'].on_enter()

    def post_build_init(self, *args):
        win = Window
        Clock.schedule_once(lambda x: win.bind(on_keyboard=self.my_key_handler))

    def my_key_handler(self, window, keycode1, keycode2, text, modifiers):
        if self.root.ids['screen_manager'].current != 'main':
            if keycode1 in [27, 1001]:
                # self.manager.current = 'main'
                self.root.ids['screen_manager'].current = 'main'
                return True
            return False


if __name__ == "__main__":
    smart_billApp().run()
