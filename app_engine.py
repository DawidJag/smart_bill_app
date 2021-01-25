import pandas as pd
import numpy as np
import ast


class Settlement():
    def __init__(self, participants, name):
        self.participants = participants  # list of people
        self.name = name
        self.receipts = []  # adding each receipt  to this list during creation of each receipt

    def add_receipt_to_settlement(self, receipt):
        # for receipt in receipts:
        self.receipts.append(receipt)

    # powinno byc OK
    def get_settle_balance(self):
        settle_balance = {}

        for person in self.participants:
            settle_balance[person] = 0

            for receipt in self.receipts:
                settle_balance[person] += receipt.get_balance_per_person()[person]
        return settle_balance

    # powinno byc OK
    def get_split_of_balance(self):  # splitting balance per person for negative and positive
        negative_bal = {}
        positive_bal = {}

        for key, value in self.get_settle_balance().items():
            if value < 0:
                negative_bal[key] = value
            else:
                positive_bal[key] = value

        positive_bal = pd.Series(positive_bal)
        negative_bal = pd.Series(negative_bal)

        positive_bal.sort_values(ascending=True, inplace=True)
        negative_bal.sort_values(ascending=True, inplace=True)
        final_payers = list(negative_bal.index)
        final_receivers = list(positive_bal.index)

        return positive_bal, negative_bal, final_payers, final_receivers

    # *********************************************************

    # powinno byc OK
    # final settlement between all participants
    def final_payments_report(self):
        payments = {}  # dictionary => {'payer1': {'receiver1': amt1, 'receiver2': amt2}}
        positive, negative, payers, receivers = self.get_split_of_balance()

        for payer in payers:
            payments[payer] = {}
            for receiver in receivers:

                if positive[receiver] <= abs(negative[payer]):
                    payments[payer].update({receiver: round(positive[receiver], 2)})  # payment
                    negative[payer] += round(positive[receiver], 2)  # adding receiver to the dict with payments
                    positive[receiver] -= round(positive[receiver], 2)  # settle of payment on receiver side
                else:
                    payments[payer].update({receiver: abs(round(negative[payer], 2))})

        return payments


# ********************************************************

class Receipt():
    def __init__(self, participants, amount, payments, exp_split_matrix, category, date, remarks=''):
        self.participants = participants
        self.amount = amount
        self.payments = payments  # dodać w aplikacji listę płacących
        self.payers = list(payments.keys())
        self.pay_amt = list(payments.values())
        self.category = category
        self.date = date
        self.remarks = remarks
        self.exp_split_matrix = np.array(ast.literal_eval(exp_split_matrix))
        self.priv_exp_matrix = self.get_priv_exp_matrix()
        self.priv_exp_per_person = self.get_priv_exp_per_person()
        self.tot_common_exp_amt = self.amount - sum(self.priv_exp_per_person.values())
        self.tot_exp_per_person = self.get_tot_exp_per_person()

    def get_priv_exp_matrix(self):
        input_matrix = self.exp_split_matrix.copy()         # @@@@@@@@ tutaj zamienić na pobieranie wszystkiego oprócz pierwszego wiersza
        input_matrix = input_matrix[1:,:]
        A = input_matrix[:, 2:].astype(float)  # type conversion
        B = A.sum(axis=1).reshape((-1, 1))
        C = input_matrix[:, 1].astype(float).reshape((-1, 1))
        D = C * (A / B)  # calculation of private expenses matrix
        # assigning private expenses
        input_matrix[:, 2:] = D
        return input_matrix

    def get_priv_exp_per_person(self):
        priv_exp_per_person = {}
        i = 0
        for person in self.participants:
            priv_exp_per_person[person] = self.priv_exp_matrix[:, 2 + i].astype(float).sum(axis=0)
            # print(self.priv_exp_matrix[:,2+i])
            i += 1
        return priv_exp_per_person

    def get_tot_exp_per_person(self):
        exp_per_person_dict = {}

        for person in self.participants:
            exp_per_person_dict[person] = self.priv_exp_per_person[person] + self.get_common_exp_per_person()
        return exp_per_person_dict

    def get_common_exp_per_person(self):
        no_of_people = len(self.participants)
        common_exp_per_person = self.tot_common_exp_amt / no_of_people
        return common_exp_per_person

    def get_payment_per_person(self):
        return self.payments

    def get_balance_per_person(self):
        balance = {}
        for person in self.participants:
            if person in self.payers:
                balance[person] = self.get_payment_per_person()[person] - self.get_tot_exp_per_person()[person]
            else:
                balance[person] = -self.get_tot_exp_per_person()[person]
        return balance