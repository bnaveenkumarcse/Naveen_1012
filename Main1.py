import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st 


def extract_column_features(df, dataset_name="UploadedFile"):
    feature_list = []
    for col in df.columns:
        col_data = df[col]
        features = {
            'dataset': dataset_name,
            'column_name': col,
            'dtype': str(col_data.dtype),
            'sample_value': str(col_data.iloc[0]),
            'has_keyword_quantity': int('quantity' in col.lower() or 'count' in col.lower() or 'item' in col.lower()),
            'has_keyword_sales': int('amount' in col.lower() or 'price' in col.lower() or 'total' in col.lower() or 'value' in col.lower() or 'sales' in col.lower()),
            'has_keyword_product': int('product' in col.lower() or 'item' in col.lower() or 'category' in col.lower() or 'name' in col.lower()),
            'has_keyword_date': int(any(x in col.lower() for x in ['date', 'order', 'invoice', 'sale', 'placed'])),
            'has_keyword_gender': int('gender' in col.lower() or 'sex' in col.lower()),
            'is_numeric': pd.api.types.is_numeric_dtype(col_data),
            'mean_value': col_data.mean() if pd.api.types.is_numeric_dtype(col_data) else None,
            'unique_values': col_data.nunique(),
            'label': 'quantity' if col.lower() in ['quantity', 'items', 'count', 'number_of_items'] else 'not_quantity'
        }
        feature_list.append(features)
    return pd.DataFrame(feature_list)


def read_file(file_path):
    data = pd.read_csv(file_path)
    print("✅ File uploaded successfully!")
    return data


def get_columns_names(data):
    col_names = data.columns
    return f'This file contains the following column names: {col_names}'


def calculate_average_basket_size(df, quantity_col):
    df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce')
    total_items = df[quantity_col].sum()
    total_transactions = df[quantity_col].count()
    if total_transactions == 0:
        return "Avg_Basket_Size", 0
    avg_basket_size = total_items / total_transactions
    return "Avg_Basket_Size", round(avg_basket_size, 2)


def calculate_average_basket_value(df, sales_col):
    total_sales = df[sales_col].sum()
    total_transactions = len(df)
    avg_basket_value = total_sales / total_transactions
    return "Avg_Basket_Value", round(avg_basket_value, 2)


def most_frequent_product_by_gender(df, gender_col, product_col, quantity_col=None):
    result = {}
    for gender in df[gender_col].dropna().unique():
        gender_df = df[df[gender_col] == gender]
        if quantity_col and quantity_col in df.columns:
            product_counts = gender_df.groupby(product_col)[quantity_col].sum()
        else:
            product_counts = gender_df[product_col].value_counts()

        most_frequent_product = product_counts.idxmax()
        count = product_counts.max()
        result[gender] = (most_frequent_product, int(count))

    summary = pd.DataFrame([(g, *v) for g, v in result.items()], columns=["Gender", "Product", "Count"])
    fig = px.bar(summary, x="Gender", y="Count", color="Product", title="Most Frequently Purchased Products by Gender")
    st.plotly_chart(fig, use_container_width=True)

    st.write("\nMost Frequently Purchased Products by Gender:")
    for gender, (product, count) in result.items():
        st.write(f"{gender}: {product} (purchased {count} times)")


def get_valid_date_column(df, candidate_cols):
    for col in candidate_cols:
        try:
            converted = pd.to_datetime(df[col], errors='coerce')
            if converted.notna().sum() > 0:
                return col
        except:
            continue
    return None


def analyze_sales_trend(df, date_col, sales_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, sales_col])

    df['Month'] = df[date_col].dt.to_period('M').astype(str)  # ✅ Convert to string here
    monthly_sales = df.groupby('Month')[[sales_col]].sum().reset_index()

    if monthly_sales.empty or monthly_sales[sales_col].empty:
        st.warning("No sales data available to analyze.")
        return

    peak_row = monthly_sales.loc[monthly_sales[sales_col].idxmax()]
    st.write(f"📈 Peak Month: {peak_row['Month']}, Sales: {peak_row[sales_col]}")
    fig = px.line(
        monthly_sales,
        x='Month',
        y=sales_col,
        title='Monthly Sales Trend',
        markers=True,
        labels={sales_col: 'Sales', 'Month': 'Month'},
        template='plotly_dark'
    )
    fig.add_scatter(
        x=[peak_row['Month']],
        y=[peak_row[sales_col]],
        mode='markers+text',
        text=[f"Peak: {peak_row[sales_col]}"],
        textposition='top center',
        marker=dict(color='red', size=10),
        name='Peak Month'
    )

    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Sales',
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)
def monthly_sales_by_category(df, date_col, category_col, sales_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, category_col, sales_col])

    df['Month'] = df[date_col].dt.to_period('M').astype(str)
    monthly_category_sales = df.groupby(['Month', category_col])[sales_col].sum().reset_index()

    if monthly_category_sales.empty:
        st.warning("No valid sales data available for category analysis.")
        return
    peak_sales = monthly_category_sales.loc[monthly_category_sales.groupby('Month')[sales_col].idxmax()]

    fig = px.bar(
        monthly_category_sales,
        x='Month',
        y=sales_col,
        color=category_col,
        barmode='group',
        title="📊 Monthly Sales by Product Category",
        labels={sales_col: 'Sales', 'Month': 'Month'},
        template='plotly_dark'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.write("📋 Monthly Sales by Category:")
    st.dataframe(monthly_category_sales)

    return monthly_category_sales,peak_sales



def sales_by_year_and_month(df, date_col, sales_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month_name()

    sales_by_year = df.groupby('Year')[sales_col].sum().reset_index()
    sales_by_month = df.groupby('Month')[sales_col].sum().reset_index()

    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    sales_by_month['Month'] = pd.Categorical(sales_by_month['Month'], categories=month_order, ordered=True)
    sales_by_month = sales_by_month.sort_values('Month')

    fig1 = px.bar(sales_by_year, x='Year', y=sales_col, title="📈 Total Sales by Year")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(sales_by_month, x='Month', y=sales_col, markers=True,
                   title="📅 Total Sales by Month (Across All Years)")
    st.plotly_chart(fig2, use_container_width=True)

    st.write("\n📆 Total Sales by Year:")
    st.dataframe(sales_by_year)

    st.write("\n📅 Total Sales by Month (across years):")
    st.dataframe(sales_by_month)

    return sales_by_year, sales_by_month
def highest_sales_period(df, date_col, sales_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])

    df['YearMonth'] = df[date_col].dt.to_period('M').astype(str)

    sales_by_month = df.groupby('YearMonth')[sales_col].sum().reset_index()

    peak_row = sales_by_month.loc[sales_by_month[sales_col].idxmax()]
    peak_period = peak_row['YearMonth']
    peak_sales = peak_row[sales_col]

    peak_year, peak_month = peak_period.split('-')
    peak_month_name = pd.to_datetime(f'{peak_year}-{peak_month}-01').strftime('%B')

    fig = px.bar(
        sales_by_month,
        x='YearMonth',
        y=sales_col,
        title="📊 Monthly Sales with Peak Highlighted",
        labels={sales_col: "Total Sales", "YearMonth": "Month-Year"}
    )

    fig.add_vline(
        x=sales_by_month[sales_by_month['YearMonth'] == peak_period].index[0],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Peak: {peak_month_name} {peak_year} ({peak_sales})",
        annotation_position="top right"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.success(f"🔺 Highest Sales Recorded: {peak_month_name} {peak_year} → {peak_sales}")

    return peak_year, peak_month_name, peak_sales