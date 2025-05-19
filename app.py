import streamlit as st
import pandas as pd
from pathlib import Path
from collections import defaultdict
import secrets
from streamlit_option_menu import option_menu

# ---------- File Paths ----------
PATIENTS_CSV = Path("patients.csv")
APPOINTMENTS_CSV = Path("appointments.csv")
DOCTOR_DETAILS_CSV = Path("details.csv")
DOCTOR_LOGIN_CSV = Path("doctor_login.csv")

# ---------- Page Config ----------
st.set_page_config("Doctor Appointment System", layout="wide")

# ---------- Session State Defaults ----------
defaults = {
    "patient_logged_in": False,
    "doctor_logged_in": False,
    "patient_name": "",
    "patient_id": "",
    "doctor_name": ""
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------- CSV Utilities ----------
def load_csv(path, columns):
    try:
        df = pd.read_csv(path)
        if not all(col in df.columns for col in columns):
            return pd.DataFrame(columns=columns)
        return df
    except:
        return pd.DataFrame(columns=columns)

def save_csv(df, path):
    df.to_csv(path, index=False)

# ---------- Load Data ----------
patients_df = load_csv(PATIENTS_CSV, ["name", "patient_id", "password", "mobile"])
appointments_df = load_csv(APPOINTMENTS_CSV, ["Doctor's Name", "Patient's Name", "Date", "Time"])
doctor_details_df = load_csv(DOCTOR_DETAILS_CSV, ["Doctor's Name", "speciality"])
doctor_login_df = load_csv(DOCTOR_LOGIN_CSV, ["username", "password", "name"])

# ---------- Group Doctors by Specialty ----------
doctor_specialties = defaultdict(list)
for _, row in doctor_details_df.iterrows():
    doctor_specialties[row["speciality"]].append(row["Doctor's Name"])

# ---------- Sidebar Navigation ----------
with st.sidebar:
    st.markdown("## 🌐 Navigation")

    if st.session_state.patient_logged_in:
        selected = option_menu("Menu", ["Book Appointment", "View Appointments"],
                               icons=["calendar-plus", "card-list"], default_index=0)
        st.markdown(f"👤 Logged in as: **{st.session_state.patient_name}**")
        if st.button("🚪 Log Out"):
            for k in ["patient_logged_in", "patient_name", "patient_id"]:
                st.session_state[k] = False if k == "patient_logged_in" else ""
            st.rerun()

    elif st.session_state.doctor_logged_in:
        selected = option_menu("Menu", ["Doctor's Appointments"],
                               icons=["clipboard-data"], default_index=0)
        st.markdown(f"🧪 Logged in as Dr. **{st.session_state.doctor_name}**")
        if st.button("🚪 Log Out"):
            for k in ["doctor_logged_in", "doctor_name"]:
                st.session_state[k] = False if k == "doctor_logged_in" else ""
            st.rerun()

    else:
        selected = option_menu("Menu", ["Patient Login", "Patient Sign Up", "Doctor Login"],
                               icons=["box-arrow-in-right", "person-plus", "person-badge"], default_index=0)

# ---------- Title ----------
st.title("🏥 Doctor Appointment Booking System")

# =====================
# Patient Login
# =====================
if selected == "Patient Login":
    st.subheader("🔐 Patient Login")
    name = st.text_input("Patient Name")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        match = patients_df[
            (patients_df["name"].str.lower() == name.strip().lower()) &
            (patients_df["password"] == password)
        ]
        if not match.empty:
            st.session_state.patient_logged_in = True
            st.session_state.patient_name = match.iloc[0]["name"]
            st.session_state.patient_id = match.iloc[0]["patient_id"]
            st.success(f"✅ Logged in as {st.session_state.patient_name}")
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")

# =====================
# Patient Sign Up
# =====================
elif selected == "Patient Sign Up":
    st.subheader("📝 Patient Sign-Up")
    name = st.text_input("Full Name").strip().title()
    password = st.text_input("Create Password", type="password")
    mobile = st.text_input("Mobile Number")

    def generate_id():
        return ''.join(str(secrets.randbelow(10)) for _ in range(8))

    if st.button("Register"):
        if name and password and mobile:
            if not mobile.isdigit() or len(mobile) != 10:
                st.warning("📵 Invalid mobile number.")
            elif len(password) < 6:
                st.warning("🔐 Password too short (min 6 chars).")
            elif not patients_df[(patients_df["name"] == name) & (patients_df["mobile"] == mobile)].empty:
                st.error("⚠️ Patient already registered.")
            else:
                patient_id = generate_id()
                new_row = pd.DataFrame([[name, patient_id, password, mobile]],
                                       columns=["name", "patient_id", "password", "mobile"])
                patients_df = pd.concat([patients_df, new_row], ignore_index=True)
                save_csv(patients_df, PATIENTS_CSV)
                st.success("✅ Registered successfully!")
                st.info(f"🆔 Your Patient ID: `{patient_id}`")
        else:
            st.warning("Fill in all fields.")

# =====================
# Doctor Login
# =====================
elif selected == "Doctor Login":
    st.subheader("🔐 Doctor Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login as Doctor"):
        match = doctor_login_df[
            (doctor_login_df["username"].str.lower() == username.strip().lower()) &
            (doctor_login_df["password"] == password)
        ]
        if not match.empty:
            st.session_state.doctor_logged_in = True
            st.session_state.doctor_name = match.iloc[0]["name"]
            st.success(f"🧪 Logged in as Dr. {st.session_state.doctor_name}")
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")

# =====================
# Book Appointment
# =====================
elif selected == "Book Appointment":
    st.subheader("📅 Book an Appointment")
    if not st.session_state.patient_logged_in:
        st.warning("Log in to book an appointment.")
    elif doctor_details_df.empty:
        st.info("No doctors available.")
    else:
        specialty = st.selectbox("Choose Specialty", list(doctor_specialties.keys()))
        doctor = st.selectbox("Choose Doctor", doctor_specialties[specialty])
        date = st.date_input("Date")
        time = st.time_input("Time")

        if st.button("Book"):
            appointments_df = load_csv(APPOINTMENTS_CSV, ["Doctor's Name", "Patient's Name", "Date", "Time"])
            conflict = appointments_df[
                (appointments_df["Doctor's Name"] == doctor) &
                (appointments_df["Date"] == str(date)) &
                (appointments_df["Time"] == str(time))
            ]
            duplicate = appointments_df[
                (appointments_df["Patient's Name"] == st.session_state.patient_name) &
                (appointments_df["Date"] == str(date)) &
                (appointments_df["Time"] == str(time))
            ]
            if not conflict.empty:
                st.error("❌ Slot already booked.")
            elif not duplicate.empty:
                st.warning("⚠️ You already have an appointment at this time.")
            else:
                new_appt = pd.DataFrame([[doctor, st.session_state.patient_name, str(date), str(time)]],
                                        columns=["Doctor's Name", "Patient's Name", "Date", "Time"])
                appointments_df = pd.concat([appointments_df, new_appt], ignore_index=True)
                save_csv(appointments_df, APPOINTMENTS_CSV)
                st.success(f"✅ Appointment booked with Dr. {doctor} on {date} at {time}")

# =====================
# View Appointments (Patient)
# =====================
elif selected == "View Appointments":
    st.subheader("📋 Your Appointments")
    if not st.session_state.patient_logged_in:
        st.warning("Login to view appointments.")
    else:
        appointments_df = load_csv(APPOINTMENTS_CSV, ["Doctor's Name", "Patient's Name", "Date", "Time"])
        my_appts = appointments_df[appointments_df["Patient's Name"] == st.session_state.patient_name]
        if not my_appts.empty:
            my_appts["datetime"] = pd.to_datetime(my_appts["Date"] + " " + my_appts["Time"])
            st.dataframe(my_appts.sort_values("datetime").drop(columns="datetime"))
        else:
            st.info("📭 No appointments found.")

# =====================
# View Appointments (Doctor)
# =====================
elif selected == "Doctor's Appointments":
    st.subheader("📁 Doctor's Appointments")
    if not st.session_state.doctor_logged_in:
        st.warning("Doctor access only.")
    else:
        appointments_df = load_csv(APPOINTMENTS_CSV, ["Doctor's Name", "Patient's Name", "Date", "Time"])
        my_appts = appointments_df[appointments_df["Doctor's Name"] == st.session_state.doctor_name]
        if not my_appts.empty:
            my_appts["datetime"] = pd.to_datetime(my_appts["Date"] + " " + my_appts["Time"])
            st.dataframe(my_appts.sort_values("datetime").drop(columns="datetime"))
        else:
            st.info("📭 No bookings found.")
