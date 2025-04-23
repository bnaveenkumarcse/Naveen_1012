import streamlit as st
import pandas as pd
import plotly.express as px
from Main1 import *  # Make sure your helper functions are imported


st.set_page_config(layout="wide")
st.title("🛒 Sales Analytics Dashboard")


st.sidebar.header("📂 Upload CSV")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")
    feature_df = extract_column_features(df)
    quantity_col = feature_df[feature_df['has_keyword_quantity'] == 1]['column_name'].values[0]
    sales_col = feature_df[feature_df['has_keyword_sales'] == 1]['column_name'].values[0]
    product_col = feature_df[feature_df['has_keyword_product'] == 1]['column_name'].values[0]
    gender_col = feature_df[feature_df['has_keyword_gender'] == 1]['column_name'].values[0]
    date_col = get_valid_date_column(df, feature_df[feature_df['has_keyword_date'] == 1]['column_name'])

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

   
    col1, col2 = st.columns(2)
    _, avg_size = calculate_average_basket_size(df, quantity_col)
    _, avg_value = calculate_average_basket_value(df, sales_col)
    col1.metric("🧺 Avg Basket Size", avg_size)
    col2.metric("💰 Avg Basket Value", avg_value)

   
    st.markdown("---")
    st.markdown("## 📊 Visual Analysis")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📈 Monthly Sales Trend")
        df['Month'] = df[date_col].dt.to_period('M').astype(str)
        monthly_sales = df.groupby('Month')[sales_col].sum().reset_index()
        fig1 = px.line(monthly_sales, x='Month', y=sales_col, markers=True, title='Monthly Sales', template='plotly_dark')
        st.plotly_chart(fig1, use_container_width=True)

    with col4:
        st.subheader("📦 Sales by Category")
        monthly_cat = df.groupby(['Month', product_col])[sales_col].sum().reset_index()

        monthly_cat[sales_col] = monthly_cat[sales_col] / 1e6 

        fig2 = px.bar(monthly_cat, x='Month', y=sales_col, color=product_col, barmode='group',
                  title="Monthly Sales by Product", template='plotly_dark')
        fig2.update_yaxes(tickformat=".2f") 
        fig2.update_layout(
    bargap=0.1,  
    barmode='group'
)
 
        st.plotly_chart(fig2, use_container_width=True)
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("🧍‍♂️ Top Product by Gender")
        result = {}
        for gender in df[gender_col].dropna().unique():
            gender_df = df[df[gender_col] == gender]
            product_counts = gender_df.groupby(product_col)[quantity_col].sum()
            top_product = product_counts.idxmax()
            result[gender] = (top_product, int(product_counts.max()))
        gender_data = pd.DataFrame([(g, *v) for g, v in result.items()],
                                   columns=["Gender", "Product", "Count"])
        fig3 = px.bar(gender_data, x="Gender", y="Count", color="Product",
                      title="Most Purchased Product by Gender", template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)

    with col6:
        st.subheader("📅 Yearly Sales")
        df['Year'] = df[date_col].dt.year
        year_sales = df.groupby('Year')[sales_col].sum().reset_index()
        fig4 = px.bar(year_sales, x='Year', y=sales_col, title="Total Sales by Year", template='plotly_dark')
        st.plotly_chart(fig4, use_container_width=True)

    col7, col8 = st.columns(2)
    with col7:
        st.subheader("📆 Sales by Month Name")
        df['MonthName'] = df[date_col].dt.month_name()
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        df['MonthName'] = pd.Categorical(df['MonthName'], categories=month_order, ordered=True)
        month_sales = df.groupby('MonthName')[sales_col].sum().reset_index().sort_values('MonthName')
        fig5 = px.line(month_sales, x='MonthName', y=sales_col, markers=True,
                       title="Sales by Month (All Years)", template='plotly_dark')
        st.plotly_chart(fig5, use_container_width=True)

    with col8:
        st.subheader("🔺 Peak Sales Period")
        df['YearMonth'] = df[date_col].dt.to_period('M').astype(str)
        peak_df = df.groupby('YearMonth')[sales_col].sum().reset_index()
        peak_row = peak_df.loc[peak_df[sales_col].idxmax()]
        fig6 = px.bar(peak_df, x='YearMonth', y=sales_col, title="Monthly Sales with Peak", template="plotly_dark")
        fig6.add_vline(x=peak_df[peak_df['YearMonth'] == peak_row['YearMonth']].index[0],
                       line_color="red", line_dash="dash",
                       annotation_text=f"Peak: {peak_row['YearMonth']} ({peak_row[sales_col]})")
        st.plotly_chart(fig6, use_container_width=True)

else:
    st.info("⬅️ Upload a CSV file from the sidebar to get started.")
