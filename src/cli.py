"""Command-line interface for ArtisanMarket."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.loaders.relational_loader import RelationalLoader
from src.loaders.document_loader import DocumentLoader
from src.loaders.graph_loader import GraphLoader
from src.loaders.vector_loader import VectorLoader
from src.utils.purchase_generator import PurchaseGenerator
from src.services.search_service import SearchService
from src.services.cart_service import cart_service
from src.services.recommendation_service import recommendation_service
from src.services.order_service import order_service

console = Console()


@click.group()
def cli():
    """ArtisanMarket - Polyglot Persistence Project CLI."""
    pass


@cli.group()
def load():
    """Data loading commands."""
    pass


@load.command()
def relational():
    """Load data into PostgreSQL."""
    console.print(Panel.fit("Loading relational data into PostgreSQL...", style="blue"))
    try:
        loader = RelationalLoader()
        loader.load_all()
        console.print("✅ Relational data loaded successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error loading relational data: {e}", style="red")


@load.command()
def documents():
    """Load data into MongoDB."""
    console.print(Panel.fit("Loading document data into MongoDB...", style="blue"))
    try:
        loader = DocumentLoader()
        loader.load_all()
        console.print("✅ Document data loaded successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error loading document data: {e}", style="red")


@load.command()
def graph():
    """Load data into Neo4j."""
    console.print(Panel.fit("Loading graph data into Neo4j...", style="blue"))
    try:
        loader = GraphLoader()
        loader.load_all()
        console.print("✅ Graph data loaded successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error loading graph data: {e}", style="red")


@load.command()
def vectors():
    """Load vector embeddings into pgvector."""
    console.print(Panel.fit("Loading vector embeddings...", style="blue"))
    try:
        loader = VectorLoader()
        loader.load_all()
        console.print("✅ Vector embeddings loaded successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error loading vector embeddings: {e}", style="red")


@load.command()
def all():
    """Load all data into all databases."""
    console.print(Panel.fit("Loading all data into all databases...", style="blue"))

    try:
        # Load relational data
        console.print("📊 Loading relational data...")
        relational_loader = RelationalLoader()
        relational_loader.load_all()

        # Load document data
        console.print("📄 Loading document data...")
        document_loader = DocumentLoader()
        document_loader.load_all()

        # Load graph data
        console.print("🕸️ Loading graph data...")
        graph_loader = GraphLoader()
        graph_loader.load_all()

        # Load vector embeddings
        console.print("🧠 Loading vector embeddings...")
        vector_loader = VectorLoader()
        vector_loader.load_all()

        console.print("✅ All data loaded successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error loading data: {e}", style="red")


@cli.command()
@click.option("--count", default=100, help="Number of purchases to generate")
def generate_purchases(count):
    """Generate purchase history and load into databases."""
    console.print(Panel.fit(f"Generating {count} purchases...", style="blue"))
    try:
        generator = PurchaseGenerator()
        generator.generate_and_load_all(count)
        console.print(
            "✅ Purchase history generated and loaded successfully!", style="green"
        )
    except Exception as e:
        console.print(f"❌ Error generating purchases: {e}", style="red")


@cli.group()
def search():
    """Search functionality commands."""
    pass


@search.command()
@click.argument("query")
@click.option("--limit", default=5, help="Number of results to return")
def text(query, limit):
    """Perform full-text search."""
    console.print(Panel.fit(f"Searching for: '{query}'", style="blue"))
    try:
        service = SearchService()
        results = service.full_text_search(query, limit=limit)

        if results:
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Category", style="yellow")

            for result in results:
                table.add_row(
                    result["id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    result.get("category_id", "N/A"),
                )

            console.print(table)
        else:
            console.print("No results found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error performing search: {e}", style="red")


@search.command()
@click.argument("query")
@click.option("--limit", default=5, help="Number of results to return")
def semantic(query, limit):
    """Perform semantic search."""
    console.print(Panel.fit(f"Semantic search for: '{query}'", style="blue"))
    try:
        service = SearchService()
        results = service.semantic_search(query, limit=limit)

        if results:
            table = Table(title=f"Semantic Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Similarity", style="yellow")

            for result in results:
                table.add_row(
                    result["id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    f"{result.get('similarity', 0):.3f}",
                )

            console.print(table)
        else:
            console.print("No results found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error performing semantic search: {e}", style="red")


@search.command()
@click.argument("query")
@click.option("--limit", default=5, help="Number of results to return")
def combined(query, limit):
    """Perform combined search (text + semantic)."""
    console.print(Panel.fit(f"Combined search for: '{query}'", style="blue"))
    try:
        service = SearchService()
        results = service.combined_search(query, limit=limit)

        if results:
            table = Table(title=f"Combined Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Category", style="yellow")

            for result in results:
                table.add_row(
                    result["id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    result.get("category_id", "N/A"),
                )

            console.print(table)
        else:
            console.print("No results found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error performing combined search: {e}", style="red")


@cli.group()
def cart():
    """Shopping cart commands."""
    pass


@cart.command()
@click.argument("user_id")
def show_cart(user_id):
    """Show user's cart."""
    console.print(Panel.fit(f"Cart for user {user_id}", style="blue"))
    try:
        cart_total = cart_service.get_cart_total(user_id)

        if cart_total["items"]:
            table = Table(title=f"Shopping Cart - User {user_id}")
            table.add_column("Product", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Quantity", style="cyan")
            table.add_column("Total", style="yellow")

            for item in cart_total["items"]:
                table.add_row(
                    item["name"][:30] + "..."
                    if len(item["name"]) > 30
                    else item["name"],
                    f"${item['price']:.2f}",
                    str(item["quantity"]),
                    f"${item['total']:.2f}",
                )

            table.add_row("", "", "Total:", f"${cart_total['total']:.2f}", style="bold")
            console.print(table)
        else:
            console.print("Cart is empty.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error showing cart: {e}", style="red")


@cart.command()
@click.argument("user_id")
@click.argument("product_id")
@click.option("--quantity", default=1, help="Quantity to add")
def add(user_id, product_id, quantity):
    """Add item to cart."""
    console.print(
        Panel.fit(
            f"Adding {quantity}x {product_id} to cart for user {user_id}", style="blue"
        )
    )
    try:
        success = cart_service.add_to_cart(user_id, product_id, quantity)
        if success:
            console.print("✅ Item added to cart successfully!", style="green")
        else:
            console.print("❌ Failed to add item to cart.", style="red")
    except Exception as e:
        console.print(f"❌ Error adding to cart: {e}", style="red")


@cli.group()
def recommend():
    """Recommendation commands."""
    pass


@cli.group()
def orders():
    """Order management commands."""
    pass


@orders.command()
@click.argument("user_id")
@click.option("--limit", default=10, help="Number of orders to show")
def history(user_id, limit):
    """Show user's order history."""
    try:
        orders = order_service.get_user_orders(user_id, limit=limit)
        if not orders:
            console.print(f"❌ No orders found for user {user_id}", style="red")
            return

        console.print(f"✅ Order history for {user_id}:", style="green")
        for order in orders:
            console.print(
                f"  • Order #{order['id']} - ${order['total_amount']} ({order['status']}) - {order['item_count']} items"
            )
            for item in order["items"]:
                console.print(
                    f"    - {item['product_name']} x{item['quantity']} @ ${item['unit_price']}"
                )
    except Exception as e:
        console.print(f"❌ Error getting order history: {e}", style="red")


@orders.command()
@click.argument("order_id", type=int)
def show(order_id):
    """Show order details."""
    try:
        order = order_service.get_order(order_id)
        if not order:
            console.print(f"❌ Order {order_id} not found", style="red")
            return

        console.print(f"✅ Order #{order_id} details:", style="green")
        console.print(f"  Customer: {order['user_name']} ({order['email']})")
        console.print(f"  Status: {order['status']}")
        console.print(f"  Total: ${order['total_amount']}")
        console.print(f"  Created: {order['created_at']}")
        console.print("  Items:")
        for item in order["items"]:
            console.print(
                f"    - {item['product_name']} x{item['quantity']} @ ${item['unit_price']} = ${item['total_price']}"
            )
    except Exception as e:
        console.print(f"❌ Error getting order details: {e}", style="red")


@orders.command()
@click.argument("order_id", type=int)
@click.argument("status")
def update_status(order_id, status):
    """Update order status."""
    try:
        success = order_service.update_order_status(order_id, status)
        if success:
            console.print(
                f"✅ Order {order_id} status updated to '{status}'", style="green"
            )
        else:
            console.print(f"❌ Failed to update order {order_id} status", style="red")
    except Exception as e:
        console.print(f"❌ Error updating order status: {e}", style="red")


@orders.command()
@click.argument("order_id", type=int)
@click.argument("user_id")
def cancel(order_id, user_id):
    """Cancel an order."""
    try:
        success = order_service.cancel_order(order_id, user_id)
        if success:
            console.print(f"✅ Order {order_id} cancelled successfully", style="green")
        else:
            console.print(f"❌ Failed to cancel order {order_id}", style="red")
    except Exception as e:
        console.print(f"❌ Error cancelling order: {e}", style="red")


@orders.command()
@click.argument("user_id")
def stats(user_id):
    """Show user's order statistics."""
    try:
        stats = order_service.get_order_statistics(user_id)
        if not stats:
            console.print(
                f"❌ No order statistics found for user {user_id}", style="red"
            )
            return

        console.print(f"✅ Order statistics for {user_id}:", style="green")
        console.print(f"  Total orders: {stats['total_orders']}")
        console.print(f"  Total spent: ${stats['total_spent']}")
        console.print(f"  Average order value: ${stats['avg_order_value']}")
        console.print(f"  Last order: {stats['last_order_date']}")
        console.print("  Top products:")
        for product in stats["top_products"]:
            console.print(
                f"    - {product['name']} (Quantity: {product['total_quantity']})"
            )
    except Exception as e:
        console.print(f"❌ Error getting order statistics: {e}", style="red")


@orders.command()
@click.option("--limit", default=10, help="Number of recent orders to show")
def recent(limit):
    """Show recent orders across all users."""
    try:
        orders = order_service.get_recent_orders(limit=limit)
        if not orders:
            console.print("❌ No recent orders found", style="red")
            return

        console.print(f"✅ Recent orders (last {limit}):", style="green")
        for order in orders:
            console.print(
                f"  • Order #{order['id']} - {order['user_name']} - ${order['total_amount']} ({order['status']})"
            )
    except Exception as e:
        console.print(f"❌ Error getting recent orders: {e}", style="red")


@orders.command()
def analytics():
    """Show order analytics dashboard."""
    try:
        analytics = order_service.get_order_analytics()
        if not analytics:
            console.print("❌ No analytics data available", style="red")
            return

        console.print("✅ Order Analytics Dashboard:", style="green")
        console.print(f"  Total orders: {analytics['total_orders']}")
        console.print(f"  Total revenue: ${analytics['total_revenue']}")
        console.print(f"  Average order value: ${analytics['avg_order_value']}")

        console.print("  Status breakdown:")
        for status in analytics["status_breakdown"]:
            console.print(f"    - {status['status']}: {status['count']} orders")

        console.print("  Top selling products:")
        for product in analytics["top_products"][:5]:  # Show top 5
            console.print(f"    - {product['name']}: {product['total_sold']} units")

        console.print("  Recent daily trends:")
        for trend in analytics["daily_trends"][:7]:  # Show last 7 days
            console.print(
                f"    - {trend['date']}: {trend['orders']} orders, ${trend['revenue']} revenue"
            )
    except Exception as e:
        console.print(f"❌ Error getting analytics: {e}", style="red")


@recommend.command()
@click.argument("user_id")
@click.option("--limit", default=5, help="Number of recommendations")
def user(user_id, limit):
    """Get personalized recommendations for user."""
    console.print(Panel.fit(f"Recommendations for user {user_id}", style="blue"))
    try:
        results = recommendation_service.get_user_recommendations(user_id, limit)

        if results:
            table = Table(title=f"Personalized Recommendations - User {user_id}")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Frequency", style="yellow")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    str(result["frequency"]),
                )

            console.print(table)
        else:
            console.print("No recommendations available.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting recommendations: {e}", style="red")


@recommend.command()
@click.argument("product_id")
@click.option("--limit", default=5, help="Number of recommendations")
def similar(product_id, limit):
    """Get similar products."""
    console.print(Panel.fit(f"Similar products to {product_id}", style="blue"))
    try:
        results = recommendation_service.get_similar_products(product_id, limit)

        if results:
            table = Table(title=f"Similar Products - {product_id}")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Similarity", style="yellow")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    f"{result['similarity']:.3f}",
                )

            console.print(table)
        else:
            console.print("No similar products found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting similar products: {e}", style="red")


@recommend.command()
@click.argument("product_id")
@click.option("--limit", default=5, help="Number of recommendations")
def frequently_bought_together(product_id, limit):
    """Get products frequently bought together."""
    console.print(Panel.fit(f"Frequently bought together with {product_id}", style="blue"))
    try:
        results = recommendation_service.get_frequently_bought_together(product_id, limit)

        if results:
            table = Table(title=f"Frequently Bought Together - {product_id}")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Frequency", style="yellow")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    str(result["frequency"]),
                )

            console.print(table)
        else:
            console.print("No frequently bought together products found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting frequently bought together: {e}", style="red")


@recommend.command()
@click.option("--days", default=30, help="Number of days to look back")
@click.option("--limit", default=10, help="Number of recommendations")
def trending(days, limit):
    """Get trending products based on recent purchases."""
    console.print(Panel.fit(f"Trending products (last {days} days)", style="blue"))
    try:
        results = recommendation_service.get_trending_products(days, limit)

        if results:
            table = Table(title=f"Trending Products - Last {days} Days")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Recent Purchases", style="yellow")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    str(result["recent_purchases"]),
                )

            console.print(table)
        else:
            console.print("No trending products found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting trending products: {e}", style="red")


@recommend.command()
@click.argument("user_id")
@click.option("--limit", default=10, help="Number of items to show")
def purchase_history(user_id, limit):
    """Get user's purchase history."""
    console.print(Panel.fit(f"Purchase history for user {user_id}", style="blue"))
    try:
        results = recommendation_service.get_user_purchase_history(user_id, limit)

        if results:
            table = Table(title=f"Purchase History - User {user_id}")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("Quantity", style="yellow")
            table.add_column("Purchase Date", style="blue")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:25] + "..."
                    if len(result["name"]) > 25
                    else result["name"],
                    f"${result['price']:.2f}",
                    str(result["quantity"]),
                    result["purchase_date"],
                )

            console.print(table)
        else:
            console.print("No purchase history found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting purchase history: {e}", style="red")


@recommend.command()
@click.argument("product_id")
@click.option("--limit", default=5, help="Number of recommendations")
def also_bought(product_id, limit):
    """Get 'users who bought this also bought' recommendations."""
    console.print(Panel.fit(f"Users who bought {product_id} also bought", style="blue"))
    try:
        results = recommendation_service.get_also_bought_recommendations(product_id, limit)

        if results:
            table = Table(title=f"Also Bought - {product_id}")
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            table.add_column("User Count", style="yellow")

            for result in results:
                table.add_row(
                    result["product_id"],
                    result["name"][:30] + "..."
                    if len(result["name"]) > 30
                    else result["name"],
                    f"${result['price']:.2f}",
                    str(result["user_count"]),
                )

            console.print(table)
        else:
            console.print("No 'also bought' recommendations found.", style="yellow")
    except Exception as e:
        console.print(f"❌ Error getting 'also bought' recommendations: {e}", style="red")


@cli.command()
def status():
    """Show system status."""
    console.print(Panel.fit("System Status", style="blue"))

    # Check database connections
    try:
        from src.db.postgres_client import db

        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM products")
            product_count = cursor.fetchone()["count"]
        console.print(f"✅ PostgreSQL: {product_count} products", style="green")
    except Exception as e:
        console.print(f"❌ PostgreSQL: {e}", style="red")

    try:
        from src.db.mongodb_client import mongo_client

        review_count = mongo_client.get_collection("reviews").count_documents({})
        console.print(f"✅ MongoDB: {review_count} reviews", style="green")
    except Exception as e:
        console.print(f"❌ MongoDB: {e}", style="red")

    try:
        from src.db.neo4j_client import neo4j_client

        with neo4j_client.driver.session() as session:
            result = session.run("MATCH (p:Product) RETURN count(p) as count")
            product_count = result.single()["count"]
        console.print(f"✅ Neo4j: {product_count} product nodes", style="green")
    except Exception as e:
        console.print(f"❌ Neo4j: {e}", style="red")

    try:
        from src.db.redis_client import redis_client

        redis_client.client.ping()
        console.print("✅ Redis: Connected", style="green")
    except Exception as e:
        console.print(f"❌ Redis: {e}", style="red")


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
