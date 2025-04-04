import random

class Statement:
    def __init__(self, str_true, str_false, str_question, state=0):
        """
            str_true = string of statement in state 1
            str_false = string of statement in state 2
            str_question = string for statement as a question; always state 1
            state = state of the statement
                0 = undetermined
                1 = state 1 (true)
                2 = state 2 (false)
        """
        self.state = state
        self.str_true = str_true
        self.str_false = str_false
        self.str_question = str_question

problem1_statement_set = [Statement("it is raining", "it is not raining", "is it raining?"), 
                          Statement("the ground is wet", "the ground is not wet", "is the ground wet?"),
                          Statement("bob is wearing boots", "bob is not wearing boots", "is bob wearing boots?"),
                          Statement("bob is wearing a coat", "bob is not wearing a coat", "is bob wearing a coat?")]

class Problem:
    def __init__(self, statements):
        self.statements = statements
    
    def generate(self, start_point=-1):
        if start_point == -1:
            start_point = random.randrange(0, len(self.statements))
        

problem1 = Problem(problem1_statement_set)