from services.risk import analyze_risk
from services.summary import generate_summaries
from fastapi import HTTPException

def compare_ipos(file_id_1: str, file_id_2: str):
    """Compare two IPO files on risk and summary metrics."""
    try:
        # --- Risk Analysis ---
        risk1 = analyze_risk(file_id_1)
        risk2 = analyze_risk(file_id_2)

        # --- Summaries ---
        sum1 = generate_summaries(file_id_1)
        sum2 = generate_summaries(file_id_2)

        # --- Prepare comparison dict ---
        result = {
            "ipo_1": {
                "file_id": file_id_1,
                "risk_score": risk1["risk_score"],
                "avg_negative": risk1["avg_negative"],
                "summary": sum1["summaries"],
                "top_negatives": risk1["top_negatives"],
            },
            "ipo_2": {
                "file_id": file_id_2,
                "risk_score": risk2["risk_score"],
                "avg_negative": risk2["avg_negative"],
                "summary": sum2["summaries"],
                "top_negatives": risk2["top_negatives"],
            },
            "comparison": {
                "higher_risk": (
                    file_id_1 if risk1["risk_score"] > risk2["risk_score"] else file_id_2
                ),
                "risk_gap": round(abs(risk1["risk_score"] - risk2["risk_score"]), 2),
            },
        }
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
