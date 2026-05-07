# def apply_incremental(solver, new_limit):
#     upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
#
#     # Nếu new_limit không hề nhỏ hơn giới hạn cũ, không có gì để chặn.
#     if new_limit >= upper_bound:
#         return
#
#     # Quét qua toàn bộ các operation
#     for i in range(solver.num_ops):
#         # Chỉ chặn các mốc thời gian vọt xà: từ new_limit + 1 đến upper_bound
#         for t in range(new_limit, upper_bound + 1):
#             # KHÔNG dùng get_var (sẽ sinh biến mới). Phải dùng var_map.get để tìm biến đã tồn tại.
#             a_var = solver.var_map.get(('A', i, t))
#
#             # Rút gọn không gian: Chỉ thêm constraint nếu biến A này thực sự tồn tại
#             if a_var is not None:
#                 # Bơm thẳng mệnh đề âm (Unary Clause) vào Solver
#                 solver.add_clause_smart([-a_var])
#
#     # Cập nhật lại mốc giới hạn mới để chuẩn bị cho lần siết tiếp theo
#     solver.current_check_limit = new_limit

def apply_incremental(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)

    # Nếu new_limit không hề nhỏ hơn giới hạn cũ, không có gì để chặn.
    if new_limit >= upper_bound:
        return

    # Chỉ truy xuất operation cuối cùng của mỗi job thay vì quét mù quáng toàn bộ
    for job_ops in solver.job_map:
        if not job_ops:
            continue

        last_op_id = job_ops[-1]  # Xác định mục tiêu thực sự quyết định Makespan

        # Chỉ chặn các mốc thời gian vọt xà: từ new_limit + 1 đến upper_bound
        for t in range(new_limit, upper_bound + 1):
            # Tìm biến A của đúng operation cuối cùng này
            a_var = solver.var_map.get(('A', last_op_id, t))

            # Rút gọn không gian: Chỉ thêm constraint nếu biến A này thực sự tồn tại
            if a_var is not None:
                # Bơm thẳng mệnh đề âm (Unary Clause) vào Solver
                solver.add_clause_smart([-a_var])

    # Cập nhật lại mốc giới hạn mới để chuẩn bị cho lần siết tiếp theo
    solver.current_check_limit = new_limit