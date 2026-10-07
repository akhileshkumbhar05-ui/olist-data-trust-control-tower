"""DEMO / SYNTHETIC fixtures. Never report these as actual Olist findings."""
import pandas as pd
from olist.ingestion.catalog import SOURCES


def demo_tables():
    records = {
        "customers": [dict(customer_id="c1", customer_unique_id="person1", customer_zip_code_prefix="01000", customer_city="sao paulo", customer_state="SP"), dict(customer_id="c2", customer_unique_id="person1", customer_zip_code_prefix="01000", customer_city="sao paulo", customer_state="SP")],
        "orders": [dict(order_id="o1", customer_id="c1", order_status="delivered", order_purchase_timestamp="2018-01-01 08:00:00", order_approved_at="2018-01-01 09:00:00", order_delivered_carrier_date="2018-01-02 08:00:00", order_delivered_customer_date="2018-01-06 12:00:00", order_estimated_delivery_date="2018-01-05 00:00:00"),
                   dict(order_id="o2", customer_id="c2", order_status="delivered", order_purchase_timestamp="2018-02-01 08:00:00", order_approved_at="2018-02-01 09:00:00", order_delivered_carrier_date="2018-02-02 08:00:00", order_delivered_customer_date="2018-02-05 18:00:00", order_estimated_delivery_date="2018-02-05 00:00:00"),
                   dict(order_id="o3", customer_id="c1", order_status="canceled", order_purchase_timestamp="2018-02-01 08:00:00", order_estimated_delivery_date="2018-02-10 00:00:00")],
        "order_items": [dict(order_id="o1", order_item_id="1", product_id="p1", seller_id="s1", shipping_limit_date="2018-01-03", price="100", freight_value="10"), dict(order_id="o1", order_item_id="2", product_id="p1", seller_id="s2", shipping_limit_date="2018-01-03", price="50", freight_value="5"), dict(order_id="o2", order_item_id="1", product_id="p1", seller_id="s1", shipping_limit_date="2018-02-03", price="200", freight_value="20")],
        "payments": [dict(order_id="o1", payment_sequential="1", payment_type="credit_card", payment_installments="1", payment_value="100"), dict(order_id="o1", payment_sequential="2", payment_type="voucher", payment_installments="1", payment_value="65"), dict(order_id="o2", payment_sequential="1", payment_type="credit_card", payment_installments="1", payment_value="220")],
        "reviews": [dict(review_id="r1", order_id="o1", review_score="1", review_creation_date="2018-01-07", review_answer_timestamp="2018-01-08"), dict(review_id="r2", order_id="o1", review_score="2", review_creation_date="2018-01-07", review_answer_timestamp="2018-01-09"), dict(review_id="r3", order_id="o2", review_score="5", review_creation_date="2018-02-06", review_answer_timestamp="2018-02-07")],
        "products": [dict(product_id="p1", product_category_name="cama_mesa_banho", product_name_lenght="10", product_description_lenght="30", product_photos_qty="1", product_weight_g="100", product_length_cm="10", product_height_cm="10", product_width_cm="10")],
        "sellers": [dict(seller_id="s1", seller_zip_code_prefix="01000", seller_city="sao paulo", seller_state="SP"), dict(seller_id="s2", seller_zip_code_prefix="01000", seller_city="sao paulo", seller_state="SP")],
        "geolocation": [dict(geolocation_zip_code_prefix="01000", geolocation_lat="-23", geolocation_lng="-46", geolocation_city="sao paulo", geolocation_state="SP"), dict(geolocation_zip_code_prefix="01000", geolocation_lat="-24", geolocation_lng="-47", geolocation_city="sao paulo", geolocation_state="SP")],
        "translation": [dict(product_category_name="cama_mesa_banho", product_category_name_english="bed_bath_table")],
    }
    return {name: pd.DataFrame(records[name], columns=source.columns).astype("string") for name, source in SOURCES.items()}
