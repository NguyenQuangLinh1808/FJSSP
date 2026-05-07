import sys
import os
import json
import time
from core_solver import FJSSP_SAT
from io_utils import parse_fjssp_file, save_result_to_file
from validator import validate_solution


def main():
    if len(sys.argv) < 8:
        print(
            "Usage: python solve_worker.py <file_path> <lb> <ub> <model_choice> <test_name> <log_dir> <result_json_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    lb = int(sys.argv[2])
    ub = int(sys.argv[3])
    model_choice = int(sys.argv[4])
    test_name = sys.argv[5]
    log_dir = sys.argv[6]
    result_json_path = sys.argv[7]

    jobs, n_mach = parse_fjssp_file(file_path)
    if not jobs:
        sys.exit(2)  # Code 2: File lỗi

    start_time = time.time()

    solver = FJSSP_SAT(jobs, n_mach, ub, model_choice=model_choice)
    solver.build_model()
    build_time = time.time() - start_time

    # Truyền timeout cực lớn (vd: 10 ngày) vì Runner sẽ ngắt tiến trình từ bên ngoài
    status, best_schedule, num_clauses, num_vars = solver.solve_optimal(
        lb, time_out=999999, test_name=test_name, log_dir=log_dir
    )

    elapsed = time.time() - start_time

    final_makespan = -1
    if best_schedule:
        is_valid, msg = validate_solution(jobs, best_schedule)
        if is_valid:
            final_makespan = msg

    result_data = {
        "test_name": test_name,
        "model_applied": f"model_{model_choice}",
        "lb": lb, "ub": ub,
        "status": status,
        "time_seconds": elapsed,
        "makespan": final_makespan,
        "num_clauses": num_clauses,
        "num_vars": num_vars
    }
    save_result_to_file(result_json_path, result_data)
    sys.exit(0)  # Code 0: Hoàn thành bình thường


if __name__ == "__main__":
    main()