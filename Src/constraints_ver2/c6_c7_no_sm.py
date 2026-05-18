from collections import defaultdict

def apply_c6_c7_no_sm(solver):
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        n = len(ops_on_m)
        for a in range(n):
            for b in range(a + 1, n):
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue
                if solver.lst[i] + p_i <= solver.est[j]:
                    continue
                if solver.lst[j] + p_j <= solver.est[i]:
                    continue

                m_var_i = solver.get_var('M', i, mach)
                m_var_j = solver.get_var('M', j, mach)

                j_before_i = (solver.est[i] + p_i > solver.lst[j])
                i_before_j = (solver.est[j] + p_j > solver.lst[i])

                if j_before_i and i_before_j:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i
                if min(c_ij, c_ji) > solver.horizon:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                # ── CSLB CHUẨN (DẤU CỘNG) ──────────────────────────────
                # Nếu j chạy trước i, thì i BẮT BUỘC phải bắt đầu từ (EST_j + p_j) trở đi.
                # Do đó X tại thời điểm đó phải là TRUE (Literal mang dấu dương)
                if j_before_i:
                    solver.add_clause_smart([
                        -m_var_i, -m_var_j,
                        solver.get_x_bounded(i, solver.est[j] + p_j)
                    ])
                elif i_before_j:
                    solver.add_clause_smart([
                        -m_var_i, -m_var_j,
                        solver.get_x_bounded(j, solver.est[i] + p_i)
                    ])
                else:
                    solver.add_clause_smart([
                        -m_var_i, -m_var_j,
                        solver.get_x_bounded(i, solver.est[j] + p_j),
                        solver.get_x_bounded(j, solver.est[i] + p_i)
                    ])

                if j_before_i:
                    directions = [(i, j, p_i, p_j, False, True), (j, i, p_j, p_i, True, False)]
                elif i_before_j:
                    directions = [(i, j, p_i, p_j, True, False), (j, i, p_j, p_i, False, True)]
                else:
                    directions = [(i, j, p_i, p_j, False, False), (j, i, p_j, p_i, False, False)]

                # ── OVERLAP CHUẨN (DẤU TRỪ CHO LEFT, CỘNG CHO RIGHT) ────
                for (anchor, other, p_a, p_o, drop_left, drop_right) in directions:
                    est_o, lst_o = solver.est[other], solver.lst[other]
                    for t in range(solver.est[anchor], solver.lst[anchor] + 1):
                        t_left  = t - p_o + 1
                        t_right = t + p_a

                        if not drop_left  and t_left  > lst_o: continue
                        if not drop_right and t_right <= est_o: continue

                        clause = [-solver.get_var('S', anchor, t), -m_var_i, -m_var_j]

                        # Để KHÔNG đè nhau:
                        # 1. Other chạy xong trước: S_other <= t - p_o -> X_left = FALSE -> Thêm -X
                        # 2. Other chạy sau: S_other >= t + p_a -> X_right = TRUE -> Thêm +X
                        if not drop_left  and t_left  > est_o:
                            clause.append(-solver.get_x_bounded(other, t_left))
                        if not drop_right and t_right <= lst_o:
                            clause.append(solver.get_x_bounded(other, t_right))

                        solver.add_clause_smart(clause)