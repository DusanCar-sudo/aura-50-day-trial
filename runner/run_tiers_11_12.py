import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT / "runner"))

import run
import recorder

def main():
    session_number = 1
    zero_memory = False
    
    # Load questions for Tiers 11 and 12
    questions = []
    for tier in [11, 12]:
        questions.extend(run.load_questions(tier=tier))
        
    print(f"Running {len(questions)} questions for session {session_number} [Tiers 11, 12]...")
    
    results = {
        "session": session_number,
        "model": run.MODEL,
        "zero_memory": zero_memory,
        "timestamp": datetime.utcnow().isoformat(),
        "questions": [],
    }
    
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        res = run.run_question(q, zero_memory)
        results["questions"].append(res)
        verdict = res["score"]["verdict"]
        print(f"  Result: {verdict} in {res['elapsed_seconds']}s")
        
    out_file = recorder.save_session(results)
    print(f"Saved results to {out_file}")
    
if __name__ == "__main__":
    main()
