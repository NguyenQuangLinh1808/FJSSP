from collections import defaultdict

def apply_c7_old(solver):
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, _ in solver.ops[i]['machines']:
            mach_to_ops[m].append(i)

    for mach, ops in mach_to_ops.items():
        n_ops = len(ops)
        for idx1 in range(n_ops):
            for idx2 in range(idx1 + 1, n_ops):
                i, j = ops[idx1], ops[idx2]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                m_var_i = solver.get_var('M', i, mach)
                m_var_j = solver.get_var('M', j, mach)

                start_chk = max(solver.est[i], solver.est[j])
                max_p_i = dict(solver.ops[i]['machines'])[mach]
                max_p_j = dict(solver.ops[j]['machines'])[mach]
                end_chk = min(solver.horizon - 1, solver.lst[i] + max_p_i - 1, solver.lst[j] + max_p_j - 1)

                if start_chk > end_chk:
                    continue

                # if start_chk >= end_chk:
                #     continue

                for t in range(start_chk, end_chk + 1):
                    # key_i = ('A', i, t)
                    # key_j = ('A', j, t)
                    #
                    # if key_i not in solver.var_map or key_j not in solver.var_map:
                    #     continue

                    # # Truy xuất an toàn, KHÔNG đẻ thêm biến
                    # a_i = solver.var_map[key_i]
                    # a_j = solver.var_map[key_j]

                    a_i = solver.get_var('A', i, t)
                    a_j = solver.get_var('A', j, t)

                    solver.add_clause_smart([-m_var_i, -m_var_j, -a_i, -a_j])