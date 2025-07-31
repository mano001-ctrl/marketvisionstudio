import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def run():
    st.title("🧮 Expected P&L Simulator")

    # Sidebar Inputs
    win_prob = st.sidebar.slider("Win Probability", 0.0, 1.0, 0.80, 0.01)
    win_exp = st.sidebar.slider("Win Expectation", 0.0, 200.0, 90.0, 1.0)
    loss_exp = st.sidebar.slider("Loss Expectation", -200.0, 0.0, -200.0, 1.0)

    # Display expectation
    loss_prob = 1.0 - win_prob
    expected_pl = win_prob * win_exp + loss_prob * loss_exp

    st.markdown(f"**Expected P/L:** {expected_pl:.2f}")

    # Simulate and Plot
    if st.button("Run Simulation"):
        try:
            steps = 252
            result = np.zeros(steps + 1)
            result[1:] = np.where(
                np.random.rand(steps) < win_prob, win_exp, loss_exp
            )
            cumulative = np.cumsum(result)

            fig, ax = plt.subplots(figsize=(6, 3))  # keep it small
            ax.plot(cumulative)
            ax.set_title("Cumulative P/L")
            ax.set_xlabel("Day")
            ax.set_ylabel("P/L")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Simulation failed: {e}")
