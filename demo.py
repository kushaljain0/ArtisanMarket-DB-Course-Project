#!/usr/bin/env python3
"""
ArtisanMarket Demo Script
Demonstrates all implemented features of the polyglot persistence marketplace.
"""

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.services.search_service import SearchService
from src.services.cart_service import cart_service
from src.services.recommendation_service import recommendation_service

console = Console()


def demo_search_features():
    """Demonstrate search functionality."""
    console.print(Panel.fit("🔍 Search Features Demo", style="blue"))
    
    search_service = SearchService()
    
    # Full-text search
    console.print("\n[bold cyan]1. Full-text Search:[/bold cyan]")
    results = search_service.full_text_search("wooden bowl", limit=3)
    if results:
        table = Table(title="Full-text Search Results")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        
        for result in results:
            table.add_row(
                result['id'],
                result['name'][:40] + "..." if len(result['name']) > 40 else result['name'],
                f"${result['price']:.2f}"
            )
        console.print(table)
    
    # Semantic search
    console.print("\n[bold cyan]2. Semantic Search:[/bold cyan]")
    results = search_service.semantic_search("eco-friendly kitchenware", limit=3)
    if results:
        table = Table(title="Semantic Search Results")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Similarity", style="yellow")
        
        for result in results:
            table.add_row(
                result['id'],
                result['name'][:40] + "..." if len(result['name']) > 40 else result['name'],
                f"${result['price']:.2f}",
                f"{result.get('similarity', 0):.3f}"
            )
        console.print(table)
    
    # Combined search
    console.print("\n[bold cyan]3. Combined Search:[/bold cyan]")
    results = search_service.combined_search("handmade jewelry", limit=3)
    if results:
        table = Table(title="Combined Search Results")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        
        for result in results:
            table.add_row(
                result['id'],
                result['name'][:40] + "..." if len(result['name']) > 40 else result['name'],
                f"${result['price']:.2f}"
            )
        console.print(table)


def demo_cart_features():
    """Demonstrate shopping cart functionality."""
    console.print(Panel.fit("🛒 Shopping Cart Demo", style="blue"))
    
    user_id = "U001"
    
    # Add items to cart
    console.print(f"\n[bold cyan]Adding items to cart for user {user_id}:[/bold cyan]")
    
    products_to_add = [
        ("P001", 2),
        ("P003", 1),
        ("P005", 3)
    ]
    
    for product_id, quantity in products_to_add:
        success = cart_service.add_to_cart(user_id, product_id, quantity)
        if success:
            console.print(f"✅ Added {quantity}x {product_id} to cart")
        else:
            console.print(f"❌ Failed to add {product_id} to cart")
    
    # Show cart contents
    console.print(f"\n[bold cyan]Cart contents for user {user_id}:[/bold cyan]")
    cart_total = cart_service.get_cart_total(user_id)
    
    if cart_total['items']:
        table = Table(title=f"Shopping Cart - User {user_id}")
        table.add_column("Product", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Quantity", style="cyan")
        table.add_column("Total", style="yellow")
        
        for item in cart_total['items']:
            table.add_row(
                item['name'][:30] + "..." if len(item['name']) > 30 else item['name'],
                f"${item['price']:.2f}",
                str(item['quantity']),
                f"${item['total']:.2f}"
            )
        
        table.add_row("", "", "Total:", f"${cart_total['total']:.2f}", style="bold")
        console.print(table)
        
        # Show cart expiry
        expiry = cart_service.get_cart_expiry(user_id)
        if expiry:
            console.print(f"⏰ Cart expires in {expiry} seconds")
    else:
        console.print("Cart is empty")


def demo_recommendation_features():
    """Demonstrate recommendation functionality."""
    console.print(Panel.fit("🎯 Recommendation Features Demo", style="blue"))
    
    user_id = "U001"
    product_id = "P001"
    
    # User recommendations
    console.print(f"\n[bold cyan]Personalized recommendations for user {user_id}:[/bold cyan]")
    recommendations = recommendation_service.get_user_recommendations(user_id, limit=3)
    
    if recommendations:
        table = Table(title=f"Personalized Recommendations - User {user_id}")
        table.add_column("Product ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Frequency", style="yellow")
        
        for rec in recommendations:
            table.add_row(
                rec['product_id'],
                rec['name'][:30] + "..." if len(rec['name']) > 30 else rec['name'],
                f"${rec['price']:.2f}",
                str(rec['frequency'])
            )
        console.print(table)
    else:
        console.print("No personalized recommendations available")
    
    # Similar products
    console.print(f"\n[bold cyan]Similar products to {product_id}:[/bold cyan]")
    similar = recommendation_service.get_similar_products(product_id, limit=3)
    
    if similar:
        table = Table(title=f"Similar Products - {product_id}")
        table.add_column("Product ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Similarity", style="yellow")
        
        for sim in similar:
            table.add_row(
                sim['product_id'],
                sim['name'][:30] + "..." if len(sim['name']) > 30 else sim['name'],
                f"${sim['price']:.2f}",
                f"{sim['similarity']:.3f}"
            )
        console.print(table)
    else:
        console.print("No similar products found")
    
    # Frequently bought together
    console.print(f"\n[bold cyan]Frequently bought together with {product_id}:[/bold cyan]")
    together = recommendation_service.get_frequently_bought_together(product_id, limit=3)
    
    if together:
        table = Table(title=f"Frequently Bought Together - {product_id}")
        table.add_column("Product ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Frequency", style="yellow")
        
        for item in together:
            table.add_row(
                item['product_id'],
                item['name'][:30] + "..." if len(item['name']) > 30 else item['name'],
                f"${item['price']:.2f}",
                str(item['frequency'])
            )
        console.print(table)
    else:
        console.print("No frequently bought together data")


def demo_comprehensive_features():
    """Demonstrate comprehensive features."""
    console.print(Panel.fit("🚀 Comprehensive Features Demo", style="blue"))
    
    user_id = "U001"
    
    # Comprehensive recommendations
    console.print(f"\n[bold cyan]Comprehensive recommendations for user {user_id}:[/bold cyan]")
    comprehensive = recommendation_service.get_comprehensive_recommendations(user_id, limit=6)
    
    for rec_type, recommendations in comprehensive.items():
        if recommendations:
            console.print(f"\n[bold]{rec_type.title()} Recommendations:[/bold]")
            table = Table()
            table.add_column("Product ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Price", style="green")
            
            for rec in recommendations:
                table.add_row(
                    rec['product_id'],
                    rec['name'][:25] + "..." if len(rec['name']) > 25 else rec['name'],
                    f"${rec['price']:.2f}"
                )
            console.print(table)
    
    # Trending products
    console.print(f"\n[bold cyan]Trending products (last 30 days):[/bold cyan]")
    trending = recommendation_service.get_trending_products(days=30, limit=3)
    
    if trending:
        table = Table(title="Trending Products")
        table.add_column("Product ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Recent Purchases", style="yellow")
        
        for product in trending:
            table.add_row(
                product['product_id'],
                product['name'][:30] + "..." if len(product['name']) > 30 else product['name'],
                f"${product['price']:.2f}",
                str(product['recent_purchases'])
            )
        console.print(table)


def demo_system_status():
    """Show system status and database connections."""
    console.print(Panel.fit("📊 System Status", style="blue"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Check PostgreSQL
        task1 = progress.add_task("Checking PostgreSQL...", total=None)
        try:
            from src.db.postgres_client import db
            with db.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM products")
                product_count = cursor.fetchone()['count']
            progress.update(task1, description=f"✅ PostgreSQL: {product_count} products")
        except Exception as e:
            progress.update(task1, description=f"❌ PostgreSQL: {str(e)[:50]}...")
        
        # Check MongoDB
        task2 = progress.add_task("Checking MongoDB...", total=None)
        try:
            from src.db.mongodb_client import mongo_client
            review_count = mongo_client.get_collection("reviews").count_documents({})
            progress.update(task2, description=f"✅ MongoDB: {review_count} reviews")
        except Exception as e:
            progress.update(task2, description=f"❌ MongoDB: {str(e)[:50]}...")
        
        # Check Neo4j
        task3 = progress.add_task("Checking Neo4j...", total=None)
        try:
            from src.db.neo4j_client import neo4j_client
            with neo4j_client.driver.session() as session:
                result = session.run("MATCH (p:Product) RETURN count(p) as count")
                product_count = result.single()['count']
            progress.update(task3, description=f"✅ Neo4j: {product_count} product nodes")
        except Exception as e:
            progress.update(task3, description=f"❌ Neo4j: {str(e)[:50]}...")
        
        # Check Redis
        task4 = progress.add_task("Checking Redis...", total=None)
        try:
            from src.db.redis_client import redis_client
            redis_client.client.ping()
            progress.update(task4, description="✅ Redis: Connected")
        except Exception as e:
            progress.update(task4, description=f"❌ Redis: {str(e)[:50]}...")


def main():
    """Run the complete demo."""
    console.print(Panel.fit("🎨 ArtisanMarket - Polyglot Persistence Demo", style="bold blue"))
    console.print("This demo showcases all implemented features of the ArtisanMarket application.\n")
    
    # Show system status first
    demo_system_status()
    
    # Wait a moment
    time.sleep(1)
    
    # Run feature demos
    demo_search_features()
    time.sleep(1)
    
    demo_cart_features()
    time.sleep(1)
    
    demo_recommendation_features()
    time.sleep(1)
    
    demo_comprehensive_features()
    
    console.print(Panel.fit("🎉 Demo Complete!", style="bold green"))
    console.print("All features have been demonstrated successfully!")


if __name__ == "__main__":
    main() 