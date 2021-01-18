from fpdf import FPDF
from datetime import date
import os
import os.path
# from android.storage import primary_external_storage_path
import webbrowser




class PDF(FPDF):
    def __init__(self, title, **kwargs):
        super(PDF, self).__init__(**kwargs)
        self.title = title

    def header(self):
        # Logo
        self.image('smart_bill_logo.png', 5, 8, 200)
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # self.set_draw_color(0, 80, 180)
        self.set_fill_color(8, 202, 241)
        # self.set_text_color(220, 50, 50)
        # Move to the right
        # self.cell(80)
        # Line break
        self.ln(20)
        # Title
        self.cell(90, 10, 'Final settlements to be done', 1, 0, 'L', fill=True)

        self.cell(100, 10, 'Settlement: ' + self.title, 1, 2, 'L')
        self.ln(10)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        self.set_fill_color(224, 224, 224)
        # Page number
        self.cell(0, 5, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C', fill=True)

    def table_header(self, payer):
        # Arial 12
        self.set_font('Arial', '', 12)
        # Background color
        self.set_fill_color(108, 231, 255)
        # self.set_text_color(255, 255, 255)
        # Title
        self.cell(40, 8, 'Receivers:', 1, 0, 'L', 1)
        self.cell(50, 8, 'Payer : %s' % payer, 1, 1, 'L', 1)
        # Line break
        # self.ln(4)

    def table_body(self, transfers):
        self.set_fill_color(224, 224, 224)
        # self.set_text_color(0, 0, 0)

        for receiver, amount in transfers.items():
            self.cell(40, 6, receiver, 1, 0, fill=True)
            self.cell(50, 6, str(amount), 1, 1, 'R')
        # Line break
        self.ln(10)

def save_report(settlement_name, payments):
    # Instantiation of inherited class
    pdf = PDF(title=settlement_name)
    pdf.set_title(settlement_name)
    pdf.alias_nb_pages()

    pdf.add_page()
    pdf.set_font('Times', '', 12)

    for payer in payments.keys():
        pdf.table_header(payer)
        pdf.table_body(payments[payer])

    # saving report
    today = str(date.today())
    file_name = 'report_' + settlement_name + '_' + today + '.pdf'

    # TO BE UNCOMMENTED BEFORE COMPILATION
    # primary_storage = primary_external_storage_path()
    # PATH = os.path.join(primary_storage, 'Sm@rt_Bill/reports')
    PATH = './reports'

    file = os.path.join(PATH, file_name)

    pdf.output(file, 'F')

    webbrowser.open(file)

    # opening the pdf file with report
    # subprocess.Popen([file], shell=True)




