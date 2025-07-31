# pl_simulator.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math

def run():
    st.title("🧮 Expected P&L Simulator")

    # Sidebar Inputs
    win_prob = st.sidebar.slider("Win Probability", 0.0, 1.0, 0.80, 0.01)
    win_exp = st.sidebar.slider("Win Expectation", 0.0, 200.0, 90.0, 1.0)
    loss_exp = st.sidebar.slider("Loss Expectation", -200.0, 0.0, -200.0, 1.0)

    # Expectation
    if math.isfinite(win_prob) and math.isfinite(win_exp) and math.isfinite(loss_exp):
        loss_prob = 1 - win_prob
        expected_pl = win_prob * win_exp + loss_prob * loss_exp

        st.subheader("📊 Expectation Metrics")
        st.markdown(f"- **Expected P/L:** {expected_pl:.2f}")
        st.markdown(f"- **Win Probability:** {win_prob:.2f}")
        st.markdown(f"- **Loss Probability:** {loss_prob:.2f}")
        st.markdown(f"- **Win Amount:** {win_exp:.2f}")
        st.markdown(f"- **Loss Amount:** {loss_exp:.2f}")
    else:
        st.error("⚠️ Invalid input values.")

    # Run Simulation
    if st.button("Run Simulation"):
        try:
            result = [0]
            for _ in range(252):
                result.append(result[-1] + (win_exp if np.random.rand() < win_prob else loss_exp))

            fig, ax = plt.subplots()
            ax.plot(result, label="Cumulative P/L", linewidth=2)
            ax.axhline(0, color="gray", linestyle="--")
            ax.set_title("📈 Simulated Trading Path (252 Days)")
            ax.set_xlabel("Day")
            ax.set_ylabel("Cumulative P/L")
            ax.legend()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Simulation error: {e}")
