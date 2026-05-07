def apply_c6(solver):
    # Constraint 7: Tối ưu hoá biến A tuyệt đối
    for i in range(solver.num_ops):
        min_p = solver.min_p[i]
        for t in range(solver.est[i], solver.lst[i] + 1):
            s_var = solver.get_var('S', i, t)

            # 7a: Active theo thời gian máy nhanh nhất
            end_min_active = t + min_p
            for tau in range(t, end_min_active):
                solver.add_clause_smart([-s_var, solver.get_var('A', i, tau)])

            # 7b: Active thêm nếu dùng máy chậm hơn (chỉ sinh khi t hợp lệ)
            for mach, p in solver.ops[i]['machines']:
                if p > min_p:
                    max_start_m = solver.lst[i] + solver.min_p[i] - p
                    if t > max_start_m: continue

                    m_var = solver.get_var('M', i, mach)
                    end_active = t + p
                    for tau in range(end_min_active, end_active):
                        solver.add_clause_smart([-m_var, -s_var, solver.get_var('A', i, tau)])