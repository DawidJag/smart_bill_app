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


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, CardTransition
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.window import Window
# Window.size = (1080, 2340)

from kivy.uix.scrollview import ScrollView



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
            labels = ['Items', 'Amounts'] + participants.split(',')
            cols = len(labels)
            labels = np.array(labels).reshape((1,-1))

            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols-2))
            array = np.concatenate((items, zeros, checks), axis=1)
            array2 = np.concatenate((labels, array), axis=0)
            array_converted = str(array2.tolist())
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
        webbrowser.open('https://youtu.be/KUo5YfdCatw')



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

class ParticipantsWindow(Screen):
    part_list_window = BoxLayout()
    s_name = ""
    participants_names = ""

    def __init__(self, **kwargs):
        super(ParticipantsWindow, self).__init__(**kwargs)

    def on_enter(self):
        self.part_list_window.clear_widgets()
        self.show_RV_participants()

    def show_RV_participants(self):  # items
        # print('s_name: ' + self.s_name)

        if self.s_name in db.get_settlements_list():
            # self.participants_names = "'participant1', 'participant2'"
            self.participants_names = db.get_settlement_participants(self.s_name)
            print('participants: ' + self.participants_names)
        else:
            self.participants_names = "'#name1', '#name2'"

        self.participants_list = self.participants_names.split(',')

        # input list to create recycle view with settlements
        self.items = []
        for name in self.participants_names.split(','):
            temp_dict = {'col_1_user': name}
            self.items.append(temp_dict)

        # self.sett_list.bind(minimum_height=self.sett_list.setter('height'))
        self.recycle_view = RV_participants(items=self.items, settlement=self.s_name)

        self.part_list_window.add_widget(self.recycle_view)


    def addToListBtn(self):
        participants = db.get_settlement_participants(self.s_name).split(',')
        no_of_part = len(participants)

        new_user = "#name" + str(no_of_part + 1)

        i = no_of_part + 1
        while new_user in participants:
            i += 1
            new_user = "_name" + str(i)

        participants.append(new_user)
        db.update_participants(self.s_name, str(participants))
        receipts = db.get_receipts_list(self.s_name)

        for receipt in receipts:
            # payments
            payments = ast.literal_eval(db.get_record_data(self.s_name, receipt)['payments'])
            payments[new_user] = 0

            # expense split
            exp_split = np.array(ast.literal_eval(db.get_record_data(self.s_name, receipt)['exp_split_matrix']))
            new_user_col = np.zeros((exp_split.shape[0],1), dtype=object)
            new_user_col[0] = new_user
            exp_split = np.append(exp_split, new_user_col, axis=1)
            exp_split = exp_split.tolist()

            db.update_record(self.s_name, receipt, self.s_name, receipt, payments=str(payments),
                             exp_split_matrix=str(exp_split))

        self.part_list_window.clear_widgets()
        self.show_RV_participants()

    def cancelBtn(self):
        AddSettlementWindow.s_name = self.s_name
        AddSettlementWindow.part_list = db.get_settlement_participants(self.s_name)



class DelUserConfWindow(Screen):
    sett_name = ObjectProperty(None)
    participant_name = ObjectProperty(None)
    participants_list = []
    s_name = ""
    user_name = ""

    def on_enter(self):
        # self.sett_name.text = self.s_name
        self.participant_name.text = self.user_name


    def delUser(self):
        self.new_participant_list = self.participants_list.copy()

        if self.user_name in self.participants_list:
            # updating participants in database
            self.new_participant_list.remove(self.user_name)
            db.update_participants(self.s_name, str(self.new_participant_list))

            # updating payments and expense split in database
            receipts = db.get_receipts_list(self.s_name)
            for receipt in receipts:
                # payments
                payments = ast.literal_eval(db.get_record_data(self.s_name, receipt)['payments'])
                payments.pop(self.user_name, 'not found')

                # expense split
                exp_split = np.array(ast.literal_eval(db.get_record_data(self.s_name, receipt)['exp_split_matrix']))
                exp_split = np.delete(exp_split, np.where(exp_split[0,:] == self.user_name), axis=1)
                exp_split = str(exp_split.tolist())

                db.update_record(self.s_name, receipt, self.s_name, receipt, payments=str(payments),
                                 exp_split_matrix=str(exp_split))

            app = App.get_running_app()
            screen_manager = app.root.ids['screen_manager']
            screen_manager.current = 'participants'
            AddSettlementWindow.part_list = db.get_settlement_participants(self.s_name)
        else:
            print('user doesn\'t exist')



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
        layout_popup.add_widget(Label(text=str(payer) + ' should make below transfers to:'))

        for receiver, amount in transfers.items():
            inside_box = GridLayout(cols=2, spacing=10)  # linia płatności
            label_rec = Label(text=receiver + ': ')
            label_amt = Label(text=str(f'{amount:.2f}'))
            inside_box.add_widget(label_rec)
            inside_box.add_widget(label_amt)

            layout_popup.add_widget(inside_box)

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
        # self.particip_list.text = self.part_list  # string
        self.particip_list.text = self.part_list.replace(',', ', ')
        self.rec_list.clear_widgets()
        self.show_rec_RV()
        self.s_name_old = self.s_name
        self.part_list_old = self.part_list
        # print(self.s_name)

    # ******************** Receipts list
    def show_rec_RV(self):  # items
        if self.s_name:
            # receipts = list(filter(None, db.get_receipts_list(self.s_name)))
            receipts = db.get_receipts_list(self.s_name).copy()
            if 'default_name' in receipts:
                receipts.remove('default_name')
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
        AddSettlementWindow.part_list = db.get_settlement_participants(self.s_name_old)                    #self.particip_list.text
        if receipts_list:
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
            labels = ['Items', 'Amounts'] + self.particip_list.text.split(',')
            labels = np.array(labels).reshape((1, -1))

            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            array2 = np.concatenate((labels, array), axis=0)
            array_converted = str(array2.tolist())
            AddReceiptWindow.r_exp_split = array_converted

        AddReceiptWindow.prev_screen = "add_settl"



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

    def addPartBtn(self):
        if self.settl_name.text in db.get_settlements_list():
            self.s_name_old = self.settl_name.text
            self.updateSett()
            # self.s_name_old = self.settl_name.text
        else:
            db.add_record(self.settl_name.text, str(['#name1', '#name2']),
                          payments=str({'#name1': 0, '#name2': 0}))
        ParticipantsWindow.s_name = self.settl_name.text



    def on_focus(self, instance):
        if instance.focus:
            Clock.schedule_once(lambda dt: instance.select_all())
        else:
            # if jesli nie istnieje rozliczenie
            if self.settl_name.text in db.get_settlements_list():
                self.updateSett()
                self.s_name_old = self.settl_name.text
            else:
                labels = ['Items', 'Amounts', '#name1', '#name2']
                labels = np.array(labels).reshape((1, -1))
                items = ['item ' + str(x) for x in range(1, 11)]  # fixed no. of rows => 10
                items = np.array(items).reshape((-1, 1))
                zeros = np.zeros((10, 1))
                checks = np.ones((10, 2))
                tmp_default_array = np.concatenate((items, zeros, checks), axis=1)
                exp_split_matrix = np.concatenate((labels, tmp_default_array), axis=0)
                exp_split_matrix = exp_split_matrix.tolist()

                db.add_record(self.settl_name.text, str(['#name1', '#name2']), receipt='default_name', amount=0,
                              payments=str({'#name1': 0, '#name2': 0}), exp_split_matrix=str(exp_split_matrix))


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
        # print(self.r_exp_split)

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
        cols = len(self.part_list.split(','))

        app = App.get_running_app()
        screen_manager = app.root.ids['screen_manager']
        screen = screen_manager.get_screen(screen_name)

        ExpSplitWindow.input_exp_matrix = self.r_exp_split
        ExpSplitWindow.show_exp_split(screen, rows, cols)

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

        r_payments = {k: r_payments[k] for k in sorted(r_payments, key=lambda x: (x[0] is '#', x))}

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
            labels = ['Item', 'Amounts'] + ast.literal_eval(self.part_list)
            labels = np.array(labels)
            cols = len(labels)
            rows = 10

            items = ['item ' + str(x) for x in range(1, rows + 1)]
            items = np.array(items).reshape((-1, 1))
            zeros = np.zeros((rows, 1))
            checks = np.ones((rows, cols))
            array = np.concatenate((items, zeros, checks), axis=1)
            array2 = np.concatenate((labels, array), axis=0)
            self.r_exp_split = str(array2.tolist())

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

    def reset(self):
        AddReceiptWindow.r_name = ""
        AddReceiptWindow.r_amount = ""
        AddReceiptWindow.r_date = ""
        AddReceiptWindow.r_category = ""
        AddReceiptWindow.r_remarks = ""
        AddReceiptWindow.r_payments_tmp = ""
        AddReceiptWindow.editPressed = 0

    def on_focus(self, instance):
        if instance.focus:
            Clock.schedule_once(lambda dt: instance.select_all())


class PayersWindow(Screen):
    # pay_list = ObjectProperty(None)
    pay_list = BoxLayout()
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
            message = 'Invalid total amount, please correct.\n\nMissing payment of:\n\n ' + str(missing_amount) + ' PLN'

            pop_content = PopContent(message=message)
            pop = Popup(title='Invalid Amount', content=pop_content, size_hint=(0.8, 0.5))
            pop.open()
        else:
            surplus_amount = abs(round(float(self.amount) - sum(self.p_list.result_dict.values()), 2))
            message = 'Invalid total amount, please correct.\n\n ' \
                      'Sum of amounts paid by all people is higher than total receipt amount by:\n\n ' \
                      + str(surplus_amount) + ' PLN'

            pop_content = PopContent(message=message)
            pop = Popup(title='Invalid Amount', content=pop_content, size_hint=(0.8, 0.5))
            pop.open()


class ExpSplitWindow(Screen):
    s_name = ""
    r_name = ""
    r_amount = ""
    r_date = ""
    r_category = ""
    r_remarks = ""
    grid = FloatLayout()
    input_exp_matrix = ""  # string

    def __init__(self, **kwargs):
        super(ExpSplitWindow, self).__init__(**kwargs)
        # self.grid.bind(minimum_height=self.grid.setter('height'))

    # def show_exp_split(self, rows, cols, labels):
    def show_exp_split(self, rows, cols):
        # self.expenses_grid = check_box_matrix(rows_no=rows, cols_no=cols, labels=labels,
        #                                       exp_split_matrix=self.input_exp_matrix)
        self.expenses_grid = check_box_matrix(rows_no=rows, cols_no=cols, exp_split_matrix=self.input_exp_matrix)
        self.grid.add_widget(self.expenses_grid)

    def OKBtn(self):
        array_converted = str(self.expenses_grid.result_matrix.tolist())
        db.update_record(self.s_name, self.r_name, self.s_name, self.r_name,
                         exp_split_matrix=array_converted)
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

class PopContent(BoxLayout):
    input_label = ObjectProperty()

    def __init__(self, message, **kwargs):
        super(PopContent, self).__init__(**kwargs)
        self.input_label.text = message


def invalidForm():
    pop_content = PopContent(message='Please fill in all inputs with valid information.')
    pop = Popup(title='Invalid Form', content=pop_content, size_hint=(0.8, 0.4))
    pop.open()


def invalidReceipt():
    pop_content = PopContent(message='Receipt already exists. Please correct data.')
    pop = Popup(title='Invalid Receipt', content=pop_content, size_hint=(0.8, 0.4))
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

# ********************* Recycle view - participants
class Row(BoxLayout, RecycleDataViewBehavior):          # based on: https://stackoverflow.com/questions/47630155/kivy-editable-recycleview
    index = None
    settlement = ""
    users = []


    def __init__(self, **kwargs):
        super(Row, self).__init__(**kwargs)
        app = App.get_running_app()
        self.settlement = app.root.ids['participants'].s_name
        self.users = db.get_settlement_participants(self.settlement).split(',')


    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(Row, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if super(Row, self).on_touch_down(touch):
            return True

        if self.collide_point(*touch.pos):
            global rowIndex
            rowIndex = self.index

    # ta funkcja działa dla już istniejącego użytkownika, czyli powinna zamienić we wszystkich tabelach starą nazwę na nową bez zmiany innych danych
    def saveUser(self, data, items):        # zmienić nazwę na UPDATE !!!!!!!!!!!!!!
        self.items = items
        user_old = items[self.index]['col_1_user']
        user = self.ids['col_1_user'].text
        self.users = db.get_settlement_participants(self.settlement).split(',')

        if user in self.users:
            print('user already exists')
            self.ids['col_1_user'].text = user_old
        elif user == user_old:
            # self.users.append(user)
            # print(self.users)
            print('przypadek do wywalenia')
        else:
            self.users.append(user)
            # print('user old: ' + user_old)
            self.users.remove(user_old)
            items[self.index] = {'col_1_user': user}
            # print(items)
            # print('user updated')
            # print('self.users: ')
            # print(self.users)

        db.update_participants(self.settlement, str(self.users))

        # updating payments in database
        receipts = db.get_receipts_list(self.settlement)
        for receipt in receipts:
            # payments
            payments = ast.literal_eval(db.get_record_data(self.settlement, receipt)['payments'])
            payments[user] = payments.pop(user_old, 'old user not in dict')

            # expense split
            exp_split = ast.literal_eval(db.get_record_data(self.settlement, receipt)['exp_split_matrix'])
            exp_split[0] = [user if user_old == participant else participant for participant in exp_split[0]]

            db.update_record(self.settlement, receipt, self.settlement, receipt, payments=str(payments), exp_split_matrix=str(exp_split))

        AddSettlementWindow.part_list = db.get_settlement_participants(self.settlement)

    def on_focus(self, instance):
        app = App.get_running_app()
        if instance.focus:
            Clock.schedule_once(lambda dt: instance.select_all())
        else:
            self.saveUser(app.root.ids['participants'].recycle_view.data, app.root.ids['participants'].recycle_view.items)

    def delBtn(self, data):
        app = App.get_running_app()
        app.root.ids['del_conf_user'].user_name = self.ids['col_1_user'].text
        app.root.ids['del_conf_user'].s_name = self.settlement
        app.root.ids['del_conf_user'].participants_list = self.users


class RV_participants(RecycleView):

    def __init__(self, items, settlement, **kwargs):
        super(RV_participants, self).__init__(**kwargs)
        self.items = items
        self.settlement = settlement

        self.data = [{'rv_user': str(x['col_1_user'])} for x in self.items]


Builder.load_string('''
<Row>:
    id: row
    #canvas.before:
     #   Color:
      #      rgba: 0.5, 0.5, 0.5, 1
       # Rectangle:
        #    size: self.size
         #   pos: self.pos

    orientation: 'horizontal'

    rv_user: 'col_1_user_text'
    spacing: 3
    padding: 1

    TextInput:
        id: col_1_user
        text: root.rv_user
        on_focus: root.on_focus(self)

    #RectangleButton:
     #   id: col_2_user
      #  text: 'Update'
       # on_release:
        #    root.saveUser(root.rv_user, root.parent.parent.items)
    RoundedRightBottomButton:
        id: col_3_user
        text: 'Delete'
        on_release:
            root.delBtn(root.rv_user)
            app.root.ids['screen_manager'].current = "del_conf_user"



<RV_participants>:
    id: rv
    viewclass: 'Row'
    scroll_type: ['bars', 'content']
    scroll_wheel_distance: dp(114)
    bar_width: dp(10)
    RecycleGridLayout:
        id: rv_grid
        cols:1
        default_size: None, dp(30) 
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        #orientation: 'vertical'
        spacing: dp(1)

''')
# **************************************************

db = DataBase("db.txt")

GUI = Builder.load_file("smart_bill_GUI.kv")


class smart_billApp(App):

    def build(self):
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
