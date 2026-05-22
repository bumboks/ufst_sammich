import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
st.set_page_config(layout="wide")

# --- Config ---
SMØRREBRØD = [
    "Fiskefilet med remoulade",
    "Fiskefilet med mayonaise & rejer",
    "Hjemmelavet hønsesalat med bacon",
    "Hjemmelavet skinkesalat med rødløg",
    "Hjemmelavet æggesalat m. bacon eller stegte løg",
    "Æg med mayonaise & rejer",
    "Æg & tomat med purløg",
    "Æg & avokado",
    "Æg med karrysalat & bacon",
    "Roastbeef med remoulade, peberrod & stegte løg",
    "Hjemmelavet frikadelle med surt",
    "Rullepølse med tyttebær/peberrodscreme",
    "Røget laks med tyttebær/peberrodscreme",
    "Tunmousse med hjemmesyltet kål",
    "Kartofler med stegte løg",
    "Kartofler med rå løg",
    "Kartofler med bacon",
    "Leverpostej med bacon & surt",
    "Dyrlægens natmad",
    "Hjemmelavet flæskesteg m. rødkål & agurkesalat",
    "Røget skinke med italiensk salat"
]
SANDWICHES = [
    "Chilimarineret kylling m. stegte svampe & artiskok",
    "Crispy kylling m. chilimayo, avokado & bacon",
    "Stegt kylling m. bacon & karrydressing",
    "Håndskåret flæskesteg m. sprøde svær, rødkål & agurkesalat",
    "Hjemmelavet frikadelle m. rødkål & agurkesalat",
    "Røget skinke m. ost, bacon & sennepscreme",
    "Roastbeef m. remoulade, peberrod, stegte løg & agurkesalat",
    "Serranoskinke & italiensk parmesanost",
    "Stegt kylling m. mortadella, rå løg & hjemmelavet grøn pesto",
    "Æg & rejer",
    "Æg & bacon",
    "Æg & tunsalat",
    "Tunsalat m. emmentaler, avokado & rød pesto",
    "Røget laks m. cremet friskost & purløg"
]
SIZES = ["medium", "large", "luksus"]
PRICES_SMØRREBRØD = {"medium": 28, "large": 55, "luksus": 75}
PRICE_SANDWICH_BASE = 85
EXTRA_AVOCADO_PRICE = 15
EXTRA_BACON_PRICE = 15
ORDERS_FILE = Path("orders.json")

# --- Helper Functions ---
def load_orders():
    if ORDERS_FILE.exists():
        with open(ORDERS_FILE, "r") as f:
            orders = json.load(f)
        for order in orders:
            if "total" not in order:
                total = 0
                for item in order.get("items", []):
                    if "size" in item:
                        size = item.get("size", "medium")
                        qty = item.get("qty", 0)
                        total += qty * PRICES_SMØRREBRØD.get(size, 0)
                    elif "extra" in item:
                        extra = item.get("extra", "")
                        qty = item.get("qty", 0)
                        extra_price = 0
                        if "ekstra avocado" in extra:
                            extra_price += EXTRA_AVOCADO_PRICE
                        if "ekstra Bacon" in extra:
                            extra_price += EXTRA_BACON_PRICE
                        total += qty * (PRICE_SANDWICH_BASE + extra_price)
                    else:
                        size = item.get("size", "medium")
                        qty = item.get("qty", 0)
                        total += qty * PRICES_SMØRREBRØD.get(size, 0)
                order["total"] = total
            for item in order.get("items", []):
                if "price_per_unit" not in item:
                    if "size" in item:
                        item["price_per_unit"] = PRICES_SMØRREBRØD.get(item.get("size", "medium"), 0)
                        if "type" not in item:
                            item["type"] = "smørrebrød"
                            item["name"] = item.get("smørrebrød", item.get("name", "Unknown"))
                    elif "extra" in item:
                        extra = item.get("extra", "")
                        extra_price = 0
                        if "ekstra avocado" in extra:
                            extra_price += EXTRA_AVOCADO_PRICE
                        if "ekstra Bacon" in extra:
                            extra_price += EXTRA_BACON_PRICE
                        item["price_per_unit"] = PRICE_SANDWICH_BASE + extra_price
                        if "type" not in item:
                            item["type"] = "sandwich"
                            item["name"] = item.get("sandwich", item.get("name", "Unknown"))
                    else:
                        item["price_per_unit"] = PRICES_SMØRREBRØD.get(item.get("size", "medium"), 0)
                        if "type" not in item:
                            item["type"] = "smørrebrød"
                            item["name"] = item.get("smørrebrød", item.get("name", "Unknown"))
        return orders
    return []

def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def get_combined_order(orders):
    """Aggregate all orders into a combined order summary."""
    combined = defaultdict(lambda: defaultdict(int))
    for order in orders:
        for item in order.get("items", []):
            item_type = item.get("type", "smørrebrød")
            name = item.get("name", "Unknown")
            if item_type == "smørrebrød" or "size" in item:
                variant = item.get("size", "medium")
                combined[name][variant] += item.get("qty", 0)
            else:
                variant = item.get("extra", "Ingen ekstra")
                combined[name][variant] += item.get("qty", 0)
    return combined

# --- Reset Quantities Flag ---
if "reset_quantities" not in st.session_state:
    st.session_state.reset_quantities = False

if st.session_state.reset_quantities:
    for smørrebrød in SMØRREBRØD:
        st.session_state[f"qty_{smørrebrød}"] = 0
    for sandwich in SANDWICHES:
        st.session_state[f"qty_sandwich_{sandwich}"] = 0
        st.session_state[f"extra_avocado_{sandwich}"] = False
        st.session_state[f"extra_bacon_{sandwich}"] = False
    st.session_state.reset_quantities = False

# --- App Title ---
st.title("🥪 Smørrebrød & Sandwich Ordering System")
st.markdown("Place your order below. All orders are visible to everyone!")

# --- Two-Column Layout (Left: 2/3, Right: 1/3) ---
left_col, right_col = st.columns([2, 1])

# --- LEFT COLUMN: Order Form ---
with left_col:
    with st.form("order_form"):
        st.subheader("Place Your Order")
        name = st.text_input("Your Name *", placeholder="e.g., Mads Hjort Larsen")

        # --- Collapsible Smørrebrød Section ---
        with st.expander("🍽️ Smørrebrød", expanded=True):
            order_items = []
            for smørrebrød in SMØRREBRØD:
                cols = st.columns([3, 2, 1, 1])
                with cols[0]:
                    st.write(f"- {smørrebrød}")
                with cols[1]:
                    size = st.radio(
                        f"Size for {smørrebrød}",
                        SIZES,
                        key=f"size_{smørrebrød}",
                        label_visibility="collapsed",
                        horizontal=True
                    )
                with cols[2]:
                    qty = st.number_input(
                        "Qty",
                        min_value=0,
                        max_value=10,
                        value=0,
                        key=f"qty_{smørrebrød}",
                        label_visibility="collapsed"
                    )
                with cols[3]:
                    if qty > 0 and size:
                        st.write(f"DKK {PRICES_SMØRREBRØD[size]}")

                if qty > 0:
                    order_items.append({
                        "type": "smørrebrød",
                        "name": smørrebrød,
                        "size": size,
                        "qty": qty,
                        "price_per_unit": PRICES_SMØRREBRØD[size]
                    })

        # --- Collapsible Sandwiches Section ---
        with st.expander("🥪 Sandwiches", expanded=True):
            for sandwich in SANDWICHES:
                cols = st.columns([3, 2, 1, 1])
                with cols[0]:
                    st.write(f"- {sandwich}")
                with cols[1]:
                    ekstra_avocado = st.checkbox(
                        "ekstra avocado",
                        key=f"extra_avocado_{sandwich}"
                    )
                    ekstra_bacon = st.checkbox(
                        "ekstra Bacon",
                        key=f"extra_bacon_{sandwich}"
                    )
                with cols[2]:
                    qty = st.number_input(
                        "Qty",
                        min_value=0,
                        max_value=10,
                        value=0,
                        key=f"qty_sandwich_{sandwich}",
                        label_visibility="collapsed"
                    )
                with cols[3]:
                    if qty > 0:
                        price = PRICE_SANDWICH_BASE
                        if ekstra_avocado:
                            price += EXTRA_AVOCADO_PRICE
                        if ekstra_bacon:
                            price += EXTRA_BACON_PRICE
                        st.write(f"DKK {price}")

                if qty > 0:
                    selected_extras = []
                    if ekstra_avocado:
                        selected_extras.append("ekstra avocado")
                    if ekstra_bacon:
                        selected_extras.append("ekstra Bacon")
                    extras_str = ", ".join(selected_extras) if selected_extras else "Ingen ekstra"

                    order_items.append({
                        "type": "sandwich",
                        "name": sandwich,
                        "extra": extras_str,
                        "qty": qty,
                        "price_per_unit": PRICE_SANDWICH_BASE +
                            (EXTRA_AVOCADO_PRICE if ekstra_avocado else 0) +
                            (EXTRA_BACON_PRICE if ekstra_bacon else 0)
                    })

        submitted = st.form_submit_button("Submit Order")

        if submitted:
            if not name:
                st.error("Please enter your name!")
            elif not order_items:
                st.error("Please order at least one item!")
            else:
                order_total = sum(
                    item["qty"] * item["price_per_unit"] for item in order_items
                )
                new_order = {
                    "name": name,
                    "items": order_items,
                    "total": order_total,
                    "timestamp": datetime.now().isoformat(),
                }
                orders = load_orders()
                orders.append(new_order)
                save_orders(orders)
                st.success(f"Order submitted, {name}! Total: DKK {order_total} ✅")
                st.session_state.reset_quantities = True
                st.rerun()

# --- RIGHT COLUMN: Orders List + Reset ---
with right_col:
    # --- Price List ---
    st.subheader("💰 Price List")
    st.markdown("**Smørrebrød Sizes:**")
    for size, price in PRICES_SMØRREBRØD.items():
        st.write(f"- {size.capitalize()}: DKK {price}")
    st.markdown("**Sandwiches:**")
    st.write(f"- Base: DKK {PRICE_SANDWICH_BASE}")
    st.write(f"- ekstra avocado: +DKK {EXTRA_AVOCADO_PRICE}")
    st.write(f"- ekstra Bacon: +DKK {EXTRA_BACON_PRICE}")
    st.divider()

    st.subheader("📋 Current Orders")
    orders = load_orders()

    if not orders:
        st.info("No orders yet. Be the first!")
    else:
        grand_total = sum(order.get("total", 0) for order in orders)
        st.metric("💰 Grand Total (All Orders)", f"DKK {grand_total}")

        # --- Combined Order Summary ---
        st.subheader("📞 Combined Order (For Phone Orders)")
        combined = get_combined_order(orders)
        for item_name, variants in combined.items():
            for variant, qty in variants.items():
                if qty > 0:
                    if item_name in SANDWICHES:
                        # Sandwich format: "1 Chilimarineret kylling... med ekstra avocado and ekstra Bacon"
                        if variant == "Ingen ekstra":
                            st.write(f"{qty} {item_name}")
                        else:
                            extras = variant.split(", ")
                            extras_str = " og ".join(extras)
                            st.write(f"{qty} {item_name} med {extras_str}")
                    else:
                        # Smørrebrød format: "2 (luksus) Fiskefilet med remoulade"
                        st.write(f"{qty} ({variant}) {item_name}")

        st.divider()

        # --- Individual Orders ---
        st.subheader("📄 Order Details")
        for i, order in enumerate(reversed(orders), 1):
            with st.expander(
                f"Order #{len(orders) - i + 1} - {order['name']} | "
                f"DKK {order.get('total', 0)} | {order['timestamp'][:19]}"
            ):
                for item in order.get("items", []):
                    item_type = item.get("type", "smørrebrød")
                    name = item.get("name", "Unknown")
                    if item_type == "smørrebrød" or "size" in item:
                        size = item.get("size", "medium")
                        subtotal = item["qty"] * item["price_per_unit"]
                        st.write(f"- **{name}** ({size}) x{item['qty']} = DKK {subtotal}")
                    else:
                        extra = item.get("extra", "Ingen ekstra")
                        subtotal = item["qty"] * item["price_per_unit"]
                        st.write(f"- **{name}** ({extra}) x{item['qty']} = DKK {subtotal}")

    st.divider()
    st.subheader("🗑️ Reset Orders (After Delivery)")
    reset_confirmed = st.checkbox("✅ I confirm all orders have been delivered and I want to reset the list.")
    if st.button("Reset All Orders", disabled=not reset_confirmed, type="primary"):
        save_orders([])
        st.success("All orders have been cleared! 🎉")
        st.rerun()