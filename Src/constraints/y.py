def apply_y(solver):
    """
    Constraint 8 (y.py): A_{i,t} -> ~X_{i,t+1}
    """
    for i in range(solver.num_ops):
        op_data = solver.ops[i]
        if not op_data['machines']:
            continue
        max_p = max(p for m, p in op_data['machines'])
        max_active_time = solver.lst[i] + max_p - 1

        for t in range(solver.est[i], max_active_time + 1):
            a_var = solver.get_var('A', i, t)
            x_next = solver.get_x_bounded(i, t + 1)

            solver.add_clause_smart([-a_var, solver.neg(x_next)])