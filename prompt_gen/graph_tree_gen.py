# jlim@wpi.edu
# Basic scenario generation for the family tree scenario.
# Inspired by logicAsker and Prolog.
import datetime
# Inspiration: https://stackoverflow.com/questions/2823316/generate-a-random-letter-in-python
import string
import random
import copy
import uuid
import pickle
import re

# Using neo4j for building a knowledge base, checking relationships
import neo4j
from neo4j import GraphDatabase

# Scenario generation: Create a tree, randomly add nodes.

# Question generation: Sub-functions for creating templates. No easy way around; just need to

# Easy question generation: Only the stated relationships.

# Hard question generation: Each relationship has a check function...

# Map to what we put in the neo4j database...
class PredicatePattern:
    def __init__(self, arglist):
        self.arglist = arglist
        self.graphDBType = ""

    def __getitem__(self, i):
        return self.arglist[i]

    def dbType(self):
        return self.graphDBType

    def addquery(self):
        # Return a string; this is the query needed to add this relationship to the database.
        # Relationships have the following properties:
        # Type - not actually Neo4j property, but used for querying.
        # transact_id - id for a particular transaction - useful for removing en masse if needed.
        # implication_level - number denoting how many steps needed to create this relationship.
        #  Level 0 means it's part of the premises.
        #  Levels 1+ require 1+ executions of build_implications to derive.
        # We can promote Level 1+ implications to Level 0.
        return ""

    # Print the natural language form of this predicate.
    def get_nl_string(self):
        pass

    def is_equal(self, otherPredicate):
        # A predicate is equal if it has the same predicate list, and is the same class.
        return (type(self) == type(otherPredicate)) and (self.arglist == otherPredicate.arglist)
    #
    # # For rebinding names.
    # def rebind_args(self, argslist):
    #     self.argslist = argslist
    #
    # def get_args(self, argslist):
    #     return self.argslist


class Male(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Male"

    def get_nl_string(self):
        return self.arglist[0] + " is male"

    def dbType(self):
        return self.graphDBType

    # Fighting weird merge semantics: https://stackoverflow.com/questions/74960958/neo4j-cypher-create-relationship-only-if-destination-node-exists
    def addquery(self):
        # Need to set this up so merge semantics aren't dumb.
        variable_preamble = "MATCH (a:Person {name:$arg0})"
        return variable_preamble + " MERGE (a)-[r:Male]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Female(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Female"

    def get_nl_string(self):
        return self.arglist[0] + " is female"

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0})"
        return variable_preamble + " MERGE (a)-[r:Female]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

# Binary
class Parent(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Parent"

    def get_nl_string(self):
        return self.arglist[0] + " is a parent of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Parent]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"


class Mother(Parent):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Mother"

    def get_nl_string(self):
        return self.arglist[0] + " is a mother of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Mother]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Father(Parent):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Father"

    def get_nl_string(self):
        return self.arglist[0] + " is a father of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Father]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Child(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Child"

    def get_nl_string(self):
        return self.arglist[0] + " is a child of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Child]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Sibling(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Sibling"

    def get_nl_string(self):
        return self.arglist[0] + " is a sibling of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Sibling]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Sister(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Sister"

    def get_nl_string(self):
        return self.arglist[0] + " is a sister of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Sister]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Brother(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Brother"

    def get_nl_string(self):
        return self.arglist[0] + " is a brother of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Brother]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

# additional child relationships
class Son(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Son"

    def get_nl_string(self):
        return self.arglist[0] + " is a son of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Son]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Daughter(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Daughter"

    def get_nl_string(self):
        return self.arglist[0] + " is a daughter of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Daughter]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"


# Infer-only relationships
class Grandparent(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Grandparent"

    def get_nl_string(self):
        return self.arglist[0] + " is a grandparent of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Grandparent]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"


class GrandMother(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Grandmother"

    def get_nl_string(self):
        return self.arglist[0] + " is a grandmother of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Grandmother]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class GrandFather(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Grandfather"

    def get_nl_string(self):
        return self.arglist[0] + " is a grandfather of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Grandfather]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"


class Aunt(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Aunt"

    def get_nl_string(self):
        return self.arglist[0] + " is an aunt of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:Aunt]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"

class Uncle(PredicatePattern):
    def __init__(self, arglist):
        super().__init__(arglist)
        self.graphDBType = "Uncle"

    def get_nl_string(self):
        return self.arglist[0] + " is an uncle of " + self.arglist[1]

    def addquery(self):
        variable_preamble = "MATCH (a:Person {name:$arg0}) MATCH (b:Person {name:$arg1})"
        return variable_preamble + " MERGE (a)-[r:uncle]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level ON MATCH SET r.implication_level = $implication_level"



STR_TO_PREDICATES = {
    'Male': Male,
    'Female': Female,
    'Parent': Parent,
    'Mother': Mother,
    'Father': Father,
    'Child': Child,
    'Sibling': Sibling,
    'Sister': Sister,
    'Brother': Brother,
    'Son': Son,
    'Daughter': Daughter,
    # infer only below
    'Grandparent': Grandparent,
    'Grandmother': GrandMother,
    'Grandfather': GrandFather,
    'Aunt': Aunt,
    'Uncle': Uncle

}


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
    parsed_names = 0
    for idx, line in enumerate(file_lines):
        if line != '\n':
            parsed_names += 1
            tokens = line.split(" ")
            if parsed_names <= num_names:
                male_names.append(tokens[1].rstrip("\n"))
            else:
                female_names.append(tokens[1].rstrip("\n"))

    return male_names, female_names

# Build all implications based on the rules we defined here.
# Return an id to track all of the implications we added, or none if nothing was added!
# Note: This will need to be run multiple times most likely.
def build_implications(db_driver, implication_level):
    transact_id = str(uuid.uuid4())
    num_records_created = 0

    # {implication_level:$implication_level, transact_id:$transact_id}
    implications = [
        # Gender implies gendered parent relationships
        "MATCH (a:Person)<-[:Male]-(a:Person)-[:Parent]->(b:Person) MERGE (a)-[r:Father]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)<-[:Female]-(a:Person)-[:Parent]->(b:Person) MERGE (a)-[r:Mother]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # gendered parent relationships imply gender
        "MATCH (a:Person)-[:Father]->(b:Person) MERGE (a)-[r:Male]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Mother]->(b:Person) MERGE (a)-[r:Female]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Gender -> Sibling variant
        "MATCH (a:Person)<-[:Male]-(a:Person)-[:Sibling]->(b:Person) MERGE (a)-[r:Brother]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)<-[:Female]-(a:Person)-[:Sibling]->(b:Person) MERGE (a)-[r:Sister]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Sibling variant -> Gender
        "MATCH (a:Person)-[:Brother]->(b:Person) MERGE (a)-[r:Male]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Sister]->(b:Person) MERGE (a)-[r:Female]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Gendered links imply nongendered links.
        "MATCH (a:Person)-[:Brother|Sister]->(b:Person) MERGE (a)-[r:Sibling]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Father|Mother]->(b:Person) MERGE (a)-[r:Parent]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Child -> Parent
        "MATCH (a:Person)-[:Child]->(b:Person) MERGE (b)-[r:Parent]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Parent -> Child
        "MATCH (a:Person)-[:Parent]->(b:Person) MERGE (b)-[r:Child]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Siblings imply shared parents
        "MATCH (p:Person)-[:Parent]->(a:Person)-[:Sibling]-(b:Person) MERGE (p)-[r:Parent]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Shared Parents imply shared siblings
        "MATCH (a:Person)-[:Child]->(p:Person)<-[:Child]-(b:Person) MERGE (b)-[r:Sibling]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Siblings are two-way.
        "MATCH (a:Person)-[:Sibling]->(b:Person) MERGE (b)-[r:Sibling]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Siblings are transitive, given scenario changes.
        "MATCH (a:Person)-[:Sibling]->(b:Person)-[:Sibling]->(c:Person) WHERE a <> c MERGE (a)-[r:Sibling]->(c) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Gendered children imply child.
        "MATCH (a:Person)-[:Son]->(b:Person) MERGE (a)-[r:Child]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Daughter]->(b:Person) MERGE (a)-[r:Child]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # children with gender imply son/daughter.
        "MATCH (a:Person)<-[:Male]-(a:Person)-[:Child]->(b:Person) MERGE (a)-[r:Son]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)<-[:Female]-(a:Person)-[:Child]->(b:Person) MERGE (a)-[r:Daughter]->(b) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Gender implications of son/daughter
        "MATCH (a:Person)-[:Son]->(b:Person) MERGE (a)-[r:Male]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Daughter]->(b:Person) MERGE (a)-[r:Female]->(a) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Implication only relationships here.
        # Grandparentage
        "MATCH (a:Person)-[:Parent]->(b:Person)-[:Parent]->(c:Person) MERGE (a)-[r:Grandparent]->(c) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Male]->(a:Person)-[:Grandparent]->(c:Person) MERGE (a)-[r:Grandfather]->(c) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Female]->(a:Person)-[:Grandparent]->(c:Person) MERGE (a)-[r:Grandmother]->(c) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        # Aunts/uncles
        "MATCH (a:Person)-[:Male]->(a:Person)-[:Sibling]->(c:Person)-[:Parent]->(d:Person) MERGE (a)-[r:Uncle]->(d) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
        "MATCH (a:Person)-[:Female]->(a:Person)-[:Sibling]->(c:Person)-[:Parent]->(d:Person) MERGE (a)-[r:Aunt]->(d) ON CREATE SET r.transact_id = $transact_id, r.implication_level = $implication_level",
    ]

    for impl in implications:
        records, summary, keys = db_driver.execute_query(impl, transact_id=transact_id, implication_level=implication_level,
                                database_="neo4j")

        num_records_created += summary.counters.relationships_created

    if num_records_created != 0:
        return transact_id
    else:
        return None


def check_contradictions(db_driver, max_loop_length):
    # Check if any contradictions exist.
    # True means no contradictions, false means some check failed!
    # List of queries where no matches should be found.

    # Useful: https://neo4j.com/docs/cypher-manual/current/subqueries/count/
    contradictions = [
        # Simplistic gender logic for now
        "MATCH (p:Person)<-[:Male]-(p:Person)-[:Female]->(p:Person) RETURN p",
        # Only gender is unary.
        "MATCH (p:Person)<-[:Parent|Mother|Father|Child|Sibling|Brother|Sister]-(p:Person) RETURN p",
        # 2 parents max
        # "MATCH (a:Person)-[:Child]->(p:Person) WHERE count(p) > 2",
        "MATCH (p:Person) WHERE COUNT{(p:Person)<-[:Parent]-(a:Person)} > 2 return p",
        # Parents must be of opposite gender - ignore step-relation issues.
        "MATCH (a:Person)-[:Male]->(a:Person)-[:Parent]->(p:Person)<-[:Parent]-(b:Person)-[:Male]->(b:Person) return p",
        "MATCH (a:Person)-[:Female]->(a:Person)-[:Parent]->(p:Person)<-[:Parent]-(b:Person)-[:Female]->(b:Person) return p",

        # Siblings will not be parents.
        "MATCH (a:Person)-[:Parent]->(p:Person)<-[:Parent]-(b:Person) MATCH (a:Person)-[:Sibling]->(b:Person) return a",

        # Colliding relationships TODO: Check
        "MATCH (a:Person)-[:Child]->(p:Person)-[:Child]->(a:Person) RETURN a",
        # No parent loops!!!. Inspiration: https://stackoverflow.com/questions/45427562/find-loops-in-neo4j
        # Note: Doing some ugly string sub here... parameters not working!
        "MATCH (p:Person)(()-[:Parent]->()){1,{max_loop_length}}(p:Person) RETURN p",
        # Parents cannot have shared ancestry
        "MATCH (p:Person)-[:Child]->(a:Person)(()-[:Parent|Sibling]->()){1,{max_loop_length}}(b:Person)<-[:Child]-(p:Person) WHERE a<>b RETURN p"
    ]

    for test in contradictions:

        # Weirdly, does not support parameters for quantified path patterns.
        if "{max_loop_length}" in test:
            test = test.replace("{max_loop_length}", str(max_loop_length))

        records, summary, keys = db_driver.execute_query(test, database_="neo4j")


        if len(records) != 0:
            return False

    return True

def get_rand_inference_relation(db_driver):
    # TODO: Query random relationship where implication_level > 0!
    # Need to map back to one of our predicate patterns to return too.
    return None


QUESTION_STR = "Is it correct that {}?"

# Quickstart: https://neo4j.com/docs/python-manual/current/
def generate_scenario(driver, male_names, female_names, hard_sample_count, num_people=5, num_rels_target=7, debug_predicates=None, debug_people=None):

    # print("Begin scenario generation...")
    max_implications = num_people  # Maximum number of times we expand implications.

    # So we don't hang forever...
    max_tries = num_rels_target * 3

    # Some predicates are more complicated to add, so only the subset here is added.
    predicate_options = [
        Parent, Mother, Father, Child, Son, Daughter, Sibling, Sister, Brother,
    ]

    # Balance parent/child implying relationships with sibling/brother relationships
    # balance 6/9 with 3/9
    predicate_prob_weights = [1/9, 1/9, 1/9, 1/9, 1/9, 1/9, 2/9, 2/9, 2/9]

    premises = []

    # CLEAR
    temp = driver.execute_query("MATCH (n) DETACH DELETE n",
                         database_="neo4j")

    if debug_people is None:
        nameset = [str(uuid.uuid4()) for x in range(num_people)] # we rebind to real names later in the process.
    else:
        nameset = debug_people
    # temp.summary.counters .nodes_created .relationships_created .properties_set
    # Put all of the nodes in the database.
    for name in nameset:
        temp = driver.execute_query("MERGE (:Person {name: $name})",
                             name=name,
                             database_="neo4j")

    failcount = 0
    tries = 0
    debug_index = 0
    while len(premises) < num_rels_target and tries < max_tries:
        tries += 1

        if debug_predicates is None:

            # Try to add a relationship.
            # Randomly choose 2 names.
            arg_names = random.sample(nameset, k=2)

            # Randomly choose a relationship
            # relationship_type = random.choice(predicate_options)
            #
            # if tries == 1:
            #     # Force sibling for testing!
            #     relationship_type = Sibling
            # else:
            relationship_type = random.choices(predicate_options, weights=predicate_prob_weights)[0]


            relationship = relationship_type(arg_names)

        else:
            relationship = debug_predicates[debug_index]
            debug_index += 1


        # check for unique relationship
        unique = True
        for premise in premises:
            if relationship.is_equal(premise):
                unique = False

        if not unique:
            # Try again!
            failcount += 1
            continue

        transact_ids = [str(uuid.uuid4())]

        # print("Trying premise: " + relationship.get_nl_string())

        # Try adding the relationship
        temp = driver.execute_query(relationship.addquery(), arg0=relationship[0], arg1=relationship[1], implication_level=0, transact_id=transact_ids[0])

        # TODO: Logic to clear & rebuild implication steps after every added node?
        # It will allow our implication level number to be accurate...
        # Expand implications... what can be inferred from current premises?
        for a in range(max_implications):
            # For now, a+1 is the implication level.
            new_id = build_implications(driver, (a+1))
            if new_id is None:
                break
            else:
                transact_ids.append(new_id)
        # Annoying warning: Neo.ClientNotification.Statement.UnknownRelationshipTypeWarning
        # Now we need to check what we
        if check_contradictions(driver, max_loop_length=num_people):
            # print("Added \"" + relationship.get_nl_string() + "\".")
            premises.append(relationship)
        else:
            # print("Failed! Adding \"" + relationship.get_nl_string() + "\" was a Contradiction...")
            # Failed! Need to undo all of that work...
            # Remove relationships that we added...
            if debug_predicates is not None:
                print("Unexpected failure!!!")

            failcount += 1
            for t_id in transact_ids:
                temp = driver.execute_query("Match ()-[r {transact_id:$transact_id}]->() DELETE r",
                                     transact_id=t_id,
                                     database_="neo4j")


    # Search for "hard" questions, return a sampling.
    records, summary, keys = driver.execute_query("match (a)-[r]->(b) WHERE r.implication_level > 0 return a, r, b", database_="neo4j")
    # name: records[0][0].items().mapping['name'], relation: records[0][1].type

    # Always grab the maximum number of samples!
    if hard_sample_count < len(records) and False:
        rand_idxs =  random.sample(range(len(records)), k=hard_sample_count)
    else:
        rand_idxs = range(len(records))
    hard_qs = []
    for i in rand_idxs:
        start_name = records[i][0].items().mapping['name']
        relation_str = records[i][1].type
        end_name = records[i][2].items().mapping['name']

        hard_relationship = STR_TO_PREDICATES[relation_str]([start_name, end_name])
        hard_qs.append(hard_relationship)


    # Rebind names in premises according to gender.
    records_male, summary, keys = driver.execute_query("match (a)-[:Male]->(a) return a",
                                                  database_="neo4j")
    records_female, summary, keys = driver.execute_query("match (a)-[:Female]->(a) return a",
                                                  database_="neo4j")

    male_names_choices = random.sample(male_names, k=len(records_male))
    female_names_choices = random.sample(female_names, k=len(records_female))

    name_mapping = {}
    used_names = male_names_choices + female_names_choices

    # map nameset -> real names!
    for i in range(len(records_male)):
        record_id = records_male[i][0].items().mapping['name']
        name_mapping[record_id] = male_names_choices[i]

    for i in range(len(records_female)):
        record_id = records_female[i][0].items().mapping['name']
        name_mapping[record_id] = female_names_choices[i]

    combined_name_candidates = male_names + female_names

    # randomly bind remaining names
    # TODO: How to check consistency for remaining names?
    for uid in nameset:
        if uid not in name_mapping:

            # We need to try a gender, see if it's consistent
            test_is_male = random.choice([True, False])

            if test_is_male:
                test_premise = Male([uid])
            else:
                test_premise = Female([uid])

            transact_ids = [str(uuid.uuid4())]
            temp = driver.execute_query(test_premise.addquery(), arg0=test_premise[0], implication_level=0, transact_id=transact_ids[0])

            # TODO: Logic to clear & rebuild implication steps after every added node?
            # It will allow our implication level number to be accurate...
            # Expand implications... what can be inferred from current premises?
            for a in range(max_implications):
                # For now, a+1 is the implication level.
                new_id = build_implications(driver, (a + 1))
                if new_id is None:
                    break
                else:
                    transact_ids.append(new_id)

            # If this gender creates a contradiction, flip it; we have the answer now.
            if not check_contradictions(driver, max_loop_length=num_people):
                test_is_male = not test_is_male

            # Remove needed records.
            for t_id in transact_ids:
                temp = driver.execute_query("Match ()-[r {transact_id:$transact_id}]->() DELETE r",
                                            transact_id=t_id,
                                            database_="neo4j")

            if test_is_male:
                gendered_name_set = male_names
            else:
                gendered_name_set = female_names

            # try to choose random name.
            name = random.choice(gendered_name_set)
            while name in used_names:
                # Simple...
                name = random.choice(gendered_name_set)

            name_mapping[uid] = name

    people = [name_mapping[x] for x in list(name_mapping.keys())]

    # rebind premise names
    for p in premises:
        args = p.arglist
        args = [name_mapping[x] for x in args] # Rebind
        p.arglist = args

    # rebind names in set of hard qs.
    for p in hard_qs:
        args = p.arglist
        args = [name_mapping[x] for x in args] # Rebind
        p.arglist = args

    # Choose a random easy question from the premises.
    # easy_q = QUESTION_STR.format(random.choice(premises).get_nl_string())
    easy_q = random.choice(premises)

    # print("Number of tries: " + str(tries))
    # print("Number of failures: " + str(failcount))
    # print("Final Premises:")
    # for p in premises:
    #     print(p.get_nl_string())
    #
    # print("")
    # print("Random easy question(premise): ")
    # print(easy_q.get_nl_string())
    #
    # print("")
    # print("Hard question candidates: ")
    # for h in hard_qs:
    #     print(h.get_nl_string())

    return people, premises, easy_q, hard_qs


def convert_format(old_pickle, new_pickle):
    with open(old_pickle, 'rb') as f:
        results = pickle.load(f)

    scenarios = []
    for r in results:
        record = {
            'people': r[0],
            'premises': [x.get_nl_string() for x in r[1]],
            'easy_infer': r[2].get_nl_string(),
            'hard_infer': [x.get_nl_string() for x in r[3]],
        }
        scenarios.append(record)

    with open(new_pickle, 'wb') as f2:
        pickle.dump(scenarios, f2)

def main(test_scenarios_path, num_scenarios=10000):
    # For now, generate a whole bunch of scenarios.
    print("Parsing names...")
    male_names, female_names = parse_names('names.txt')
    full_nameset = male_names + female_names

    print("Starting scenario generation...")
    # num_scenarios = 10000

    uri = "neo4j://localhost:7687"
    # Really basic local database for development. Not a production instance...
    db_pass = input("Enter db password: ")
    auth = ("neo4j", db_pass) # local db, only for development...

    total_hard_count = 0

    # Probability distribution for number of people, number of relationships involved.
    min_people = 4
    max_people = 8

    # limit to just 6 people for computation's sake!
    # min_people = 4
    # max_people = 6

    # Reduce max relationship to 9?
    min_rel = 3
    max_rel = 12

    # # Reduce max relationship to 9?
    # min_rel = 3
    # max_rel = 9

    # Will encode most of the information in the "name" property. All nodes are Object, all relations are RELATION
    results = []
    with GraphDatabase.driver(uri, auth=auth) as driver:
        starttime = datetime.datetime.now()
        for a in range(num_scenarios):
            num_people = random.randint(min_people, max_people)
            num_relations = random.randint(min_rel, max_rel)

            hard_sample_count = int(num_relations * 1.5)
            if a % 10 == 0:
                print(str(a) + "/" + str(num_scenarios))
                total_elapsed = datetime.datetime.now() - starttime
                print("Total elapsed time: " + str(total_elapsed.total_seconds()))

                with open(test_scenarios_path, 'wb') as f:
                    pickle.dump(results, f)

            r = generate_scenario(driver, male_names, female_names, num_people=num_people,
                                  num_rels_target=num_relations, hard_sample_count=hard_sample_count)
            record = {
                'people': r[0],
                'premises': [x.get_nl_string() for x in r[1]],
                'hard_infer_list': [x.get_nl_string() for x in r[3]],
                'hard_infer_responses': [None for x in r[3]]
            }
            total_hard_count += len(r[3])
            results.append(record)

    print("Total number of hard inferences generated: " + str(total_hard_count))
    # Save results.
    with open(test_scenarios_path, 'wb') as f:
        pickle.dump(results, f)

    print("Done.")

def rebuild_people_list(people_str):
    startstr = re.split("[ ,.]+", people_str)
    # no empty strings!
    return list(filter(lambda x: len(x) > 0, startstr))

# Quickly rebuild a set of predicates from a string, for debugging.
def rebuild_predicate(pred_str):
    predicate_type = None
    for pred_key in STR_TO_PREDICATES.keys():
        if pred_key.lower() in pred_str.lower():
            predicate_type = STR_TO_PREDICATES[pred_key]
            break

    # rebuild predicate.
    if predicate_type is None:
        raise Exception("Cannot find predicate.")
    if predicate_type == Male or predicate_type == Female:
        raise Exception("Not handling this right now.")
    else:
        # find parameters
        tokens = re.split("[ .]+", pred_str)
        tokens = list(filter(lambda x: len(x) > 0, tokens))
        return predicate_type([tokens[0], tokens[-1]])

def debug_scenario():
    # For now, generate a whole bunch of scenarios.
    print("Parsing names...")
    male_names, female_names = parse_names('names.txt')
    full_nameset = male_names + female_names

    print("Starting scenario generation...")
    # num_scenarios = 10000

    uri = "neo4j://localhost:7687"
    # Really basic local database for development. Not a production instance...
    db_pass = input("Enter db password: ")
    auth = ("neo4j", db_pass)  # local db, only for development...

    # # debug_people = ["Carter", "Nevaeh", "Cecilia", "Isabelle", "Emilia", "Elena", "Ethan", "Henry"]
    # debug_people = rebuild_people_list("Carter, Nevaeh, Cecilia, Isabelle, Emilia, Elena, Ethan, Henry.")
    # # Isabelle is a sister of Emilia.
    # # Elena is a child of Cecilia.
    # # Henry is a child of Elena.
    # # Elena is a child of Emilia.
    # # Carter is a brother of Ethan.
    # # Carter is a parent of Henry.
    # # Nevaeh is a sister of Emilia.
    # # Isabelle is a sister of Cecilia.
    # # Carter is a father of Henry.
    # # Cecilia is a sister of Isabelle.
    # debug_predicates = [
    #     rebuild_predicate("Isabelle is a sister of Emilia."),
    #     rebuild_predicate("Elena is a child of Cecilia."),
    #     rebuild_predicate("Henry is a child of Elena."),
    #     rebuild_predicate("Elena is a child of Emilia."),
    #     rebuild_predicate("Carter is a brother of Ethan."),
    #     rebuild_predicate("Carter is a parent of Henry."),
    #     rebuild_predicate("Nevaeh is a sister of Emilia."),
    #     rebuild_predicate("Isabelle is a sister of Cecilia."),
    #     rebuild_predicate("Carter is a father of Henry."),
    #     rebuild_predicate("Cecilia is a sister of Isabelle."),
    # ]

    debug_people = rebuild_people_list("Levi, Alexandria, Kaiden, Bentley, Zion, Sawyer, Declan.")
    # Alexandria is a mother of Levi.
    # Levi is a father of Sawyer.
    # Kaiden is a child of Bentley.
    # Bentley is a parent of Kaiden.
    # Levi is a child of Alexandria.
    # Sawyer is a child of Zion.
    # Bentley is a child of Sawyer.
    # Is this statement true: Zion is a parent of Sawyer.

    debug_predicates = [
        rebuild_predicate("Alexandria is a mother of Levi."),
        rebuild_predicate("Levi is a father of Sawyer."),
        rebuild_predicate("Kaiden is a child of Bentley."),
        rebuild_predicate("Bentley is a parent of Kaiden."),
        rebuild_predicate("Levi is a child of Alexandria."),
        rebuild_predicate("Sawyer is a child of Zion."),
        rebuild_predicate("Bentley is a child of Sawyer."),
    ]

    with GraphDatabase.driver(uri, auth=auth) as driver:
        generate_scenario(driver, male_names, female_names, 1, num_people=len(debug_people), num_rels_target=len(debug_predicates),
                          debug_predicates=debug_predicates, debug_people=debug_people)

if __name__ == "__main__":
    # main('Test_largeset.pickle')
    # convert_format('Test_2000.pickle', 'Scenarios_2000.pickle')
    # convert_format('Test_largeset.pickle', 'Scenarios_10000.pickle')
    # main('test_mini.pickle', 100)
    # main('test_moderate.pickle', 1000)
    # main('test_mini_more_relations2.pickle', 300)
    # main('scenarios_set_medium.pickle', 1000)
    main('scenarios_set_medium_large.pickle', 2000)

    # Debugging
    # debug_scenario()
    # Note: Post code! make it open source...