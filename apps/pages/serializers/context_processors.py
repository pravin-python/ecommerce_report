def context_label(request=None):
    CONTEXT = {
        # customers
        'customers_chart': 'Customer Chart',
        'customers_table': 'Customer Table',
        'customer_scanned_products_chart': 'Customer Scanned Chart',
        'customer_scanned_products_table': 'Customer Scanned Table',
        'leaderboard_summary_table': 'Customer Leaderboard Table',

        # products
        'most_top_10_scan_products_table': 'Customer Scanned Most Top 10 Products',
        'customer': 'Customers',
    }
    return {
        "context": CONTEXT
    }

def context_data(request=None):
    data = {'customer_scanned_products_chart':{

            }
            
        }
    return data