def apply_x(solver):
    for i in range(solver.num_ops):
        valid_machines = set(m for m, p in solver.ops[i]['machines'])
        for m in range(solver.num_machines):
            if m not in valid_machines:
                solver.add_clause_smart([-solver.get_var('M', i, m)])