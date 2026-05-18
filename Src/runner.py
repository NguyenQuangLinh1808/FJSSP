# import os
# import time
# import csv
# from Src.io_utils import parse_brandimarte_file, load_result_from_file, save_result_to_file
# from validator import get_heuristic_bound, validate_solution
# from Src.core_solver import FJSSP_SAT
#
# TIMEOUT = 4800
#
#
# def upsert_and_sort_csv(csv_file_path, csv_headers, new_row):
#     """
#     Đảm bảo tính duy nhất (Unique) và thứ tự (Sorted) cho file CSV.
#     new_row: danh sách chứa thông tin của 1 dòng test (vd: ['mk01.txt', ...])
#     """
#     records = {}
#
#     # 1. Đọc dữ liệu cũ (nếu có) vào HashMap để dễ kiểm soát
#     if os.path.exists(csv_file_path):
#         with open(csv_file_path, 'r', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             try:
#                 next(reader)  # Bỏ qua header cũ
#             except StopIteration:
#                 pass
#             for row in reader:
#                 if row:  # Bỏ qua dòng rỗng
#                     records[row[0]] = row  # key là tên test (vd: 'mk01.txt')
#
#     # 2. Update/Upsert: Ghi đè test mới vào dict (Giải quyết triệt để lỗi trùng lặp)
#     records[new_row[0]] = [str(x) for x in new_row]
#
#     # 3. Sắp xếp lại theo key (mk01.txt -> mk02.txt...)
#     sorted_keys = sorted(records.keys())
#
#     # 4. Ghi đè toàn bộ file với thứ tự chuẩn
#     with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(csv_headers)
#         for k in sorted_keys:
#             writer.writerow(records[k])
#
# def run_brandimarte_tests(base_dir, test_indices=None, run_name="default_run"):
#     project_root = os.path.dirname(os.path.abspath(base_dir))
#     brandimarte_dir = os.path.join(project_root, 'brandimarte')
#     result_dir = os.path.join(project_root, 'Results', run_name)
#     json_dir = os.path.join(result_dir, 'json')
#
#     os.makedirs(json_dir, exist_ok=True)
#
#     os.path.join(result_dir, f'{run_name}_summary.csv')
#     csv_headers = ['Problem', 'Số job', 'số máy', 'Upper bound', 'Lower bound',
#                    'Number of clause', 'Number of variable', 'Makespan', 'Status', 'Runtime']
#
#     csv_file_path = os.path.join(result_dir, f'{run_name}_summary.csv')
#     os.path.exists(csv_file_path)
#
#     lb_path = os.path.join(project_root, 'LB_UB', 'LB.txt')
#     ub_path = os.path.join(project_root, 'LB_UB', 'UB.txt')
#
#     if not os.path.exists(lb_path) or not os.path.exists(ub_path):
#         print("Lỗi: Không tìm thấy file LB hoặc UB")
#         return
#
#     with open(lb_path, 'r') as f:
#         lbs = [int(x) for x in f.read().split()]
#     with open(ub_path, 'r') as f:
#         ubs = [int(x) for x in f.read().split()]
#
#     summary_records = []
#
#     print("=================================================================")
#     print(f"BẮT ĐẦU CHẠY ĐỢT: {run_name} (Timeout={TIMEOUT}s)")
#     print("=================================================================\n")
#
#     if test_indices is None:
#         test_indices = range(1, 16)
#
#     for i in test_indices:
#         test_name = f"mk{i:02d}.txt"
#         file_path = os.path.join(brandimarte_dir, test_name)
#         result_file_path = os.path.join(json_dir, f"{test_name}.json")
#
#         if not os.path.exists(file_path):
#             print(f">>> Lỗi: Không tìm thấy file {test_name} trong thư mục brandimarte.")
#             continue
#
#         lb, file_ub = lbs[i - 1], ubs[i - 1]
#         jobs, n_mach = parse_brandimarte_file(file_path)
#
#         real_feasible_bound = get_heuristic_bound(jobs, n_mach)
#         ub = min(file_ub, real_feasible_bound)
#
#         print(f"   [Pre-process] File UB: {file_ub} | Bound Thật (Greedy): {real_feasible_bound} -> Chốt Horizon: {ub}")
#
#         start_total_test = time.time()
#         num_jobs = len(jobs)
#         num_machines = n_mach
#
#         record = {
#             "test": test_name, "lb": lb, "ub": ub,
#             "status": "N/A", "valid": "N/A", "makespan": "N/A", "time": 0.0,
#             "note": ""
#         }
#
#         existing_result = load_result_from_file(result_file_path)
#
#         if existing_result:
#             status = existing_result.get('status', 'UNKNOWN')
#             elapsed = existing_result.get('time_seconds', 0)
#             schedule = existing_result.get('schedule', [])
#
#             if 'num_clauses' in existing_result and 'num_vars' in existing_result:
#                 num_clauses = existing_result['num_clauses']
#                 num_vars = existing_result['num_vars']
#             else:
#                 temp_solver = FJSSP_SAT(jobs, n_mach, ub)
#                 temp_solver.build_model()
#                 num_clauses = len(temp_solver.cnf.clauses)
#                 num_vars = temp_solver.var_count
#                 existing_result['num_clauses'] = num_clauses
#                 existing_result['num_vars'] = num_vars
#                 save_result_to_file(result_file_path, existing_result)
#
#             is_valid, msg = validate_solution(jobs, schedule)
#             valid_str = "OK" if is_valid else "FAIL"
#
#             # ĐÃ XÓA SỰ CHE GIẤU "Err"
#             mkspan_str = str(msg)
#
#             record["status"] = status
#             record["time"] = elapsed
#             record["note"] = "(Saved)"
#             record["valid"] = valid_str
#             record["makespan"] = mkspan_str
#
#             final_status = status
#             final_runtime = elapsed
#             final_makespan = msg if is_valid else -1
#
#             print(f">>> {test_name}: Đã có kết quả (Saved).")
#             if is_valid:
#                 print(f"   [Result] Status: {status:<8} | Makespan: {mkspan_str:<5} | Time: {elapsed:.2f}s")
#             else:
#                 print(f"   [FATAL ERROR] Lịch trình sai logic: {msg}")
#
#         else:
#             print(f">>> {test_name}: Đang chạy (LB={lb}, UB={ub})...")
#
#             solver = FJSSP_SAT(jobs, n_mach, ub)
#             solver.build_model()
#             build_time = time.time() - start_total_test
#             remaining_time = TIMEOUT - build_time
#
#             if remaining_time <= 0:
#                 status = "TIME_OUT"
#                 elapsed = build_time
#                 num_clauses = len(solver.cnf.clauses)
#                 num_vars = solver.var_count
#                 best_schedule = None
#             else:
#                 status, best_schedule, num_clauses, num_vars = solver.solve_optimal(lb, time_out=remaining_time)
#                 elapsed = time.time() - start_total_test
#
#             record["status"] = status
#             record["time"] = elapsed
#
#             final_status = status
#             final_runtime = elapsed
#
#             valid_str = "N/A"
#             mkspan_str = "N/A"
#
#             if best_schedule:
#                 is_valid, msg = validate_solution(jobs, best_schedule)
#                 valid_str = "OK" if is_valid else "FAIL"
#
#                 # ĐÃ XÓA SỰ CHE GIẤU "Err"
#                 mkspan_str = str(msg)
#
#                 final_makespan = msg if is_valid else -1
#             else:
#                 final_makespan = -1
#
#             record["valid"] = valid_str
#             record["makespan"] = mkspan_str
#
#             result_data = {
#                 "test_name": test_name,
#                 "lb": lb, "ub": ub,
#                 "status": status,
#                 "time_seconds": elapsed,
#                 "makespan": final_makespan,
#                 "schedule": best_schedule,
#                 "num_clauses": num_clauses,
#                 "num_vars": num_vars
#             }
#             save_result_to_file(result_file_path, result_data)
#
#             if is_valid:
#                 print(f"   [Result] Status: {status:<8} | Makespan: {mkspan_str:<5} | Time: {elapsed:.2f}s")
#             else:
#                 print(f"   [FATAL ERROR] Lịch trình sai logic: {msg}")
#
#         final_runtime = round(final_runtime, 2)
#
#         new_row = [
#             test_name, num_jobs, num_machines, ub, lb,
#             num_clauses, num_vars, final_makespan, final_status, final_runtime
#         ]
#         upsert_and_sort_csv(csv_file_path, csv_headers, new_row)
#
#         summary_records.append(record)
#         print("-" * 65)
#
#     print("\n\n")
#     print("=" * 95)
#     print(f"{'BẢNG TỔNG KẾT KẾT QUẢ':^95}")
#     print("=" * 95)
#     for r in summary_records:
#         # Giới hạn in lỗi ngắn gọn trong bảng tổng kết
#         short_msg = str(r['makespan'])[:20] + "..." if r['valid'] == "FAIL" else r['makespan']
#         print(
#             f"{r['test']:<8} | {r['lb']:<5} | {r['ub']:<5} | {r['status']:<8} | {r['valid']:<8} | {short_msg:<20} | {r['time']:.4f}     | {r['note']}")
#     print("-" * 95)
#     print(f"\n[INFO] Đã lưu bảng kết quả chi tiết tại: {csv_file_path}")

# import os
# import time
# import csv
# from Src.io_utils import parse_brandimarte_file, load_result_from_file, save_result_to_file
# from validator import get_heuristic_bound, validate_solution
# from Src.core_solver import FJSSP_SAT
#
# TIMEOUT = 4800
#
#
# def upsert_and_sort_csv(csv_file_path, csv_headers, new_row):
#     records = {}
#     if os.path.exists(csv_file_path):
#         with open(csv_file_path, 'r', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             try:
#                 next(reader)
#             except StopIteration:
#                 pass
#             for row in reader:
#                 if row:
#                     records[row[0]] = row
#
#     records[new_row[0]] = [str(x) for x in new_row]
#     sorted_keys = sorted(records.keys())
#
#     with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(csv_headers)
#         for k in sorted_keys:
#             writer.writerow(records[k])
#
#
# def run_brandimarte_tests(base_dir, test_indices=None, run_name="default_run", model_choice=3):
#     project_root = os.path.dirname(os.path.abspath(base_dir))
#     brandimarte_dir = os.path.join(project_root, 'brandimarte')
#
#     # THƯ MỤC GỐC CỦA ĐỢT CHẠY
#     result_dir = os.path.join(project_root, 'Results', run_name)
#     os.makedirs(result_dir, exist_ok=True)
#
#     # 1 MASTER CSV DUY NHẤT ĐỂ QUẢN LÝ TOÀN BỘ DỮ LIỆU
#     csv_file_path = os.path.join(result_dir, f"{run_name}_summary.csv")
#     csv_headers = ['Problem', 'Số job', 'số máy', 'Upper bound', 'Lower bound',
#                    'Number of clause', 'Number of variable', 'Makespan', 'Status', 'Runtime']
#
#     lb_path = os.path.join(project_root, 'LB_UB', 'LB.txt')
#     ub_path = os.path.join(project_root, 'LB_UB', 'UB.txt')
#
#     if not os.path.exists(lb_path) or not os.path.exists(ub_path):
#         print("Lỗi: Không tìm thấy file LB hoặc UB")
#         return
#
#     with open(lb_path, 'r') as f:
#         lbs = [int(x) for x in f.read().split()]
#     with open(ub_path, 'r') as f:
#         ubs = [int(x) for x in f.read().split()]
#
#     summary_records = []
#
#     model_names = {
#         1: "replace_active",
#         2: "replace_active_overlap",
#         3: "old_optimal",
#         4: "old_not_optimal"
#     }
#
#     print("=================================================================")
#     print(f"BẮT ĐẦU CHẠY ĐỢT: {run_name} | MÔ HÌNH: {model_names[model_choice]} | Timeout={TIMEOUT}s")
#     print("=================================================================\n")
#
#     if test_indices is None:
#         test_indices = range(1, 16)
#
#     for i in test_indices:
#         clean_test_name = f"mk{i:02d}"
#         original_test_name = f"{clean_test_name}.txt"
#         file_path = os.path.join(brandimarte_dir, original_test_name)
#
#         if not os.path.exists(file_path):
#             print(f">>> Lỗi: Không tìm thấy file {original_test_name} trong thư mục brandimarte.")
#             continue
#
#         lb, file_ub = lbs[i - 1], ubs[i - 1]
#
#         jobs, n_mach = parse_brandimarte_file(file_path)
#         real_feasible_bound = get_heuristic_bound(jobs, n_mach)
#         ub = min(file_ub, real_feasible_bound)
#
#         print(f"\n================ ĐANG XỬ LÝ TEST: {clean_test_name} ================")
#         print(f"   [Pre-process] File UB: {file_ub} | Bound Thật (Greedy): {real_feasible_bound} -> Chốt Horizon: {ub}")
#
#         num_jobs = len(jobs)
#         num_machines = n_mach
#
#         # GOM NHÓM DỮ LIỆU BẰNG THƯ MỤC TEST (VD: Results/Run_A/mk01/)
#         test_folder = os.path.join(result_dir, clean_test_name)
#         os.makedirs(test_folder, exist_ok=True)
#
#         for run_idx in range(1):
#             print(f"\n   ---> Chạy lần {run_idx}/3 cho {clean_test_name} (LB={lb}, UB={ub})...")
#
#             # ĐỊNH DANH FILE RÕ RÀNG: Không bao giờ bị ghi đè
#             # run_specific_name = f"{clean_test_name}_run{run_idx}"
#             run_specific_name = f"{clean_test_name}"
#             result_file_path = os.path.join(test_folder, f"{run_specific_name}.json")
#
#             start_total_test = time.time()
#
#             solver = FJSSP_SAT(jobs, n_mach, ub, model_choice=model_choice)
#             solver.build_model()
#             build_time = time.time() - start_total_test
#             remaining_time = TIMEOUT - build_time
#
#             if remaining_time <= 0:
#                 status = "TIME_OUT"
#                 elapsed = build_time
#                 num_clauses = len(solver.cnf.clauses)
#                 num_vars = solver.var_count
#                 best_schedule = None
#             else:
#                 # Core_solver sẽ tự động lấy 'run_specific_name' làm tên file log (trace_mk01_run1.log)
#                 # và ném thẳng vào thư mục test_folder (mk01/)
#                 status, best_schedule, num_clauses, num_vars = solver.solve_optimal(
#                     lb, time_out=remaining_time, test_name=run_specific_name, log_dir=test_folder
#                 )
#                 elapsed = time.time() - start_total_test
#
#             final_status = status
#             final_runtime = elapsed
#             valid_str = "N/A"
#             mkspan_str = "N/A"
#
#             if best_schedule:
#                 is_valid, msg = validate_solution(jobs, best_schedule)
#                 valid_str = "OK" if is_valid else "FAIL"
#                 mkspan_str = str(msg)
#                 final_makespan = msg if is_valid else -1
#             else:
#                 is_valid = False
#                 msg = "No schedule"
#                 final_makespan = -1
#
#             result_data = {
#                 "test_name": run_specific_name,
#                 "model_applied": model_names[model_choice],
#                 "run_index": run_idx,
#                 "lb": lb, "ub": ub,
#                 "status": status,
#                 "time_seconds": elapsed,
#                 "makespan": final_makespan,
#                 "schedule": best_schedule,
#                 "num_clauses": num_clauses,
#                 "num_vars": num_vars
#             }
#             save_result_to_file(result_file_path, result_data)
#
#             if is_valid:
#                 print(f"   [Result {run_idx}] Status: {status:<8} | Makespan: {mkspan_str:<5} | Time: {elapsed:.2f}s")
#             else:
#                 print(f"   [FATAL ERROR {run_idx}] Lịch trình sai logic: {msg}")
#
#             final_runtime = round(final_runtime, 2)
#
#             # GHI NỐI VÀO MASTER CSV
#             new_row = [
#                 run_specific_name, num_jobs, num_machines, ub, lb,
#                 num_clauses, num_vars, final_makespan, final_status, final_runtime
#             ]
#             upsert_and_sort_csv(csv_file_path, csv_headers, new_row)
#
#             record = {
#                 "test": run_specific_name, "lb": lb, "ub": ub,
#                 "status": status, "valid": valid_str, "makespan": mkspan_str, "time": elapsed,
#                 "note": ""
#             }
#             summary_records.append(record)
#
#         print("-" * 65)
#
#     print("\n\n")
#     print("=" * 95)
#     print(f"{'BẢNG TỔNG KẾT KẾT QUẢ TẤT CẢ CÁC VÒNG CHẠY':^95}")
#     print("=" * 95)
#     for r in summary_records:
#         short_msg = str(r['makespan'])[:20] + "..." if r['valid'] == "FAIL" else r['makespan']
#         print(
#             f"{r['test']:<15} | {r['lb']:<5} | {r['ub']:<5} | {r['status']:<8} | {r['valid']:<8} | {short_msg:<20} | {r['time']:.4f}     | {r['note']}")
#     print("-" * 95)

# import os
# import time
# import csv
# from io_utils import parse_fjssp_file, load_result_from_file, save_result_to_file
# from validator import get_heuristic_bound, validate_solution
# from core_solver import FJSSP_SAT
#
# TIMEOUT = 10
#
#
# def upsert_and_sort_csv(csv_file_path, csv_headers, new_row):
#     records = {}
#     if os.path.exists(csv_file_path):
#         with open(csv_file_path, 'r', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             try:
#                 next(reader)
#             except StopIteration:
#                 pass
#             for row in reader:
#                 if row:
#                     records[row[0]] = row
#
#     records[new_row[0]] = [str(x) for x in new_row]
#     sorted_keys = sorted(records.keys())
#
#     with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(csv_headers)
#         for k in sorted_keys:
#             writer.writerow(records[k])
#
#
# def run_benchmark_tests(base_dir, dataset_rel_path, test_indices=None, run_name="default_run", model_choice=3):
#     project_root = os.path.dirname(os.path.abspath(base_dir))
#     dataset_dir = os.path.join(project_root, dataset_rel_path)
#
#     # Thư mục gốc độc lập cho đợt chạy này (x, y, z hoặc model_1, v.v...)
#     result_dir = os.path.join(project_root, 'Results', dataset_rel_path, run_name)
#     os.makedirs(result_dir, exist_ok=True)
#
#     csv_file_path = os.path.join(result_dir, f"{run_name}_summary.csv")
#     csv_headers = ['Problem', 'Số job', 'số máy', 'Upper bound', 'Lower bound',
#                    'Number of clause', 'Number of variable', 'Makespan', 'Status', 'Runtime']
#
#     lb_path = os.path.join(project_root, 'LB_UB', dataset_rel_path, 'LB.txt')
#     ub_path = os.path.join(project_root, 'LB_UB', dataset_rel_path, 'UB.txt')
#
#     lbs, ubs = [], []
#     if os.path.exists(lb_path):
#         with open(lb_path, 'r') as f:
#             lbs = [int(x) for x in f.read().split()]
#     else:
#         print(f">>> CẢNH BÁO: Không tìm thấy {lb_path}. Lower Bound mặc định bị ép về 0.")
#
#     if os.path.exists(ub_path):
#         with open(ub_path, 'r') as f:
#             ubs = [int(x) for x in f.read().split()]
#     else:
#         print(f">>> CẢNH BÁO: Không tìm thấy {ub_path}. Upper Bound thả trôi vô cực.")
#
#     summary_records = []
#     applied_model_str = f"model_{model_choice}"
#
#     print("=================================================================")
#     print(f"BẮT ĐẦU CHẠY ĐỢT: {run_name} | TARGET: {dataset_rel_path} | MÔ HÌNH: {applied_model_str}")
#     print("=================================================================\n")
#
#     all_files = sorted(
#         [f for f in os.listdir(dataset_dir) if f.endswith('.txt') and os.path.isfile(os.path.join(dataset_dir, f))])
#
#     if not all_files:
#         print(f">>> Lỗi: Thư mục {dataset_dir} không chứa file .txt nào.")
#         return
#
#     if test_indices is None:
#         selected_indices = range(len(all_files))
#     else:
#         selected_indices = [i - 1 for i in test_indices if 0 < i <= len(all_files)]
#
#     for idx in selected_indices:
#         original_test_name = all_files[idx]
#         clean_test_name = os.path.splitext(original_test_name)[0]
#         file_path = os.path.join(dataset_dir, original_test_name)
#
#         lb = lbs[idx] if idx < len(lbs) else 0
#         file_ub = ubs[idx] if idx < len(ubs) else float('inf')
#
#         jobs, n_mach = parse_fjssp_file(file_path)
#
#         if not jobs:
#             print(f">>> BỎ QUA: File {original_test_name} hỏng hoặc rỗng.")
#             continue
#
#         real_feasible_bound = get_heuristic_bound(jobs, n_mach)
#         ub = min(file_ub, real_feasible_bound)
#
#         print(f"\n================ ĐANG XỬ LÝ TEST: {clean_test_name} ================")
#         print(f"   [Pre-process] File UB: {file_ub} | Bound Thật (Greedy): {real_feasible_bound} -> Chốt Horizon: {ub}")
#
#         num_jobs, num_machines = len(jobs), n_mach
#         test_folder = os.path.join(result_dir, clean_test_name)
#         os.makedirs(test_folder, exist_ok=True)
#
#         for run_idx in range(1):
#             print(f"\n   ---> Tiến hành giải {clean_test_name} (LB={lb}, UB={ub})...")
#
#             # Cấu trúc file nguyên thủy, không gắn thêm tiền tố rác
#             run_specific_name = f"{clean_test_name}"
#             result_file_path = os.path.join(test_folder, f"{run_specific_name}.json")
#
#             start_total_test = time.time()
#
#             solver = FJSSP_SAT(jobs, n_mach, ub, model_choice=model_choice)
#             solver.build_model()
#             build_time = time.time() - start_total_test
#             remaining_time = TIMEOUT - build_time
#
#             if remaining_time <= 0:
#                 status, elapsed, num_clauses, num_vars, best_schedule = "TIME_OUT", build_time, len(
#                     solver.cnf.clauses), solver.var_count, None
#             else:
#                 status, best_schedule, num_clauses, num_vars = solver.solve_optimal(
#                     lb, time_out=remaining_time, test_name=run_specific_name, log_dir=test_folder
#                 )
#                 elapsed = time.time() - start_total_test
#
#             final_status, final_runtime = status, elapsed
#
#             if best_schedule:
#                 is_valid, msg = validate_solution(jobs, best_schedule)
#                 valid_str, mkspan_str = ("OK", str(msg)) if is_valid else ("FAIL", str(msg))
#                 final_makespan = msg if is_valid else -1
#             else:
#                 is_valid, valid_str, mkspan_str, msg, final_makespan = False, "N/A", "N/A", "No schedule", -1
#
#             result_data = {
#                 "test_name": run_specific_name, "model_applied": applied_model_str,
#                 "run_index": run_idx, "lb": lb, "ub": ub, "status": status, "time_seconds": elapsed,
#                 "makespan": final_makespan, "schedule": best_schedule,
#                 "num_clauses": num_clauses, "num_vars": num_vars
#             }
#             save_result_to_file(result_file_path, result_data)
#
#             if is_valid:
#                 print(f"   [Kết quả] Status: {status:<8} | Makespan: {mkspan_str:<5} | Time: {elapsed:.2f}s")
#             else:
#                 print(f"   [LỖI NGHIÊM TRỌNG] Lịch trình sai logic: {msg}")
#
#             final_runtime = round(final_runtime, 2)
#
#             upsert_and_sort_csv(csv_file_path, csv_headers, [
#                 run_specific_name, num_jobs, num_machines, ub, lb,
#                 num_clauses, num_vars, final_makespan, final_status, final_runtime
#             ])
#
#             summary_records.append({
#                 "test": run_specific_name, "lb": lb, "ub": ub, "status": status,
#                 "valid": valid_str, "makespan": mkspan_str, "time": elapsed, "note": ""
#             })
#
#         print("-" * 65)
#         # --- BẮT BUỘC DỌN DẸP INSTANCE ---
#         if 'solver' in locals():
#             if solver.solver_instance:
#                 solver.solver_instance.delete()
#             del solver.cnf
#             del solver.var_map
#             del solver.ops
#             del solver
#
#         import gc
#         gc.collect()
#
#     print("\n\n" + "=" * 95)
#     print(f"{'BẢNG TỔNG KẾT KẾT QUẢ':^95}")
#     print("=" * 95)
#     for r in summary_records:
#         short_msg = str(r['makespan'])[:20] + "..." if r['valid'] == "FAIL" else r['makespan']
#         print(
#             f"{r['test']:<20} | {r['lb']:<5} | {r['ub']:<5} | {r['status']:<8} | {r['valid']:<8} | {short_msg:<20} | {r['time']:.4f}")
#     print("-" * 95)

import os
import time
import csv
import sys
import subprocess
from io_utils import parse_fjssp_file, load_result_from_file, save_result_to_file
from validator import get_heuristic_bound, validate_solution

TIMEOUT = 10800

def rescue_data_from_log(log_filepath):
    if not os.path.exists(log_filepath):
        return -1, "HARD_TIMEOUT", 0, 0

    best_mk = -1
    final_status = "UNKNOWN"
    clauses = 0
    vars_cnt = 0

    with open(log_filepath, 'r', encoding='utf-8') as file:
        for line in file:
            if "Found Real Makespan:" in line:
                try:
                    val = int(line.split(":")[1].strip())
                    if best_mk == -1 or val < best_mk:
                        best_mk = val
                except ValueError:
                    pass
            elif "FINAL STATUS:" in line:
                final_status = line.split(":")[1].strip()
            elif "Số mệnh đề =" in line:
                try:
                    parts = line.split("|")
                    vars_cnt = int(parts[1].split("=")[1].strip())
                    clauses = int(parts[2].split("=")[1].strip())
                except Exception:
                    pass

    if final_status == "UNKNOWN":
        final_status = "FEASIBLE" if best_mk != -1 else "TIME_OUT"

    return best_mk, final_status, clauses, vars_cnt


def upsert_and_sort_csv(csv_file_path, csv_headers, new_row):
    records = {}
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)
            except StopIteration:
                pass
            for row in reader:
                if row:
                    records[row[0]] = row

    records[new_row[0]] = [str(x) for x in new_row]
    sorted_keys = sorted(records.keys())

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for k in sorted_keys:
            writer.writerow(records[k])


def run_benchmark_tests(base_dir, dataset_rel_path, test_indices=None, run_name="default_run", model_choice=3):
    project_root = os.path.dirname(os.path.abspath(base_dir))
    dataset_dir = os.path.join(project_root, dataset_rel_path)

    # Thư mục gốc độc lập cho đợt chạy này (x, y, z hoặc model_1, v.v...)
    result_dir = os.path.join(project_root, 'Results', dataset_rel_path, run_name)
    os.makedirs(result_dir, exist_ok=True)

    csv_file_path = os.path.join(result_dir, f"{run_name}_summary.csv")
    csv_headers = ['Problem', 'Số job', 'số máy', 'Upper bound', 'Lower bound',
                   'Number of clause', 'Number of variable', 'Makespan', 'Status', 'Runtime']

    lb_path = os.path.join(project_root, 'LB_UB', dataset_rel_path, 'LB.txt')
    ub_path = os.path.join(project_root, 'LB_UB', dataset_rel_path, 'UB.txt')

    lbs, ubs = [], []
    if os.path.exists(lb_path):
        with open(lb_path, 'r') as f:
            lbs = [int(x) for x in f.read().split()]
    else:
        print(f">>> CẢNH BÁO: Không tìm thấy {lb_path}. Lower Bound mặc định bị ép về 0.")

    if os.path.exists(ub_path):
        with open(ub_path, 'r') as f:
            ubs = [int(x) for x in f.read().split()]
    else:
        print(f">>> CẢNH BÁO: Không tìm thấy {ub_path}. Upper Bound thả trôi vô cực.")

    summary_records = []
    applied_model_str = f"model_{model_choice}"

    print("=================================================================")
    print(f"BẮT ĐẦU CHẠY ĐỢT: {run_name} | TARGET: {dataset_rel_path} | MÔ HÌNH: {applied_model_str}")
    print("=================================================================\n")

    all_files = sorted(
        [f for f in os.listdir(dataset_dir) if f.endswith('.txt') and os.path.isfile(os.path.join(dataset_dir, f))])

    if not all_files:
        print(f">>> Lỗi: Thư mục {dataset_dir} không chứa file .txt nào.")
        return

    if test_indices is None:
        selected_indices = range(len(all_files))
    else:
        selected_indices = [i - 1 for i in test_indices if 0 < i <= len(all_files)]

    for idx in selected_indices:
        original_test_name = all_files[idx]
        clean_test_name = os.path.splitext(original_test_name)[0]
        file_path = os.path.join(dataset_dir, original_test_name)

        lb = lbs[idx] if idx < len(lbs) else 0
        file_ub = ubs[idx] if idx < len(ubs) else float('inf')

        jobs, n_mach = parse_fjssp_file(file_path)

        if not jobs:
            print(f">>> BỎ QUA: File {original_test_name} hỏng hoặc rỗng.")
            continue

        real_feasible_bound = get_heuristic_bound(jobs, n_mach)
        ub = min(file_ub, real_feasible_bound)

        print(f"\n================ ĐANG XỬ LÝ TEST: {clean_test_name} ================")
        print(f"   [Pre-process] File UB: {file_ub} | Bound Thật (Greedy): {real_feasible_bound} -> Chốt Horizon: {ub}")

        num_jobs, num_machines = len(jobs), n_mach
        test_folder = os.path.join(result_dir, clean_test_name)
        os.makedirs(test_folder, exist_ok=True)

        for run_idx in range(1):
            print(
                f"\n   ---> Tiến hành giải {clean_test_name} (LB={lb}, UB={ub}) với Timeout Hệ điều hành = {TIMEOUT}s...")

            # Cấu trúc file nguyên thủy, không gắn thêm tiền tố rác
            run_specific_name = f"{clean_test_name}"
            result_file_path = os.path.join(test_folder, f"{run_specific_name}.json")
            log_file_path = os.path.join(test_folder, f"trace_{run_specific_name}.log")

            start_total_test = time.time()

            # Chuẩn bị lệnh gọi hệ điều hành tới solve_worker.py
            cmd = [
                sys.executable,
                os.path.join(base_dir, "solve_worker.py"),
                file_path, str(lb), str(ub), str(model_choice),
                run_specific_name, test_folder, result_file_path
            ]

            try:
                # RUNNER CHỜ WORKER CHẠY. NẾU QUÁ GIỜ, HỆ ĐIỀU HÀNH SẼ CHÉM WORKER.
                process_result = subprocess.run(cmd, timeout=TIMEOUT, capture_output=True, text=True)
                elapsed = time.time() - start_total_test

                if process_result.returncode == 0:
                    # Worker hoàn thành bình thường, load JSON nó vừa tạo ra
                    existing_result = load_result_from_file(result_file_path) or {}
                    final_status = existing_result.get("status", "ERROR")
                    final_makespan = existing_result.get("makespan", -1)
                    num_clauses = existing_result.get("num_clauses", 0)
                    num_vars = existing_result.get("num_vars", 0)

                    valid_str = "OK" if final_makespan != -1 else "FAIL"
                    mkspan_str = str(final_makespan) if final_makespan != -1 else "N/A"

                else:
                    # Worker bị crash do lỗi code nội bộ hoặc hết RAM
                    final_status = f"CRASH ({process_result.returncode})"
                    final_makespan, _, num_clauses, num_vars = rescue_data_from_log(log_file_path)
                    valid_str = "N/A"
                    mkspan_str = str(final_makespan) if final_makespan != -1 else "N/A"
                    print(f"   [FATAL] Tiến trình Worker sập. Lỗi stderr: {process_result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                # LƯỠI MÁY CHÉM OS ĐÃ GIÁNG XUỐNG
                elapsed = time.time() - start_total_test
                print(f"   [CẢNH BÁO] Vượt quá {TIMEOUT}s. Giải phóng RAM.")

                # Cứu hộ kết quả cuối cùng từ Log
                final_makespan, final_status, num_clauses, num_vars = rescue_data_from_log(log_file_path)
                valid_str = "OK (Rescued)" if final_makespan != -1 else "FAIL"
                mkspan_str = str(final_makespan) if final_makespan != -1 else "FAIL"

            print(f"   [Kết quả] Status: {final_status:<10} | Makespan: {mkspan_str:<5} | Time: {elapsed:.2f}s")

            final_runtime = round(elapsed, 2)

            upsert_and_sort_csv(csv_file_path, csv_headers, [
                run_specific_name, num_jobs, num_machines, ub, lb,
                num_clauses, num_vars, final_makespan, final_status, final_runtime
            ])

            summary_records.append({
                "test": run_specific_name, "lb": lb, "ub": ub, "status": final_status,
                "valid": valid_str, "makespan": mkspan_str, "time": elapsed, "note": ""
            })

        print("-" * 65)
        # Giờ đây tiến trình phụ đã chết hẳn, RAM tự động được OS thu hồi.
        # Không cần dùng gc.collect() chắp vá trong python nội bộ nữa.

    print("\n\n" + "=" * 95)
    print(f"{'BẢNG TỔNG KẾT KẾT QUẢ':^95}")
    print("=" * 95)
    for r in summary_records:
        short_msg = str(r['makespan'])[:20] + "..." if r['valid'] == "FAIL" else r['makespan']
        print(
            f"{r['test']:<20} | {r['lb']:<5} | {r['ub']:<5} | {r['status']:<15} | {r['valid']:<12} | {short_msg:<15} | {r['time']:.4f}")
    print("-" * 95)