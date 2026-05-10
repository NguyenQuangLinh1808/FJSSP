from collections import defaultdict


def apply_c6_c7_v3(solver):
    """
    Hybrid overlap constraint — tự chứa hoàn toàn, không phụ thuộc file cũ.

    Chiến lược:
      - A variable (định nghĩa inline, không import c6.py)
          → compact hơn X/S khi pair không có forced ordering
          → 1 clause per active time slot, cover cả hai chiều
      - X/S ordering (cho forced pair)
          → nhỏ hơn A khi thứ tự đã xác định (bỏ được 1 chiều)
      - 2-literal exclusion khi conflict/capacity vượt horizon
      - Không dùng SM variable → ít biến phụ, VSIDS quality tốt hơn

    Thứ tự quan trọng: A vars phải được tạo TRƯỚC khi sinh overlap clause.
    File này làm cả hai bước trong một hàm, đảm bảo thứ tự đúng.
    """

    # ══════════════════════════════════════════════════════════════════
    # BƯỚC 1: Định nghĩa A variable (logic C6 — inline)
    # A_{i,τ} = True nếu op i đang chạy tại time slot τ
    #
    # Implication (không phải biconditional):
    #   S_{i,t} → A_{i,τ}  với τ ∈ [t, t+min_p-1]           (base: máy nhanh nhất)
    #   M_{i,m} ∧ S_{i,t} → A_{i,τ} với τ ∈ [t+min_p, t+p-1] (extra: máy chậm hơn)
    # ══════════════════════════════════════════════════════════════════
    for i in range(solver.num_ops):
        min_p = solver.min_p[i]

        for t in range(solver.est[i], solver.lst[i] + 1):
            s_var = solver.get_var('S', i, t)

            # Base: active tối thiểu [t, t+min_p-1] — không cần kẹp biến M
            for tau in range(t, t + min_p):
                solver.add_clause_smart([-s_var, solver.get_var('A', i, tau)])

            # Extra: active thêm cho từng máy chậm hơn min_p
            for mach, p in solver.ops[i]['machines']:
                if p <= min_p:
                    continue  # Đã xử lý ở base case
                # Chỉ sinh khi t còn hợp lệ với máy chậm này
                max_start_m = solver.lst[i] + min_p - p
                if t > max_start_m:
                    continue
                m_var = solver.get_var('M', i, mach)
                for tau in range(t + min_p, t + p):
                    solver.add_clause_smart([-m_var, -s_var, solver.get_var('A', i, tau)])

    # ══════════════════════════════════════════════════════════════════
    # BƯỚC 2: Overlap constraint (logic C7 — inline với forced ordering opt)
    # ══════════════════════════════════════════════════════════════════
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

                # Bỏ qua cặp cùng job
                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                # ── Interval check ──────────────────────────────────
                # Nếu active window không giao nhau → không bao giờ conflict
                if solver.lst[i] + p_i <= solver.est[j]:
                    continue
                if solver.lst[j] + p_j <= solver.est[i]:
                    continue

                m_var_i = solver.get_var('M', i, mach)
                m_var_j = solver.get_var('M', j, mach)

                # ── Forced ordering detection ───────────────────────
                # EST[i] + p_i > LST[j]: i không thể kết thúc trước LST[j]
                # → nếu cùng máy mach, j PHẢI chạy trước i
                j_before_i = (solver.est[i] + p_i > solver.lst[j])
                i_before_j = (solver.est[j] + p_j > solver.lst[i])

                # ── Conflict: cả hai phải trước nhau → loại ────────
                if j_before_i and i_before_j:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                # ── Capacity check ──────────────────────────────────
                # Ngay cả sắp xếp tối ưu vẫn vượt horizon
                c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i
                if min(c_ij, c_ji) > solver.horizon:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                # ── Forced ordering: X/S approach ───────────────────
                # Khi j_before_i, active period của i và j KHÔNG BAO GIỜ
                # overlap trên máy này → bỏ hoàn toàn A-variable clause,
                # thay bằng ordering constraint (ít clause hơn)
                if j_before_i:
                    # CSLB: nếu cùng máy mach, i phải bắt đầu ≥ EST[j]+p_j
                    solver.add_clause_smart([
                        -m_var_i, -m_var_j,
                        solver.get_x_bounded(i, solver.est[j] + p_j)
                    ])
                    # Ordering: S_{j,t} → X_{i, t+p_j}
                    # Với mọi start time của j, i phải bắt đầu sau khi j xong
                    for t in range(solver.est[j], solver.lst[j] + 1):
                        solver.add_clause_smart([
                            -m_var_i, -m_var_j,
                            -solver.get_var('S', j, t),
                            solver.get_x_bounded(i, t + p_j)
                        ])
                    continue

                elif i_before_j:
                    # Đối xứng: i phải chạy trước j
                    solver.add_clause_smart([
                        -m_var_i, -m_var_j,
                        solver.get_x_bounded(j, solver.est[i] + p_i)
                    ])
                    for t in range(solver.est[i], solver.lst[i] + 1):
                        solver.add_clause_smart([
                            -m_var_i, -m_var_j,
                            -solver.get_var('S', i, t),
                            solver.get_x_bounded(j, t + p_i)
                        ])
                    continue

                # ── Unforced ordering: A-variable approach ──────────
                # Thứ tự chưa xác định → dùng A variable để encode compact
                # ONE clause per active time slot τ:
                #   [¬M_i, ¬M_j, ¬A_{i,τ}, ¬A_{j,τ}]
                # Cover CẢ HAI chiều (i trước j hoặc j trước i) trong 1 clause
                # → compact hơn ~2× so với X/S approach
                start_tau = max(solver.est[i], solver.est[j])
                end_tau   = min(
                    solver.lst[i] + p_i,
                    solver.lst[j] + p_j,
                    solver.horizon + 1
                ) - 1

                if start_tau > end_tau:
                    continue

                for tau in range(start_tau, end_tau + 1):
                    # Dùng var_map.get thay vì get_var:
                    # Nếu A_{i,tau} = None → C6 không tạo nó → i không thể
                    # active tại tau trên máy này (do C4 prohibit) → tautology → skip đúng
                    a_i = solver.var_map.get(('A', i, tau))
                    a_j = solver.var_map.get(('A', j, tau))
                    if a_i is not None and a_j is not None:
                        solver.add_clause_smart([-m_var_i, -m_var_j, -a_i, -a_j])