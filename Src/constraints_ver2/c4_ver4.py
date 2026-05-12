def apply_c4_ver4(solver):
    """
    Precedence Constraint (C4) - Bản Tối ưu O(1) Late-start Blocking
    """
    for j_ids in solver.job_map:
        for k in range(len(j_ids) - 1):
            i = j_ids[k]
            j = j_ids[k + 1]

            # 1. Base case: Mối quan hệ dựa trên min_p (Máy nhanh nhất)
            for t in range(solver.est[i], solver.lst[i] + 1):
                s_var = solver.var_map.get(('S', i, t))
                if s_var:
                    x_target = solver.get_x_bounded(j, t + solver.min_p[i])
                    solver.add_clause_smart([-s_var, x_target])

            # 2. Differential case: Các máy chậm hơn min_p
            machine_vars = []
            for m, p_m in solver.ops[i]['machines']:
                if (i, m) in getattr(solver, 'killed_machines', set()):
                    continue
                if p_m > solver.min_p[i]:
                    m_var = solver.var_map.get(('M', i, m))
                    if m_var:
                        machine_vars.append((m_var, p_m))

            for m_var, p_m in machine_vars:
                max_start_m = solver.lst[i] - (p_m - solver.min_p[i])

                # [ĐÒN CHÍ MẠNG O(1)] Dùng tính đơn điệu của X để chặt đuôi thời gian
                if max_start_m < solver.lst[i]:
                    x_bound = solver.get_x_bounded(i, max_start_m + 1)
                    solver.add_clause_smart([-m_var, solver.neg(x_bound)])

                # Chỉ ánh xạ độ trễ S -> X cho vùng thời gian khả thi thực sự
                for t in range(solver.est[i], max_start_m + 1):
                    s_var = solver.var_map.get(('S', i, t))
                    if s_var:
                        x_target = solver.get_x_bounded(j, t + p_m)
                        solver.add_clause_smart([-m_var, -s_var, x_target])