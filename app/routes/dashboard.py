from flask import Blueprint, jsonify
from app.extensions import db
from app.utils.logger import logger
from flask_jwt_extended import jwt_required, get_jwt
import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Retrieve overview statistics for the POS dashboard."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        
        start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_today_str = start_of_today.isoformat()
        start_yesterday_str = start_of_yesterday.isoformat()
        
        # Customers stats
        today_customers_count = db.customers.count_documents({"tenant_id": tenant_id, "createdAt": {"$gte": start_today_str}})
        yesterday_customers_count = db.customers.count_documents({"tenant_id": tenant_id, "createdAt": {"$gte": start_yesterday_str, "$lt": start_today_str}})
        
        # Orders stats today vs yesterday
        today_orders_cursor = db.orders.find({"tenant_id": tenant_id, "createdAt": {"$gte": start_today_str}})
        today_orders = list(today_orders_cursor)
        
        yesterday_orders_cursor = db.orders.find({"tenant_id": tenant_id, "createdAt": {"$gte": start_yesterday_str, "$lt": start_today_str}})
        yesterday_orders = list(yesterday_orders_cursor)
        
        today_revenue = sum(float(o.get('total', 0)) for o in today_orders)
        today_orders_count = len(today_orders)
        today_aov = (today_revenue / today_orders_count) if today_orders_count > 0 else 0
        
        yesterday_revenue = sum(float(o.get('total', 0)) for o in yesterday_orders)
        yesterday_orders_count = len(yesterday_orders)
        yesterday_aov = (yesterday_revenue / yesterday_orders_count) if yesterday_orders_count > 0 else 0
        
        def calc_change(today_val, yesterday_val):
            if yesterday_val == 0:
                if today_val > 0: return "+100%", "up"
                return "0%", "up"
            change = ((today_val - yesterday_val) / yesterday_val) * 100
            trend = "up" if change >= 0 else "down"
            return f"{'+' if change >= 0 else ''}{change:.1f}%", trend

        rev_change, rev_trend = calc_change(today_revenue, yesterday_revenue)
        ord_change, ord_trend = calc_change(today_orders_count, yesterday_orders_count)
        cust_change, cust_trend = calc_change(today_customers_count, yesterday_customers_count)
        aov_change, aov_trend = calc_change(today_aov, yesterday_aov)
        
        # Sales Data (Last 7 Days)
        start_7_days_ago = (today - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_orders = list(db.orders.find({"tenant_id": tenant_id, "createdAt": {"$gte": start_7_days_ago.isoformat()}}))
        
        last_7_dates = [(today - datetime.timedelta(days=i)).date() for i in range(6, -1, -1)]
        sales_by_date = {d.isoformat(): {"revenue": 0, "orders": 0} for d in last_7_dates}
            
        for o in recent_orders:
            date_str = o.get('createdAt', '')[:10]
            if date_str in sales_by_date:
                sales_by_date[date_str]['revenue'] += float(o.get('total', 0))
                sales_by_date[date_str]['orders'] += 1
                
        sales_data = [{"date": k, "revenue": v["revenue"], "orders": v["orders"]} for k,v in sales_by_date.items()]
        
        # Monthly Revenue (Last 7 Months)
        import calendar
        months_info = []
        for i in range(6, -1, -1):
            m = today.month - i
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            months_info.append(f"{y}-{m:02d}")
            
        # We need orders for the last 7 months. Let's just retrieve them all or query from start of 7 months ago
        first_month_str = months_info[0] + "-01T00:00:00"
        monthly_orders = list(db.orders.find({"tenant_id": tenant_id, "createdAt": {"$gte": first_month_str}}))
        
        monthly_map = {m: 0 for m in months_info}
        for o in monthly_orders:
            ym = o.get('createdAt', '')[:7]
            if ym in monthly_map:
                monthly_map[ym] += float(o.get('total', 0))
                
        monthly_revenue = []
        for ym, rev in monthly_map.items():
            y, m = ym.split('-')
            month_name = calendar.month_abbr[int(m)]
            monthly_revenue.append({"month": month_name, "revenue": rev})
            
        # Top Products (This Month)
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        this_month_orders = [o for o in monthly_orders if o.get('createdAt', '') >= start_of_month]
        
        product_stats = {}
        for o in this_month_orders:
            for item in o.get('items', []):
                p_name = item.get('product', {}).get('name', 'Unknown')
                qty = float(item.get('quantity', 0))
                price = float(item.get('product', {}).get('price', 0))
                
                item_total = qty * price
                if p_name not in product_stats:
                    product_stats[p_name] = {"revenue": 0, "units": 0}
                product_stats[p_name]["revenue"] += item_total
                product_stats[p_name]["units"] += qty
                
        top_products = [{"name": k, "revenue": v["revenue"], "units": v["units"]} for k,v in product_stats.items()]
        top_products = sorted(top_products, key=lambda x: x["revenue"], reverse=True)[:5]
        
        # Sales By Category (Overall from recent orders or today? Let's do today to match mock)
        products = list(db.products.find({"tenant_id": tenant_id}))
        product_categories = {str(p.get('_id')): p.get('category', 'Other') for p in products}
        
        category_map = {}
        for o in today_orders:
            for item in o.get('items', []):
                p_id = item.get('product', {}).get('id')
                cat = product_categories.get(p_id, 'Other')
                qty = float(item.get('quantity', 0))
                price = float(item.get('product', {}).get('price', 0))
                item_total = qty * price
                category_map[cat] = category_map.get(cat, 0) + item_total
                
        total_today_items_revenue = sum(category_map.values())
        sales_by_category = []
        for cat, rev in category_map.items():
            if total_today_items_revenue > 0:
                pct = round((rev / total_today_items_revenue) * 100, 1)
                if pct > 0:
                    sales_by_category.append({"name": cat.capitalize(), "value": pct})
                    
        if not sales_by_category:
             sales_by_category = [{"name": "No Sales", "value": 100}]

        return jsonify({
            "status": "success",
            "data": {
                "today_revenue": today_revenue,
                "revenue_change": rev_change,
                "revenue_trend": rev_trend,
                
                "today_orders": today_orders_count,
                "orders_change": ord_change,
                "orders_trend": ord_trend,
                
                "new_customers": today_customers_count,
                "customers_change": cust_change,
                "customers_trend": cust_trend,
                
                "avg_order_value": today_aov,
                "aov_change": aov_change,
                "aov_trend": aov_trend,
                
                "sales_data": sales_data,
                "monthly_revenue": monthly_revenue,
                "top_products": top_products,
                "sales_by_category": sales_by_category
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch dashboard statistics"}), 500
