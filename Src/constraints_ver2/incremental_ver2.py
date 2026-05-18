# def apply_incremental_ver2(solver, new_limit):
#     upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
#     if new_limit >= upper_bound:
#         return
#     for j_ids in solver.job_map:
#         if not j_ids:
#             continue
#         last_op_id = j_ids[-1]
#         op_data = solver.ops[last_op_id]
#         for mach, p in op_data['machines']:
#             m_var = solver.var_map.get(('M', last_op_id, mach))
#             if m_var is None:
#                 continue
#             t_end = new_limit + 1
#             t_start_blocked = t_end - p
#             x_var = solver.get_x_bounded(last_op_id, t_start_blocked)
#             solver.add_clause_smart([-m_var, solver.neg(x_var)])
#     solver.current_check_limit = new_limit


from constraints_ver2.mvcc import update_mvcc_incremental

def apply_incremental_ver2(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
    if new_limit >= upper_bound:
        return

    # Giữ nguyên logic original blocking của Model_9
    for j_ids in solver.job_map:
        if not j_ids:
            continue
        last_op_id = j_ids[-1]
        for mach, p in solver.ops[last_op_id]['machines']:
            m_var = solver.var_map.get(('M', last_op_id, mach))
            if m_var is None:
                continue
            t_start_blocked = new_limit + 1 - p
            x_var = solver.get_x_bounded(last_op_id, t_start_blocked)
            solver.add_clause_smart([-m_var, solver.neg(x_var)])

    # PHẦN THÊM MỚI TỪ MODEL_12: Kích hoạt MVCC update
    update_mvcc_incremental(solver, new_limit)

    solver.current_check_limit = new_limit