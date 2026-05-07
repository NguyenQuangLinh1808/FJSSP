def apply_c6_old(solver):
    # Constraint 7: Liên kết biến Active (A) với Machine (M) và Start (S)
    for i in range(solver.num_ops):
        for t in range(solver.est[i], solver.lst[i] + 1):
            s_var = solver.get_var('S', i, t)

            for mach, p in solver.ops[i]['machines']:
                max_start_m = solver.lst[i] + solver.min_p[i] - p
                if t > max_start_m:
                    continue

                m_var = solver.get_var('M', i, mach)
                for tau in range(t, t + p):
                    a_var = solver.get_var('A', i, tau)
                    solver.add_clause_smart([-m_var, -s_var, a_var])