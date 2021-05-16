class Person:

    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.amount_contributed = 0
        self.amount_owed = 0

    def get_details(self):
        return self.name + " email: " + self.email + " amount due: " + self.amount_contributed
