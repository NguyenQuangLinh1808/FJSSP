def apply_c2_ver2(solver):
    """
    Constraint 2: Tính liền mạch của biến X (Step variable)
    X[i, t] >= X[i, t+1] -> CNF: ~X[i, t+1] V X[i, t]
    """
    for i in range(solver.num_ops):
        for t in range(solver.est[i], solver.lst[i] + 1):
            x_curr = solver.get_x_bounded(i, t)
            x_next = solver.get_x_bounded(i, t + 1)

            solver.add_clause_smart([solver.neg(x_next), x_curr])