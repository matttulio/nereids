from jax import random
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import networkx as nx
import scienceplots

class Equations:

    def __init__(self, n_vars, n_eqs, max_sum_terms, max_mult_terms, non_lins, sym_non_lins=None, seed=42):
        """
            Initialize differential equations generator.

            Parameters:
            n_vars: number of variables of the system;
            n_eqs: number of equations to generate;
            max_sum_terms: max number of addends in each equation;
            max_mult_terms: max number of multiplicands in each addend;
            non_lins: list of all the possible non linearities;
            sym_non_lins: list of the symbolic expression of the non linearities.
        """

        # Initialize variables
        self.n_vars = n_vars
        self.n_eqs = n_eqs
        self.max_sum_terms = max_sum_terms
        self.max_mult_terms = max_mult_terms
        self.non_lins = non_lins
        self.sym_non_lins = sym_non_lins

        # If the symbols are not defined a priori, use generic names
        if(self.sym_non_lins == None):
            self.sym_non_lins = []
            for i in range(len(non_lins)):
                self.sym_non_lins.append(f"\\text{{nl}}_{i+1}")

        # Initialize lists for storing the equations
        # and their symbolic expression
        self.equations = []
        self.sym_expr = []

        self.key = random.key(seed)

        # Random generation of the number of addends to have in each equation
        n_sum_terms = random.randint(self.key, shape=(self.n_eqs,), minval=1, maxval=self.max_sum_terms+1)
        n_mult_terms = []

        for i in tqdm(range(self.n_eqs), desc="Generating Equations"):

            equation = []
            sym_eq = f"f_{{{i+1}}} = "

            # Loop on every addend in the i-th equation
            for _ in range(n_sum_terms[i]):

                self.key, subkey = random.split(self.key)
                n_mult_terms = random.randint(subkey, shape=(1,), minval=1, maxval=self.max_mult_terms+1)  # Draw how many multiplicands for the i-th addend
                non_lins_idxs = random.randint(subkey, shape=(n_mult_terms[0],), minval=0, maxval=len(self.non_lins))  # Draw a number of n_mult_terms of nls with replacement
                var_to_be_applied_idxs = random.randint(subkey, shape=(n_mult_terms[0],), minval=0, maxval=self.n_vars)  # Draw to which variable apply the non-linearities

                # Create an array of the length equal to the number of variables
                # such that each position represent the variable to which apply
                # the non-linearity/ies
                addend = np.ones(self.n_vars).tolist()
                sym_addend = ""

                for j in list(set(var_to_be_applied_idxs.tolist())):
                    idxs = non_lins_idxs[np.where(var_to_be_applied_idxs == j)]
                    temp = []

                    for k in idxs:
                        temp.append(self.non_lins[k])
                        sym_addend += self.sym_non_lins[k] + f"(y_{{{j+1}}})"

                    addend[j] = temp  # Add the the non-linearity/ies in the position where it should ne applied
                    
                equation.append(addend)
                
                sym_eq += sym_addend + " + "

            self.equations.append(equation)

            sym_eq = sym_eq[:-3]
            self.sym_expr.append(sym_eq)
        
    # Function that defines the oject's output
    def __getitem__(self, idx):
        return self.equations[idx], self.sym_expr[idx]
    

    # The call method can be passed to a standard python
    # solver for differential equations
    def __call__(self, t, y):

        f = []  # List that will have all the equations
        
        # Cycle that build eqs eq by eq
        for i in range(self.n_eqs):

            eq = 0  # Initialize eq to zero

            # Cycle over all the addends
            for j in range(len(self.equations[i])):

                addend = 1
                func_idxs = [_ for _, element in enumerate(self.equations[i][j]) if element != 1.0]  # Find to which variables there are nls

                for k in func_idxs:
                    for func in self.equations[i][j][k]:
                        addend *= func(y[k])  # Apply the nls to the variable

                eq += addend  # Once the addend has all the multiplicands, add it to the eq

            f.append(eq)  # Once eq is complete append it to the list

        return f
    
    # Function useful to display the generated equations
    def show_equations(self, save=False, filename=None):

        plt.style.use('science')
        plt.rcParams['text.usetex'] = True
        
        fig, ax = plt.subplots(figsize=(16, 8))

        # Hide axes
        ax.axis('off')

        # Loop over the list of expressions and render each one
        for idx, expr in enumerate(self.sym_expr):
            ax.text(0.5, 1 - (idx * 0.2), f"${expr}$", fontsize=20, ha='center', va='top')

        if(save):
            if(filename==None):
                plt.savefig('expressions.pdf', format='pdf', bbox_inches='tight')
            else:
                plt.savefig(filename, format='pdf', bbox_inches='tight')
        else:
            plt.show()

        plt.clf()
        plt.close()


    def show_graph(self, save=False, filename=None):

        variables = [f"y_{{{i+1}}}" for i in range(self.n_vars)]
        funcs = [f"f_{{{i+1}}}" for i in range(self.n_eqs)]

        # Initialize a graph to store interactions
        G = nx.DiGraph()
        G.add_nodes_from(variables)
        G.add_nodes_from(funcs)

        # Iterate over the equations
        i = 0
        for eq in self.equations:
            active_idxs = []
            
            # Collect variable indices for the terms in the equation
            for term in eq:
                active_idxs.extend([_ for _, element in enumerate(term) if element != 1.0])

            for j in range(len(active_idxs)):
                # From variable to function
                G.add_edge(variables[active_idxs[j]], funcs[i])

            i += 1

        # Plot the interaction graph
        plt.figure(figsize=(8, 6))

        # Define positions using spring layout
        pos = nx.spring_layout(G, k=10, iterations=5000)

        # Set LaTeX rendering for labels
        plt.rc('text', usetex=True)

        # Define node colors: blue for variables, green for functions
        node_colors = ['skyblue' if node in variables else 'lightgreen' for node in G.nodes]

        # Draw the graph with labels
        nx.draw(G, pos, with_labels=True, labels={node: f"${node}$" for node in G.nodes()},
                node_size=1000, node_color=node_colors, font_size=12, font_weight='bold')

        if(save):
            if(filename==None):
                plt.savefig('graph.pdf', format='pdf', bbox_inches='tight')
            else:
                plt.savefig(filename, format='pdf', bbox_inches='tight')
        else:
            plt.show()

        plt.clf()
        plt.close()