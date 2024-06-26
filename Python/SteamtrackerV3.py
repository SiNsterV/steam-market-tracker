import streamlit as st
import requests
import json
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime
from pathlib import Path
import database as ta
import os


def program():
    steam_api_key = st.secrets["STEAM_API"]
    username = st.session_state.get('user', 'No User Set')
    ta.create_usertable()
    tab1, tab2 = st.tabs(["Main", "Preset Manager"])

    with tab1:
        col1, col2, col3 = st.columns([2,2,4])
        #exchange_api_key = os.environ['exchange_api_key']
        app_id = 730  # CSGO App ID
        # Load or initialize the last_price dictionary
        def load_price_history():
            try:
                with open('price_record.json', 'r') as file:
                    return json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

        last_price = load_price_history()

        # Load or initialize presets
        def load_presets(username):
            with ta.get_db_connection() as conn:
                # It's important to fetch data as a dictionary or ensure you correctly reference columns
                cursor = conn.cursor()
                cursor.execute('SELECT preset_name, items FROM userstable WHERE username = ?', (username,))
                presets = {}
                for row in cursor.fetchall():  # Ensure that you iterate over fetched results
                    preset_name = row['preset_name']
                    items = row['items']
                    if items:  # Ensure that 'items' is not None or empty
                        try:
                            # Presuming items is stored as a JSON-encoded string
                            presets[preset_name] = json.loads(items)
                        except json.JSONDecodeError:
                            st.error(f"Error decoding JSON for preset: {preset_name}")
                    else:
                        st.error(f"No items found for preset: {preset_name}, possibly corrupted data.")
            return presets



        presets = load_presets(username)

        def save_presets(username, preset_name, items):
            items_json = json.dumps(items)
            with ta.get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO userstable (username, preset_name, items)
                    VALUES (?, ?, ?)
                ''', (username, preset_name, items_json))
                conn.commit()


        # Function to save the updated price history to a file
        def save_price_history(price_data):
            with open('price_record.json', 'w') as file:
                json.dump(price_data, file)

        def get_current_time():
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def get_steam_market_item(api_key, app_id, market_hash_name):
            url = f"https://steamcommunity.com/market/priceoverview/?appid={app_id}&currency=3&market_hash_name={market_hash_name}"
            headers = {'Content-Type': 'application/json'}
            params = {'key': api_key}
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                st.error("Failed to fetch item data: " + str(e))
                return None

        #rates = get_exchange_rates(exchange_)
        # Session state for storing prices, timing, and last prices for comparison
        if 'eur_price' not in st.session_state:
            st.session_state['eur_price'] = 0
            st.session_state['last_eur_price'] = 0
        #if 'czk_price' not in st.session_state:
        #   st.session_state['czk_price'] = 0
        #  st.session_state['last_czk_price'] = 0
        if 'last_update_time' not in st.session_state:
            st.session_state['last_update_time'] = 0

        if 'prices' not in st.session_state:
            st.session_state['prices'] = {}
        # Function to determine price trend emoji
        def price_trend(current, previous):
            if current > previous:
                return "🟩"
            elif current < previous:
                return "🟥"
            else:
                return "🔶"

        # Function to convert currency
        #def convert_currency(amount, rate):
            return round(amount * rate, 2)


        def update_price(steam_api_key, app_id, market_hash_name):
            current_time = get_current_time()
            if market_hash_name:
                item_data = get_steam_market_item(steam_api_key, app_id, market_hash_name)
                if item_data and 'lowest_price' in item_data:
                    #usd_price = float(item_data['lowest_price'].strip('$'))
                    new_eur_price = float(item_data['lowest_price'].strip('€').replace(',','.').replace('--','00'))
                    #new_czk_price = convert_currency(usd_price, rates.get('CZK', 0))

                    eur_emoji = price_trend(new_eur_price, st.session_state['prices'].get(market_hash_name, {}).get('last_eur_price', 0))
                    #czk_emoji = price_trend(new_czk_price, st.session_state['prices'].get(market_hash_name, {}).get('last_czk_price', 0))

                    if market_hash_name not in last_price:
                        last_price[market_hash_name] = {'eur': []}

                    # Append both price and timestamp
                    last_price[market_hash_name]['eur'].append({'price': new_eur_price, 'timestamp': current_time})
                    save_price_history(last_price)

                    st.session_state['prices'][market_hash_name] = {
                        'eur_price': f"{new_eur_price} {eur_emoji}",
                        #'czk_price': f"{new_czk_price} {czk_emoji}",
                        'last_eur_price': new_eur_price,
                        #'last_czk_price': new_czk_price
                    }
            else:
                st.warning("ENTER AN ITEM")
        # Button handling for adding and removing items

        def save_current_config(username):
            preset_name = st.session_state.preset_name
            if preset_name:
                items = [st.session_state.get(f'item_name{i+1}', '') for i in range(st.session_state.get('item_count', 0))]
                save_presets(username, preset_name, items)
                st.sidebar.success("Preset saved!")

        def load_selected_preset(username, selected_preset):
            presets = load_presets(username)
            if selected_preset in presets:
                preset_items = presets[selected_preset]
                st.session_state['item_count'] = len(preset_items)
                for idx, item_name in enumerate(preset_items):
                    st.session_state[f'item_name{idx+1}'] = item_name



        def add_item():
            if 'item_count' in st.session_state and st.session_state.item_count < 5:
                st.session_state.item_count += 1
            elif 'item_count' not in st.session_state:
                st.session_state.item_count = 1
            else:
                st.warning("Maximum of 5 items allowed.")

        def remove_item():
            if 'item_count' in st.session_state and st.session_state.item_count > 0:
                st.session_state.item_count -= 1
        st.sidebar.divider()
        st.sidebar.button("Add new item", on_click=add_item)
        st.sidebar.button("Remove Last Item", on_click=remove_item)
        st.sidebar.button("Manual Refresh")

        st.sidebar.divider()


        st.sidebar.header("Save current as preset")
        new_preset = st.sidebar.text_input("Preset Name", key='preset_name')

        if new_preset:
            save = st.sidebar.button("Save", on_click=save_current_config(username))

        st.sidebar.header("Load in a preset")
     # Using the load presets function and adding the choice to session state
        preset_options = list(load_presets(username).keys())
        if preset_options:  # Check if there are any presets
            selected_preset = st.sidebar.selectbox("Choose a preset", preset_options)
            if st.sidebar.button("Load"):
                # Load the selected preset's items
                load_selected_preset(username, selected_preset)  # Define this function if not already defined


        def load_data_to_dataframe():
            data = load_price_history()
            data_list = []

            for item_name, prices in data.items():
                for price_record in prices['eur']:
                    data_list.append({
                        'item_name': item_name,
                        'price': price_record['price'],
                        'timestamp': price_record['timestamp']
                    })

            df = pd.DataFrame(data_list)
            return df
        @st.experimental_fragment
        def plot_data(item_name):
            df = load_data_to_dataframe()
            if item_name in df['item_name'].unique():
                item_data = df[df['item_name'] == item_name]
                st.write(f"Price History for {item_name}")
                st.line_chart(item_data.set_index('timestamp')['price'])
            st_autorefresh(interval=150000, key=f'autorefresh{idx+1}')

        with col1:
                st.header("Input")

        with col2:
                st.header("Live Prices")

        with col3:
                st.header("Graph") 

        for idx in range(st.session_state.get('item_count', 0)):
                with col1:
                    with st.container(height=200):
                        market_hash_name = st.text_input("Enter Desired Item", key=f'item_name{idx+1}')
                        if market_hash_name:
                            update_price(steam_api_key, app_id, market_hash_name)

                    with col2:
                        with st.container(height=200):
                                if market_hash_name in st.session_state['prices']:
                                    empty_space = st.empty()
                                    st.metric(label="EUR", value=st.session_state['prices'][market_hash_name]['eur_price'])
                                    #st.metric(label="CZK", value=st.session_state['prices'][market_hash_name]['czk_price'])
                with col3:
                    with st.container(height=200):      
                        if market_hash_name:
                            plot_data(market_hash_name)

    with tab2:
        fill, col1, col2, fill2 = st.columns([1,2,2,1])

        def remove_preset(username, preset_name):
            with ta.get_db_connection() as conn:
                conn.execute('DELETE FROM userstable WHERE username = ? AND preset_name = ?', (username, preset_name))
                conn.commit()


        with col1:
            st.title("Preset Names")
            if presets:
                for preset_name in list(presets.keys()):
                    with st.container(height=100):
                        st.columns(3)[1].header(preset_name)
            else:
                st.write("No presets found") 

        with col2:
            st.title("Preset Actions")
            if presets:
                for preset_name in list(presets.keys()):
                    with st.container(height=100):
                        if st.columns(3)[1].button(f"Remove", key=f"btn_{preset_name}"):
                            remove_preset(username, preset_name)
