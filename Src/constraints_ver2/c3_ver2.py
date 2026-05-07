def apply_c3_ver2(solver):
    """
    Constraint 3: Kích hoạt biến S (Start time)
    S[i, t] <-> (X[i, t] & ~X[i, t+1])
    """
    for i in range(solver.num_ops):
        for t in range(solver.est[i], solver.lst[i] + 1):
            x_curr = solver.get_x_bounded(i, t)
            x_next = solver.get_x_bounded(i, t + 1)

            # Khởi tạo biến S
            s_var = solver.get_var('S', i, t)

            # 3 mệnh đề CNF để ép quan hệ tương đương (<->)
            solver.add_clause_smart([-s_var, x_curr])
            solver.add_clause_smart([-s_var, solver.neg(x_next)])
            solver.add_clause_smart([solver.neg(x_curr), x_next, s_var])
