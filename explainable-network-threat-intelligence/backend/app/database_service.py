
from app.database import SessionLocal
from app.db_models import NetworkFlow, AttackPrediction


def save_predictions(flows, predictions):

    db = SessionLocal()

    try:
        for flow, result in zip(flows, predictions):

            
            network_flow = NetworkFlow(
                source_ip=flow.get("src_ip"),
                destination_ip=flow.get("dst_ip"),
                source_port=flow.get("src_port"),
                destination_port=flow.get("dst_port"),
                protocol=str(flow.get("protocol", "")),
                flow_duration=flow.get("flow_duration"),
                total_fwd_packets=flow.get("tot_fwd_pkts"),
                total_bwd_packets=flow.get("tot_bwd_pkts"),
                flow_bytes_per_second=flow.get("flow_byts_s"),
                flow_packets_per_second=flow.get("flow_pkts_s")
            )


            db.add(network_flow)
            db.flush()

            prediction = AttackPrediction(
                flow_id=network_flow.flow_id,
                prediction=result["prediction"],
                label=result["label"],
                confidence=result["confidence"],
                uncertainty=result["uncertainty"],
                status=result["status"]
            )

            db.add(prediction)

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
