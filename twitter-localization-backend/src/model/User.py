class User:

    @staticmethod
    def parseFromGraphNode(node):
        """
        Creates a User object froma Neo4j graph node
        :param node: Neo4j graph node
        :return: created User object
        """
        user = User()
        user.node_id = node.id
        for key in node.keys():
            user.properties[key] = node[key]
        return user

    def __init__(self):
        self.node_id = -1
        self.properties = {}

    def __str__(self):
        string_rep = "User("
        key_val_pair_strings = [str(key) + "=" + str(val) for key, val in self.properties.items()]
        string_rep += ", ".join(key_val_pair_strings)
        string_rep += ")"
        return string_rep

    def __repr__(self):
        return str(self)





