def find_cycle_nodes(graph: dict) -> list:
    """Returns a list of nodes that are part of a cycle in the graph."""

    visited = set()
    rec_stack = []  # Use a list for tracking the recursion path
    cycle_nodes = []

    def dfs(node):
        nonlocal cycle_nodes
        visited.add(node)
        rec_stack.append(node)

        for neighbor in graph.get(node, []):
            if neighbor in rec_stack:
                # Cycle detected
                # Add only the nodes from the current node to the cycle's starting point
                cycle_nodes.append(rec_stack[rec_stack.index(neighbor):])
            elif neighbor not in visited:
                dfs(neighbor)

        rec_stack.pop() 

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycle_nodes

# graph = {"w0": ["ls1"], 
#          "ls1": ["w1"], 
#          "w1": ["le1"],
#          "le1": ["end", "w2"], 
#          "w2": ["ls2"],
#          "ls2": ["w3"],
#          "w3": ["le2"],
#          "w4": ["ls2"],
#          "le2": ["w4", "w5"],
#          "w5": ["w6"],
#          "w6": ["ls1"]
#         }
graph = {"w0": ["ls1"], 
         "ls1": ["w1"], 
         "w1": ["le1"],
         "le1": ["end", "w2"], 
         "w2": ["ls2"],
         "ls2": ["w3"],
         "w3": ["le2"],
         "le2": ["w4", "w5"],
         "w5": ["w6"],
        }
print(find_cycle_nodes(graph=graph))

