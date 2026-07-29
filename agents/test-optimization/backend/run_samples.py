import json
import urllib.request


def post(path: str):
    req = urllib.request.Request(f"http://127.0.0.1:8001{path}", method="POST")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


for name in ("low_risk", "high_risk"):
    data = post(f"/api/v1/optimize/sample/{name}")
    print("=" * 72)
    print(f"SAMPLE: {name}")
    print("=" * 72)
    print(
        json.dumps(
            {
                "id": data["id"],
                "lot_id": data["lot_id"],
                "device": data["device"],
                "summary": data["summary"],
                "risk_level": data["risk_level"],
                "risk_score": data["risk_score"],
                "confidence": data["confidence"],
                "recommended_strategy": data["recommended_strategy"],
                "adaptive_testing": data["adaptive_testing"]["recommendation"],
                "flow_mode": data["adaptive_testing"]["flow_mode"],
                "test_stop": data["test_stop"]["recommendation"],
                "estimated_time_reduction": data["estimated_time_reduction"],
                "estimated_cost_reduction": data["estimated_cost_reduction"],
                "expected_yield_improvement": data["expected_yield_improvement"],
                "business_impact": data["business_impact"],
                "top_yield": [x["action"] for x in data["yield_recommendations"][:2]],
                "top_cost": [x["action"] for x in data["cost_recommendations"][:2]],
                "engine": data["engine"],
            },
            indent=2,
        )
    )
    print()
