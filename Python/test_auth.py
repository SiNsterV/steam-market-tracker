import streamlit as st
import hashlib
import sqlite3
from SteamtrackerV3 import program
import database as data



st.set_page_config(layout="wide")

def main():

    if 'user' not in st.session_state:
        # User is not logged in
        menu = ["Login", "SignUp"]
        choice = st.sidebar.selectbox("Menu", menu)
        st.title("Please, create a new account to sign in, or sign in to your existing account.")
    else:
        # User is logged in
        menu = ["Home", "Logout"]
        choice = st.sidebar.selectbox("Menu", menu)
        st.sidebar.write(f"Logged in as {st.session_state['user']}")

    if choice == "Home":
        st.subheader("Home")

    elif choice == "Login" and 'user' not in st.session_state:
        st.sidebar.subheader("Login Section")
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            data.create_usertable()
            hashed_pswd = data.make_hashes(password)
            result = data.login_user(username, hashed_pswd)
            if result:
                st.session_state['user'] = result['username']
                st.success(f"Logged In as {username}")
                st.rerun()

            else:
                st.error("This process didn't succeed")

    elif choice == "SignUp" and 'user' not in st.session_state:
        st.sidebar.subheader("Create New Account")
        new_user = st.sidebar.text_input("Username")
        new_password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Signup") and new_user and new_password:
            data.create_usertable()
            data.add_userdata(new_user, data.make_hashes(new_password))
            st.success("You have successfully created an account")
            st.info("Go to Login Menu to login")
        else:
            st.sidebar.error("Username or password is empty.")

    elif choice == "Logout":
        st.session_state.pop('user', None)  # Remove user from session
        st.info("You have been logged out.")
        st.rerun()

    if 'user' in st.session_state:
        program()

if __name__ == '__main__':
    main()
