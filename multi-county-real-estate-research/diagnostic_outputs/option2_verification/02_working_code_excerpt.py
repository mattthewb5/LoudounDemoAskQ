# Lines 650-841 from loudoun_streamlit_app.py
# "School Performance vs State & Peers" section
#
# NOTE: This code appears to work (no duplicate lines) but actually has a DATA QUALITY bug.
# It uses match_school_in_performance_data() which has a first-word matching fallback
# that can return the WRONG school when multiple schools share a first word.

# Key pattern - uses create_performance_chart() which internally uses match_school_in_performance_data()
# See line 690 for example:
#   fig = create_performance_chart(elem_school, elem_peers, "Math", "Math_Pass_Rate", "Elem", perf_with_state_df)

# The create_performance_chart function (from core/loudoun_school_performance.py lines 255-387):
#
# def create_performance_chart(...):
#     chart_data = []
#
#     # 1. Get subject school data
#     subject_match = match_school_in_performance_data(subject_school, perf_df)  # <-- Can return wrong school!
#     if subject_match:
#         subject_data = perf_df[
#             (perf_df['School_Name'] == subject_match) &  # <-- Uses EXACT match on result
#             (perf_df['Division_Name'] == 'Loudoun County')
#         ]
#         # ... adds data to chart_data
#
# Why it APPEARS to work (no duplicate lines):
# - match_school_in_performance_data() returns ONE school name (or None)
# - The subsequent filter uses EXACT match on that name
# - Result: Only one school's data per line
#
# Why it ACTUALLY has a bug (wrong data):
# - match_school_in_performance_data() has a first-word fallback (lines 244-250)
# - It returns the FIRST school that matches the first word (based on file order)
# - For "Belmont Ridge Middle", it returns "Belmont Station Elementary" (wrong!)
#   because "Belmont Station Elementary" appears earlier in the data file

# COMPARISON WITH BUGGY CODE (lines 604-614):
#
# BUGGY (shows duplicate lines):
#   school_data = performance_df[
#       performance_df['School_Name'].str.contains(
#           school.split()[0],  # "Belmont"
#           case=False, na=False
#       )
#   ]
#   # Returns: Belmont Station Elementary, Belmont Ridge Middle (all schools containing "Belmont")
#   # Result: Multiple schools' data with same legend label = DUPLICATE LINES
#
# "WORKING" (but wrong data):
#   subject_match = match_school_in_performance_data("Belmont Ridge Middle", perf_df)
#   # Returns: "Belmont Station Elementary" (first match by file order)
#   subject_data = perf_df[perf_df['School_Name'] == "Belmont Station Elementary"]
#   # Result: One school's data = no duplicates, but WRONG SCHOOL DATA

# ============================================================
# Excerpt from lines 650-700 (Elementary School section)
# ============================================================

# School Performance Comparison with State Average and Peer Schools
if PLOTLY_AVAILABLE:
    with st.expander("📊 School Performance vs State & Peers", expanded=False):
        st.markdown("Compare assigned schools to Virginia state averages and nearest peer schools in Loudoun County.")

        try:
            # Load enhanced performance data with state averages
            perf_with_state_df = load_performance_with_state_avg()
            coords_df = load_school_coordinates()

            # Create school level tabs
            elem_tab, middle_tab, high_tab = st.tabs([
                "📚 Elementary School",
                "🎓 Middle School",
                "🏫 High School"
            ])

            # Elementary School Tab
            with elem_tab:
                if assignments.get('elementary'):
                    elem_school = assignments['elementary']
                    # Find 2 nearest peer elementary schools
                    elem_peers = find_peer_schools(
                        elem_school,
                        'Elem',
                        lat,
                        lon,
                        coords_df,
                        n=2
                    )

                    # Subject tabs for elementary
                    e_math, e_read, e_hist, e_sci, e_overall = st.tabs([
                        "Math", "Reading", "History", "Science", "Overall"
                    ])

                    with e_math:
                        # This call uses match_school_in_performance_data() internally
                        # which can return wrong school for names like "Belmont Ridge Middle"
                        fig = create_performance_chart(elem_school, elem_peers, "Math", "Math_Pass_Rate", "Elem", perf_with_state_df)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No math data available")

                    # ... similar pattern for other subjects and school levels
