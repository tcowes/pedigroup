class User:

    def __init__(self, name, username):
        self.name = name
        self.username = username
        self.groups = set()

    def addGroup(self, group):
        self.groups.add(group)