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
    
    def copy(self):
        return Statement(self.str_true, self.str_false, self.str_question, self.state)
    
    def __str__(self):
        if self.state == 0:
            return "undetermined"
        elif self.state == 1:
            return self.str_true
        else:
            return self.str_false

class Operation:
    def __init__(self, operation, op_left, op_right=None):
        self.operation = operation
        self.op_left = op_left
        self.op_right = op_right
        self.solved = False
    
    def solve(self, statements):
        if self.operation == 0 and self.op_left.solve(statements):
            if statements[self.op_right.op_left].state == 0:
                statements[self.op_right.op_left].state = self.op_right.op_right
                self.solved = True
                return statements
            else:
                return None
        elif self.operation == 1:
            return self.op_left.solve(statements) and self.op_right.solve(statements)
        elif self.operation == 2:
            return self.op_left.solve(statements) or self.op_right.solve(statements)
        elif self.operation == 3:
            return statements[self.op_left].state == self.op_right
            

class Problem:
    def __init__(self, statements, op_string):
        self.statements = statements
        
        propositions = []
        operations = op_string.split(" ")
        for op in operations:
            propositions.append(self.interpret_operation(op))
        
        self.propositions = propositions
    
    def find_unknowns(self):
        progress_flag = True
        while progress_flag:
            progress_flag = False
            for proposition in self.propositions:
                new_statements = proposition.solve(self.statements)
                if(new_statements):
                    progress_flag = True
                    self.statements = new_statements
                    
    def set_knowns(self, known_statements):
        for ks in known_statements:
            self.statements[ks[0]].state = ks[1]
    
    def interpret_operation(self, op):
        # Remove pointless parenthesis
        if op[0] == "(" and op[-1] == ")":
            op = op[1:-1]
        
        if len(op.split(">")) > 1:
            left, right = op.split(">")
            return Operation(0, self.interpret_operation(left), self.interpret_operation(right))
        elif op.find("^") != -1 or op.find("v") != -1:
            par_track = 0
            for i, char in enumerate(op):
                if char == "(":
                    par_track += 1
                elif char == ")":
                    par_track -= 1
                elif par_track == 0 and char == "^":
                    return Operation(1, self.interpret_operation(op[:i]), self.interpret_operation(op[i+1:]))
                elif par_track == 0 and char == "v":
                    return Operation(2, self.interpret_operation(op[:i]), self.interpret_operation(op[i+1:]))
        else:
            if op[0] == "~":
                return Operation(3, int(op[1:]), 2)
            else:
                return Operation(3, int(op), 1)

    def find_answer(self, statement_index):
        return str(self.statements[statement_index])
        
problem1_statement_set = [Statement("it is raining", "it is not raining", "is it raining?"), 
                          Statement("the ground is wet", "the ground is not wet", "is the ground wet?"),
                          Statement("bob is wearing boots", "bob is not wearing boots", "is bob wearing boots?"),
                          Statement("bob is wearing a coat", "bob is not wearing a coat", "is bob wearing a coat?")]

problem1 = Problem(problem1_statement_set, "0>1 0>2 2^3>0 ~3>~0 1>3")
problem1.set_knowns([[2, 1], [3, 1]])
problem1.find_unknowns()
print(problem1.find_answer(0))