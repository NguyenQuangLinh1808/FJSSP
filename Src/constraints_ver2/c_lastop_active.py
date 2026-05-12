from collections import defaultdict


def apply_lastop_active(solver):
    """
    Targeted UNSAT Proof: Chỉ tạo biến A (Active) và Overlap Constraint
    cho các LAST OP của mỗi job.
    Giúp rút ngắn chứng chỉ UNSAT ở các mốc thời gian cuối mà không gây quá tải CNF.
    """
    last_ops = [job_ids[-1] for job_ids in solver.job_map if job_ids]

    # ── Bước 1: Định nghĩa biến A CHỈ cho last ops ────────
    for op_id in last_ops:
        min_p = solver.min_p[op_id]

        for t in range(solver.est[op_id], solver.lst[op_id] + 1):
            s_var = solver.var_map.get(('S', op_id, t))
            if not s_var: continue

            # Base: Mặc định active trong [t, t + min_p - 1]
            for tau in range(t, t + min_p):
                a_var = solver.get_var('A', op_id, tau)
                solver.add_clause_smart([-s_var, a_var])

            # Extra: Active thêm nếu chọn máy chạy chậm hơn min_p
            for mach, p in solver.ops[op_id]['machines']:
                if (op_id, mach) in getattr(solver, 'killed_machines', set()):
                    continue
                if p <= min_p:
                    continue

                max_start_m = solver.lst[op_id] + min_p - p
                if t > max_start_m:
                    continue

                m_var = solver.var_map.get(('M', op_id, mach))
                if not m_var: continue

                for tau in range(t + min_p, t + p):
                    a_var = solver.get_var('A', op_id, tau)
                    solver.add_clause_smart([-m_var, -s_var, a_var])

    # ── Bước 2: Ràng buộc Overlap qua biến A cho Last Ops ────
    mach_to_last = defaultdict(list)
    for op_id in last_ops:
        for m, p in solver.ops[op_id]['machines']:
            if (op_id, m) not in getattr(solver, 'killed_machines', set()):
                mach_to_last[m].append((op_id, p))

    for mach, ops_on_m in mach_to_last.items():
        n = len(ops_on_m)
        for a in range(n):
            for b in range(a + 1, n):
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                if solver.lst[i] + p_i <= solver.est[j]: continue
                if solver.lst[j] + p_j <= solver.est[i]: continue

                m_var_i = solver.var_map.get(('M', i, mach))
                m_var_j = solver.var_map.get(('M', j, mach))
                if not m_var_i or not m_var_j: continue

                # Bỏ qua nếu có forced ordering hoặc capacity overflow
                # (Vì c6_c7_ver2 đã xử lý X/S constraint rồi)
                j_before_i = (solver.est[i] + p_i > solver.lst[j])
                i_before_j = (solver.est[j] + p_j > solver.lst[i])
                if j_before_i or i_before_j:
                    continue

                c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i
                if min(c_ij, c_ji) > solver.horizon:
                    continue

                # Chỉ gắn biến A cho unforced overlap (Mỏ neo VSIDS)
                start_tau = max(solver.est[i], solver.est[j])
                end_tau = min(solver.lst[i] + p_i, solver.lst[j] + p_j, solver.horizon + 1) - 1

                for tau in range(start_tau, end_tau + 1):
                    a_i = solver.var_map.get(('A', i, tau))
                    a_j = solver.var_map.get(('A', j, tau))
                    if a_i is not None and a_j is not None:
                        solver.add_clause_smart([-m_var_i, -m_var_j, -a_i, -a_j])