from kivy.app import App
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout


Builder.load_string('''
<Row>:
    canvas.before:
        Color:
            rgba: 0.5, 0.5, 0.5, 1
        Rectangle:
            size: self.size
            pos: self.pos
        
    orientation: 'horizontal'
                             
    rv_user: 'col_4_rec_text'
    spacing: 3
    padding: 1

    TextInput:
        id: col_1_user
        text: root.rv_user

    Button:
        id: col_2_user
        text: 'Save'
        on_release:
            root.saveUser(root.rv_user)
          #  app.root.ids['screen_manager'].current = "add_receipt"
    Button:
        id: col_3_user
        text: 'Delete'
        on_release:
            root.deleteUser(root.rv_user)
          #  app.root.ids['screen_manager'].current = "del_conf_rec"


<RV>:
    id: rv
    viewclass: 'Row'
    scroll_type: ['bars', 'content']
    scroll_wheel_distance: dp(114)
    bar_width: dp(10)
    RecycleGridLayout:
        cols:1
        default_size: None, dp(30) 
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        #orientation: 'vertical'
        spacing: dp(1)

''')
items = [{'col_1_user':'1'}, {'col_1_user':'John'}, {'col_1_user':'K'}, {'col_1_user':'2'}, {'col_1_user':'David'}, {'col_1_user':'P'}]

class RV(RecycleView):

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.items = items
        self.data = [{'rv_user': str(x['col_1_user'])} for x in self.items]



class Row(BoxLayout, RecycleDataViewBehavior):
    index = None

    def __init__(self, **kwargs):
        super(Row, self).__init__(**kwargs)


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
    def saveUser(self, data):
        app = App.get_running_app()
        user_old = items[self.index]['col_1_user']
        user = self.ids['col_1_user'].text

        if user in app.users:
            print('user already exists')
            self.ids['col_1_user'].text = user_old
        elif user == user_old:
            app.users.append(user)
            print(app.users)
        else:
            app.users.append(user)
            print('user old: ' + user_old)
            app.users.remove(user_old)
            items[self.index] = {'col_1_user': user}
            print(items)
            print('user updated')
            print(app.users)


    # tutaj dopisać: usuwanie użytkownika ze wszystkich paragonów, ze wszystkich płatnosci, z exp_split po nazwie kolumny
    def deleteUser(self, data):
        app = App.get_running_app()
        user = self.ids['col_1_user'].text

        if user in app.users:
            app.users.remove(user)
            print(app.users)
        else:
            print('user doesn\'t exist')



# class rvTestApp(App):
#     def __init__(self, **kwargs):
#         super(rvTestApp, self).__init__(**kwargs)
#         self.users = []
#
#     def build(self):
#
#         return RV()
#
# # if __name__ == '__main__':
# rvTestApp().run()