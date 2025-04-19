# jlim@wpi.edu
# Basic scenario generation for the family tree scenario.
# Inspired by logicAsker and Prolog.

# Inspiration: https://stackoverflow.com/questions/2823316/generate-a-random-letter-in-python
import string
import random
import copy

# Scenario generation: Create a tree, randomly add nodes.

# Question generation: Sub-functions for creating templates. No easy way around; just need to

# Easy question generation: Only the stated relationships.

# Hard question generation: Each relationship has a check function...


# Knowledge base needs to:
# remember atoms
#


# class KnowledgeBase:
#     def __init__(self):
#         pass

    # keeps track of atoms

    # keeps track of predicates

    # Given atoms, and a list of possible rules, a simple generator for new rules?

# Using prolog terminology.
def add_kb_atom(kb_list, atom):
    if atom not in kb_list:
        kb_list.append(atom)

# Try all possibilities
# We need some sort of bfs/dfs modified by a regex...

# Parent/child check: Make sure we're at the same level.
def check_relationship_path(proposed_predicate, kb_list, node_regex):
    # True means good, false means bad.

    # kind a bfs search.
    # atom is the root.

    # Empty for now.
    reached_set = {

    }

    frontier_set = {
        proposed_predicate[0]: 0
    }

    new_frontier_set = {


    }

    # parse predicates to see if there's a path!
    offset_level = 0
    if type(proposed_predicate) in [Mother, Father, Parent]:
        offset_level = -1
    elif type(proposed_predicate) in [Sibling, Sister, Brother]:
        offset_level = 0
    elif type(proposed_predicate) in [Child]:
        offset_level = 1

    for item in kb_list:
        if type(item) != str:
            if item[0] in reached_set or item[1] in reached_set or item[0] in frontier_set or item[1] in frontier_set:
                if item[0] == item[1]:
                    continue
                else:
                    if type(item) in [Mother, Father, Parent]:
                        pass
            elif item[1] in reached_set or item[1] in frontier_set: # Reverse relationship.
                pass

    while len(frontier_set) != 0:
        pass

    return True

class Predicate:
    def __init__(self, arglist):
        self.arglist = arglist

    def __getitem__(self, i):
        return self.arglist[i]

    # Print the natural language form of this predicate.
    def get_nl_string(self):
        pass

    def is_equal(self, otherPredicate):
        # A predicate is equal if it has the same predicate list, and is the same class.
        return (type(self) == type(otherPredicate)) and (self.arglist == otherPredicate.arglist)

    def check_if_consistent(self, knowledge_base_list):
        # Check the knowledge base, add if it's consistent with existing facts, and is not a duplicate.
        # Focus on contradictions.
        # subclasses should extend!
        if len(knowledge_base_list) == 0:
            return True

        # Check atoms
        atom_set = copy.deepcopy(self.arglist)

        # Check for exact matches.
        for x in knowledge_base_list:
            if isinstance(x, str):
                if x in atom_set:
                    atom_set.remove(x)

            if self.is_equal(x):
                return False

        if len(atom_set) != 0:
            return False # All atoms must exist!

        return True

    # For sampling rules to try: randomly take existing atoms,
    def can_prove(self, knowledge_base_list):
        # Check if we can deduce this from the knowledge base.
        # Focus on implications.

        # First: Check exact matches
        if len(knowledge_base_list) == 0:
            return False

        for x in knowledge_base_list:
            if self.is_equal(x):
                return True

    # TODO: May need helper function for a sort of path detection algorithm.

# Simplified family predicates.

# Unary
class Male(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is male."

    def check_if_consistent(self, knowledge_base_list):
        if super().check_if_consistent(knowledge_base_list):
            # Check rules
            for x in knowledge_base_list:
                # Can't be primary subject for some gendered predicate.
                if x[0] == self[0]:
                    if(type(x) in [Mother, Sister]):
                        return False

            return True

class Female(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is female."

    def check_if_consistent(self, knowledge_base_list):
        if super().check_if_consistent(knowledge_base_list):
            # Check rules
            for x in knowledge_base_list:
                # Can't be primary subject for some gendered predicate.
                if x[0] == self[0]:
                    if (type(x) in [Father, Brother]):
                        return False

            return True

# Binary
class Parent(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is a parent of " + self.arglist[1]

    def check_if_consistent(self, knowledge_base_list):
        if super().check_if_consistent(knowledge_base_list):

            # Cannot parent thyself.
            if self[0] == self[1]:
                return False

            # Max 2 parents for one child
            child_map = {}
            for x in knowledge_base_list:

                if (type(x) in [Mother, Father, Parent]):
                    if x[1] not in child_map:
                        child_map[x[1]] = 1
                    else:
                        child_map[x[1]] += 1


            if self[1] in child_map:
                if child_map[self[1]] >= 2:
                    return False

            # Check opposite relationships ... difficult!


            return True

class Mother(Parent):
    def get_nl_string(self):
        return self.arglist[0] + " is the mother of " + self.arglist[1]

class Father(Parent):
    def get_nl_string(self):
        return self.arglist[0] + " is the father of " + self.arglist[1]

class Child(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is a child of " + self.arglist[1]

    def check_if_consistent(self, knowledge_base_list):
        # Cannot be a weird reverse relationship (already parent of the candidate child, etc)
        pass

class Sibling(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is a sibling of " + self.arglist[1]

class Sister(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is a sister of " + self.arglist[1]

class Brother(Predicate):
    def get_nl_string(self):
        return self.arglist[0] + " is a brother of " + self.arglist[1]


def namelike_strs(gen_count, name_len=6):
    # choose name_len random chars.
    names = []
    choice_set = string.ascii_lowercase
    # choice_set = string.ascii_letters
    for a in range(gen_count):
        chars_list = random.choices(choice_set, k=name_len)
        name = ''
        for c in chars_list:
            name = name + c
        names.append(name)

    return names


def parse_names(name_path):
    with open(name_path, 'r') as f:
        file_lines = f.readlines()

    # 150 boy, 150 girl names.
    num_names = 150
    male_names = []
    female_names = []
    for idx, line in enumerate(file_lines):
        tokens = line.split(" ")
        if idx < num_names:
            male_names.append(tokens[1])
        else:
            female_names.append(tokens[1])

    return male_names, female_names

def basic_test_scenario():
    kb_list = []

    allowed_predicates = [Parent, Mother, Father, Child, Sibling, Sister, Brother]
    # Names, basically
    # Using randomized names
    # allowed_atoms = namelike_strs(5, name_len=6)
    male_names, female_names = parse_names('names.txt')
    allowed_atoms = male_names + female_names

    # For now, add all atoms
    for atom in allowed_atoms:
        kb_list.append(atom)

    # sampling rule:
    # Choose random relationship

    num_tries = 5
    for a in range(num_tries):
        # random predicate
        try_pred = random.choice(allowed_predicates)
        # Try any 2 atoms.
        try_atoms = random.choices(allowed_atoms, k=2)

        # https://stackoverflow.com/questions/5924879/how-to-create-a-new-instance-from-a-class-object-in-python

        try_pred = try_pred(try_atoms)
        if try_pred.check_if_consistent(kb_list):
            print("Rule consistent: " + try_pred.get_nl_string())
            print("Adding...")
            # add
            kb_list.append(try_pred)
        else:
            print("Rule not consistent: " + try_pred.get_nl_string())

    print("Knowledge base: ")
    for clause in kb_list:
        if isinstance(clause, str):
            print(clause)
        else:
            print(clause.get_nl_string())

if __name__ == "__main__":
    basic_test_scenario()