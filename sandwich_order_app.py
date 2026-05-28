import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from zoneinfo import ZoneInfo

st.set_page_config(
    layout="wide",
    page_title="AI SLOP BY MADS",
    page_icon="🤡"
)

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
    "Tunsalat m. emmentaler, avocado & rød pesto",
    "Røget laks m. cremet friskost & purløg"
]
SIZES = ["medium", "large", "luksus"]
PRICES_SMØRREBRØD = {"medium": 28, "large": 55, "luksus": 75}
PRICE_SANDWICH_BASE = 85
EXTRA_AVOCADO_PRICE = 15
EXTRA_BACON_PRICE = 15
ORDERS_FILE = Path("orders.json")
PASSWORD = st.secrets.get("password")

# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login Required")
    st.write("Enter the password to view the ordering page.")

    password_input = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if not PASSWORD:
            st.error("No password is configured. Please add `password` to secrets.toml.")
        elif password_input == PASSWORD:
            st.session_state.authenticated = True
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

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
                        if "avocado" in extra.lower():
                            extra_price += EXTRA_AVOCADO_PRICE
                        if "bacon" in extra.lower():
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
                        if "avocado" in extra.lower():
                            extra_price += EXTRA_AVOCADO_PRICE
                        if "bacon" in extra.lower():
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

def get_denmark_timestamp():
    return datetime.now(ZoneInfo("Europe/Copenhagen")).isoformat(timespec="seconds")

def format_timestamp(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp)
    except ValueError:
        return timestamp

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Europe/Copenhagen"))

    return dt.astimezone(ZoneInfo("Europe/Copenhagen")).strftime("%Y-%m-%d %H:%M:%S %Z")

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
                variant = item.get("extra", "Intet ekstra")
                combined[name][variant] += item.get("qty", 0)
    return combined

def format_combined_order_as_text(combined):
    """Format the combined order as plain text for download."""
    lines = []
    lines.append("=== Kombineret Bestilling ===\n")

    for item_name in sorted(combined.keys()):
        for variant in sorted(combined[item_name].keys()):
            qty = combined[item_name][variant]
            if qty > 0:
                if item_name in SANDWICHES:
                    if variant == "Intet ekstra":
                        lines.append(f"{qty}x {item_name}")
                    else:
                        extras = variant.split(", ")
                        extras_str = " og ".join(extras)
                        lines.append(f"{qty}x {item_name} med ekstra {extras_str}")
                else:
                    lines.append(f"{qty}x ({variant}) {item_name}")

    return "\n".join(lines)

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
st.title("B.A.S.S. 🥪 (Bestilling Af Smørrebrød og Sandwiches)")
st.markdown("Indtast din bestilling herunder. Alle bestillinger er synlige for alle!")

# --- Price List ---
price_left, price_right = st.columns([2, 1])
with price_left:
    price_col1, price_col2 = st.columns([1, 1])
    with price_col1:
        st.subheader("💰 Smørrebrød priser:")
        st.markdown(f"- Medium: {PRICES_SMØRREBRØD['medium']} DKK\n- Large: {PRICES_SMØRREBRØD['large']} DKK\n- Luksus: {PRICES_SMØRREBRØD['luksus']} DKK")
    with price_col2:
        st.subheader("💰 Sandwich priser:")
        st.markdown(
            f"- Normal: {PRICE_SANDWICH_BASE} DKK\n- Ekstra avocado: +{EXTRA_AVOCADO_PRICE} DKK\n- Ekstra bacon: +{EXTRA_BACON_PRICE} DKK"
        )
with price_right:
    st.markdown("### 📞 +45 28 44 17 40\n### 🕒 Man-Fre 09.00-14.00\n ### 🏠 [mitlillekoekken.dk](https://mitlillekoekken.dk)")

# --- Two-Column Layout (Left: 2/3, Right: 1/3) ---
left_col, right_col = st.columns([2, 1])

# --- LEFT COLUMN: Order Form ---
with left_col:
    with st.form("order_form"):
        st.subheader("Menukort")

        # --- Collapsible Smørrebrød Section ---
        with st.expander("🍽️ Smørrebrød", expanded=False):
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
        with st.expander("🥪 Sandwiches", expanded=False):
            for sandwich in SANDWICHES:
                cols = st.columns([3, 2, 1, 1])
                with cols[0]:
                    st.write(f"- {sandwich}")
                with cols[1]:
                    checkbox_cols = st.columns([1, 1])
                    with checkbox_cols[0]:
                        ekstra_avocado = st.checkbox(
                            "avocado",
                            key=f"extra_avocado_{sandwich}"
                        )
                    with checkbox_cols[1]:
                        ekstra_bacon = st.checkbox(
                            "bacon",
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
                        selected_extras.append("avocado")
                    if ekstra_bacon:
                        selected_extras.append("bacon")
                    extras_str = ", ".join(selected_extras) if selected_extras else "Intet ekstra"

                    order_items.append({
                        "type": "sandwich",
                        "name": sandwich,
                        "extra": extras_str,
                        "qty": qty,
                        "price_per_unit": PRICE_SANDWICH_BASE +
                            (EXTRA_AVOCADO_PRICE if ekstra_avocado else 0) +
                            (EXTRA_BACON_PRICE if ekstra_bacon else 0)
                    })

        name_input_col, submit_col = st.columns([4, 1])
        with name_input_col:
            name = st.text_input("", placeholder="Indtast dit navn f.eks. Allan Jakobsen", label_visibility="collapsed")
        with submit_col:
            submitted = st.form_submit_button("Send bestilling")

        if submitted:
            if not name:
                st.error("Indtast venligst dit navn!")
            elif not order_items:
                st.error("Bestil mindst en ting!")
            else:
                order_total = sum(
                    item["qty"] * item["price_per_unit"] for item in order_items
                )
                new_order = {
                    "name": name,
                    "items": order_items,
                    "total": order_total,
                    "timestamp": get_denmark_timestamp(),
                }
                orders = load_orders()
                orders.append(new_order)
                save_orders(orders)
                st.success(f"Order submitted, {name}! Total: DKK {order_total} ✅")
                st.session_state.reset_quantities = True
                st.rerun()

# --- RIGHT COLUMN: Orders List + Reset + File Handling ---
with right_col:
    orders = load_orders()

    # --- Orders List ---
    if not orders:
        st.info("Ingen bestillinger endnu. Vær den første!")
    else:
        grand_total = sum(order.get("total", 0) for order in orders)
        st.metric("💰 Pris i alt (for alle bestillinger)", f"DKK {grand_total}")

        # --- Combined Order Summary ---
        st.subheader("🗒️ Kombineret bestilling")
        combined = get_combined_order(orders)

        # Sort items alphabetically by name
        for item_name in sorted(combined.keys()):
            for variant in sorted(combined[item_name].keys()):
                qty = combined[item_name][variant]
                if qty > 0:
                    if item_name in SANDWICHES:
                        if variant == "Intet ekstra":
                            st.write(f"{qty} {item_name}")
                        else:
                            extras = variant.split(", ")
                            extras_str = " og ".join(extras)
                            st.write(f"{qty} {item_name} med ekstra {extras_str}")
                    else:
                        st.write(f"{qty} ({variant}) {item_name}")

        st.divider()

        # --- Individual Orders ---
        st.subheader("📄 Individuelle bestillinger")
        for i, order in enumerate(reversed(orders), 1):
            original_index = len(orders) - i
            with st.expander(
                f"Bestilling #{len(orders) - i + 1} - {order['name']} | "
                f"DKK {order.get('total', 0)} | {format_timestamp(order.get('timestamp', ''))}"
            ):
                for item in order.get("items", []):
                    item_type = item.get("type", "smørrebrød")
                    name = item.get("name", "Unknown")
                    if item_type == "smørrebrød" or "size" in item:
                        size = item.get("size", "medium")
                        subtotal = item["qty"] * item["price_per_unit"]
                        st.write(f"- **{name}** ({size}) x{item['qty']} = DKK {subtotal}")
                    else:
                        extra = item.get("extra", "Intet ekstra")
                        subtotal = item["qty"] * item["price_per_unit"]
                        st.write(f"- **{name}** ({extra}) x{item['qty']} = DKK {subtotal}")

                st.divider()
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🗑️ Slet bestilling", key=f"delete_order_{original_index}"):
                        orders.pop(original_index)
                        save_orders(orders)
                        st.success("Bestilling slettet!")
                        st.rerun()

    # --- File Handling Section ---
    st.divider()
    st.subheader("📥 Filhåndtering")
    col1, col2 = st.columns(2)
    with col1:
        combined_text = format_combined_order_as_text(get_combined_order(orders))
        st.download_button(
            label="📥 orders.txt",
            data=combined_text,
            file_name="orders.txt",
            mime="text/plain"
        )
    
    with col2:
        orders_json = json.dumps(orders, indent=2)
        st.download_button(
            label="📥 orders.json",
            data=orders_json,
            file_name="orders.json",
            mime="application/json"
        )

    uploaded_file = st.file_uploader("Upload orders.json (will overwrite current orders)", type=["json"])
    if uploaded_file is not None:
        try:
            new_orders = json.loads(uploaded_file.getvalue().decode("utf-8"))
            save_orders(new_orders)
            st.success("Bestillinger uploadet!")
            st.rerun()
        except Exception as e:
            st.error(f"Fejl ved upload: {e}")

    # --- Reset Orders ---
    st.divider()
    st.subheader("🗑️ Nulstil bestillinger (Efter levering)")
    reset_confirmed = st.checkbox("✅ Jeg bekræfter, at alle bestillinger er blevet leveret, og jeg vil nulstille listen.")
    if st.button("Nulstil alle bestillinger", disabled=not reset_confirmed, type="primary"):
        save_orders([])
        st.success("Alle bestillinger er blevet slettet! 🎉")
        st.rerun()