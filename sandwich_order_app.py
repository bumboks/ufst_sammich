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

# --- Order Manager ---

class OrderManager:
    ORDERS_FILE = ORDERS_FILE

    @staticmethod
    def get_price_per_unit(item):
        if item.get("type") == "sandwich":
            extra = item.get("extra", "")
            price = PRICE_SANDWICH_BASE
            if "avocado" in extra.lower():
                price += EXTRA_AVOCADO_PRICE
            if "bacon" in extra.lower():
                price += EXTRA_BACON_PRICE
            return price
        return PRICES_SMØRREBRØD.get(item.get("size", "medium"), 0)

    @classmethod
    def normalize_order_item(cls, item):
        item_type = item.get("type", "smørrebrød")
        item["type"] = item_type
        item["qty"] = item.get("qty", 0)

        if item_type == "sandwich":
            item["extra"] = item.get("extra", "Intet ekstra")
            item["name"] = item.get("sandwich", item.get("name", "Unknown"))
        else:
            item["size"] = item.get("size", "medium")
            item["name"] = item.get("smørrebrød", item.get("name", "Unknown"))

        item["price_per_unit"] = cls.get_price_per_unit(item)
        return item

    @classmethod
    def calculate_order_total(cls, items):
        return sum(item.get("qty", 0) * item.get("price_per_unit", cls.get_price_per_unit(item)) for item in items)

    @classmethod
    def load_orders(cls):
        if not cls.ORDERS_FILE.exists():
            return []

        with open(cls.ORDERS_FILE, "r") as f:
            orders = json.load(f)

        for order in orders:
            items = order.get("items", [])
            for item in items:
                cls.normalize_order_item(item)
            order["total"] = cls.calculate_order_total(items)

        return orders

    @classmethod
    def save_orders(cls, orders):
        with open(cls.ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=2)

    @classmethod
    def get_combined_order(cls, orders):
        combined = defaultdict(lambda: defaultdict(int))
        for order in orders:
            for item in order.get("items", []):
                item_type = item.get("type", "smørrebrød")
                name = item.get("name", "Unknown")
                variant = item.get("extra", "Intet ekstra") if item_type == "sandwich" else item.get("size", "medium")
                combined[name][variant] += item.get("qty", 0)
        return combined

    @staticmethod
    def format_order_item_line(item):
        item_type = item.get("type", "smørrebrød")
        qty = item.get("qty", 0)
        subtotal = qty * item.get("price_per_unit", OrderManager.get_price_per_unit(item))
        name = item.get("name", "Unknown")

        if item_type == "sandwich":
            extra = item.get("extra", "Intet ekstra")
            return f"- **{name}** ({extra}) x{qty} = DKK {subtotal}"
        return f"- **{name}** ({item.get('size', 'medium')}) x{qty} = DKK {subtotal}"

    @staticmethod
    def format_combined_order_line(item_name, variant, qty):
        if item_name in SANDWICHES:
            if variant == "Intet ekstra":
                return f"{qty} {item_name}"
            extras = " og ".join(variant.split(", "))
            return f"{qty} {item_name} med ekstra {extras}"
        return f"{qty} ({variant}) {item_name}"

    @classmethod
    def render_combined_order(cls, combined):
        for item_name, variants in combined.items():
            for variant, qty in variants.items():
                if qty > 0:
                    st.write(cls.format_combined_order_line(item_name, variant, qty))


# compatibility wrappers
get_price_per_unit = OrderManager.get_price_per_unit
normalize_order_item = OrderManager.normalize_order_item
calculate_order_total = OrderManager.calculate_order_total
load_orders = OrderManager.load_orders
save_orders = OrderManager.save_orders
get_combined_order = OrderManager.get_combined_order
format_order_item_line = OrderManager.format_order_item_line
format_combined_order_line = OrderManager.format_combined_order_line
render_combined_order = OrderManager.render_combined_order


def render_order_details(order, display_number, original_index):
    with st.expander(
        f"Order #{display_number} - {order['name']} | "
        f"DKK {order.get('total', 0)} | {format_timestamp(order.get('timestamp', ''))}"
    ):
        for item in order.get("items", []):
            st.write(format_order_item_line(item))

        st.divider()
        col1, _ = st.columns([1, 1])
        with col1:
            return st.button("🗑️ Slet bestilling", key=f"delete_order_{original_index}")

# --- App Title ---
st.title("🥪 (B.A.S.S.) Bestilling Af Smørrebørd og Sandwiches")
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
        name = st.text_input("Dit navn *", placeholder="f.eks., Allan Jakobsen")

        # --- Collapsible Smørrebrød Section ---
        with st.expander("🍽️ Smørrebrød", expanded=False):
            order_items = []
            for smørrebrød in SMØRREBRØD:
                render_smorrebrod_item(smørrebrød, order_items)

        # --- Collapsible Sandwiches Section ---
        with st.expander("🥪 Sandwiches", expanded=False):
            for sandwich in SANDWICHES:
                render_sandwich_item(sandwich, order_items)

        submitted = st.form_submit_button("Send bestilling")

        if submitted:
            if not name:
                st.error("Indtast venligst dit navn!")
            elif not order_items:
                st.error("Bestil mindst en ting!")
            else:
                order_total = calculate_order_total(order_items)
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
                reset_order_form_state()
                st.experimental_rerun()

# --- RIGHT COLUMN: Orders List + Reset ---
with right_col:
    #st.subheader("📋 Current Orders")
    orders = load_orders()

    if not orders:
        st.info("Ingen bestillinger endnu. Vær den første!")
    else:
        grand_total = sum(order.get("total", 0) for order in orders)
        st.metric("💰 Grand Total (All Orders)", f"DKK {grand_total}")

        # --- Combined Order Summary ---
        st.subheader("🗒️ Combined order")
        combined = get_combined_order(orders)
        render_combined_order(combined)

        st.divider()

        # --- Individual Orders ---
        st.subheader("📄 Order Details")
        for i, order in enumerate(reversed(orders), 1):
            original_index = len(orders) - i
            delete_pressed = render_order_details(order, len(orders) - i + 1, original_index)
            if delete_pressed:
                orders.pop(original_index)
                save_orders(orders)
                st.success("Bestilling slettet!")
                st.rerun()

    st.divider()
    st.subheader("🗑️ Nulstil bestillinger (Efter levering)")
    reset_confirmed = st.checkbox("✅ Jeg bekræfter, at alle bestillinger er blevet leveret, og jeg vil nulstille listen.")
    if st.button("Nulstil alle bestillinger", disabled=not reset_confirmed, type="primary"):
        save_orders([])
        st.success("Alle bestillinger er blevet slettet! 🎉")
        st.rerun()
