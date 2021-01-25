# ****************************** Data Base ******************
# created based on:   https://www.techwithtim.net/tutorials/kivy-tutorial/example-gui/
import re

class DataBase:
    def __init__(self, file_name):
        self.filename = file_name
        self.settlements = None
        self.file = None
        self.load()

    def load(self):
        self.file = open(self.filename, "r")
        self.settlements = {}

        for line in self.file:
            settlement, receipt, participants, amount, payments, exp_split_matrix, category, date, remarks = line.strip().split(";")

            if settlement in self.settlements.keys():
                self.settlements[settlement].update(
                    {receipt: [participants, amount, payments, exp_split_matrix, category, date, remarks]})
            else:
                self.settlements[settlement] = {receipt: [participants, amount, payments, exp_split_matrix, category, date, remarks]}
        self.file.close()

    def add_record(self, settlement, participants, receipt='', amount='', payments='', exp_split_matrix='', category='', date='', remarks=''):
        if settlement.strip() in self.settlements.keys():
            # checking if specific receipt already exists for that settlement, if not add receipt to the settlement
            if receipt.strip() not in self.settlements[settlement.strip()]:
                self.settlements[settlement.strip()].update(
                    {receipt.strip(): [participants, amount, payments, exp_split_matrix, category, date, remarks]})
                self.save()
                return 1
            else:
                print("Receipt exists already")
                return -1
        else:
            self.settlements[settlement.strip()] = {
                receipt.strip(): [participants, amount, payments, exp_split_matrix, category, date, remarks]}
            self.save()
            return 1

    def save(self):
        with open(self.filename, "w") as f:
            for settlement in self.settlements:
                for receipt in self.settlements[settlement]:
                    item = self.settlements[settlement][receipt]

                    f.write(settlement + ";" + receipt + ";" + item[0] + ";" + item[1] + ";" + item[2] + ";" + item[
                        3] + ";" + item[4] + ";" + item[5] + ";" + item[6] + "\n")

    def update_record(self, old_settlement, old_receipt, new_settlement, new_receipt, participants="", amount="",
                       payments="", exp_split_matrix="", category="", date="", remarks=""):
        # added possibility of passing through only settlement, receipt and just one another feature
        tmp_record = {'settlement': new_settlement, 'receipt': new_receipt, 'participants': participants,'amount': amount,
                      'payments': payments, 'exp_split_matrix': exp_split_matrix, 'category': category, 'date': date, 'remarks': remarks}
        old_record = self.get_record_data(old_settlement, old_receipt)
        self.delete_record(old_settlement, old_receipt)

        new_record = {}
        for feature in old_record.keys():
            if tmp_record[feature] == "":
                new_record[feature] = old_record[feature]
            else:
                new_record[feature] = tmp_record[feature]

        self.add_record(new_record['settlement'], new_record['participants'], new_record['receipt'], new_record['amount'],
                        new_record['payments'], new_record['exp_split_matrix'], new_record['category'], new_record['date'],
                        new_record['remarks'])
        return 1

    def update_participants(self, settlement, new_participants):
        receipts = self.get_receipts_list(settlement)

        for receipt in receipts:
            self.update_record(old_settlement=settlement, old_receipt=receipt, new_settlement=settlement,
                               new_receipt=receipt, participants=new_participants)
        return 1

    def delete_record(self, settlement, receipt):
        self.settlements[settlement].pop(receipt)
        self.save()
        return 1

    def delete_settlement(self, settlement):
        self.settlements.pop(settlement, None)
        self.save()
        return 1

    def get_settlements_list(self):
        settlements = list(self.settlements.keys())
        settlements = sorted(settlements, key=str.lower)
        # return self.settlements.keys() *
        return settlements

    def get_settlement_amount(self, settlement):
        sett = self.settlements[settlement]

        amount = 0
        for key, value in sett.items():
            if not value[1] == "":
                amount += float(value[1])
        return amount

    def get_receipt_amount(self, settlement, receipt):
        sett = self.settlements[settlement]
        receipt_data = sett[receipt]
        rec_amount = receipt_data[1]
        return rec_amount

    def get_receipts_list(self, settlement):            # for specific settlement
        receipts_list = list(self.settlements[settlement].keys())
        return receipts_list

    def get_settlement_participants(self, settlement):
        sett = self.settlements[settlement]
        receipts = self.get_receipts_list(settlement)
        first_receipt = receipts[0]

        participants = sett[first_receipt][0]
        # participants = re.sub("[\[\]\']", '', participants)
        participants = re.sub(r"([^a-zA-Z0-9^,])", '', participants)
        return participants                                         # string

    def get_record_data(self, settlement, receipt):
        sett = self.settlements[settlement]
        record = sett[receipt]
        items = ['participants', 'amount', 'payments', 'exp_split_matrix', 'category', 'date', 'remarks']

        record_data = {'settlement': settlement, 'receipt': receipt}
        i=0
        for item in items:
            record_data[item] = record[i]
            i +=1
        return record_data

    def get_exp_split_matrix(self, settlement, receipt):
        record = self.get_record_data(settlement, receipt)
        exp_matrix = record['exp_split_matrix']
        return exp_matrix
