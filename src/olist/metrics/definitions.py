from dataclasses import asdict, dataclass
import pandas as pd


@dataclass(frozen=True)
class Metric:
    metric_id: str
    name: str
    definition: str
    formula: str
    exclusions: str
    assumption: str
    unit: str = "number"
    source: str = "gold.fact_orders"
    grain: str = "One accepted order"
    owner: str = "Operations Analytics Owner"


METRICS = [
    Metric("total_orders", "Total Orders", "Accepted orders in selected purchase period", "count(order_id)", "Quarantined orders and missing accepted customer", "Historical purchase cohorts"),
    Metric("delivered_orders", "Delivered Orders", "Accepted orders with delivered status", "sum(is_delivered)", "Other statuses", "Final source status"),
    Metric("cancelled_orders", "Cancelled Orders", "Accepted orders with canceled status", "sum(is_cancelled)", "Other statuses", "Final source status"),
    Metric("gmv", "Delivered Item GMV", "Accepted item price on delivered orders in BRL", "sum(item_gmv) where is_delivered", "Freight, canceled, unavailable, quarantined items", "GMV is merchandise value, not recognized revenue", "BRL"),
    Metric("freight", "Delivered Freight", "Accepted item freight on delivered orders", "sum(freight_value) where is_delivered", "Other statuses", "Freight is separate from merchandise GMV", "BRL"),
    Metric("aov", "Average Delivered Order Value", "Delivered item GMV per delivered order with accepted items", "delivered GMV / delivered orders with item_count > 0", "Delivered orders without accepted items", "No accounting revenue claim", "BRL"),
    Metric("on_time_rate", "On-Time Delivery Rate", "Eligible deliveries on or before estimated calendar day", "100 * count(eligible and not late) / count(eligible)", "Non-delivered or missing delivery/estimate", "Date-level deadline; source timezone unspecified", "%"),
    Metric("late_rate", "Late Delivery Rate", "Eligible deliveries after estimated calendar day", "100 * count(eligible and late) / count(eligible)", "Non-eligible deliveries", "Historical outcome, not live backlog", "%"),
    Metric("delivery_days", "Average Delivery Time", "Mean elapsed days purchase to delivery", "avg(nonnegative delivery_days)", "Non-delivered or negative intervals", "Elapsed days, not business days", "days"),
    Metric("delay_days", "Average Late Delivery Delay", "Mean positive date-level delay among late deliveries", "avg(delay_days) where is_late", "On-time and non-eligible", "Calendar days", "days"),
    Metric("review_score", "Average Latest Review Score", "Mean latest answered accepted review per order", "avg(review_score)", "No accepted review", "Latest answer then review_id tie-breaker", "score"),
    Metric("negative_review_rate", "Negative Review Rate", "Latest accepted reviews rated 1 or 2", "100 * count(review_score <= 2) / count(nonnull review_score)", "No review", "One latest review per order", "%"),
    Metric("repeat_customer_rate", "Repeat Customer Rate", "Persistent customers with multiple accepted orders in selection", "100 * customers with >1 order / distinct customer_unique_id", "Missing persistent identity", "Selection-dependent; customer_id is not persistent", "%"),
]


def definitions_frame():
    return pd.DataFrame([asdict(m) for m in METRICS])


def divide(n, d):
    return n / d if d else None


def calculate(fact: pd.DataFrame) -> dict:
    d = fact[fact.is_delivered]
    eligible = fact[fact.delivery_eligible]
    reviewed = fact[fact.review_score.notna()]
    customers = fact.groupby("customer_unique_id").size()
    gmv = float(d.item_gmv.sum())
    return {"total_orders": len(fact), "delivered_orders": len(d), "cancelled_orders": int(fact.is_cancelled.sum()),
            "gmv": gmv, "freight": float(d.freight_value.sum()),
            "aov": divide(gmv, int(d.item_count.gt(0).sum())),
            "on_time_rate": divide(100 * int((~eligible.is_late).sum()), len(eligible)),
            "late_rate": divide(100 * int(eligible.is_late.sum()), len(eligible)),
            "delivery_days": float(d.delivery_days.mean()) if d.delivery_days.notna().any() else None,
            "delay_days": float(eligible.loc[eligible.is_late, "delay_days"].mean()) if eligible.is_late.any() else None,
            "review_score": float(reviewed.review_score.mean()) if len(reviewed) else None,
            "negative_review_rate": divide(100 * int(reviewed.review_score.le(2).sum()), len(reviewed)),
            "repeat_customer_rate": divide(100 * int(customers.gt(1).sum()), len(customers))}


def segment_performance(items: pd.DataFrame, dimension: str) -> pd.DataFrame:
    # Seller/category performance counted per distinct order within segment; GMV per item.
    segments = []
    for value, group in items.groupby(dimension):
        orders = group.drop_duplicates("order_id")
        eligible = orders[orders.delivery_eligible]
        delivered = group[group.order_status.eq("delivered")]
        segments.append({dimension: value, "orders": len(orders), "eligible_deliveries": len(eligible),
                         "late_orders": int(eligible.is_late.sum()),
                         "late_rate": divide(100 * int(eligible.is_late.sum()), len(eligible)),
                         "delivered_gmv": float(delivered.price.sum()),
                         "average_review": float(orders.review_score.mean()),
                         "average_delay_days": float(eligible.delay_days.mean())})
    return pd.DataFrame(segments).sort_values(["late_orders", "orders"], ascending=False) if segments else pd.DataFrame()
