mod db;
mod handlers;
mod models;
mod routes;
mod state;

use dotenv::dotenv;
use state::AppState;
use std::env;

#[tokio::main]
async fn main() {
    dotenv().ok();

    let pool = db::establish_connection().await;
    
    // Run migrations (commented out - tables managed by Python scraper)
    // sqlx::migrate!("./migrations")
    //     .run(&pool)
    //     .await
    //     .expect("Failed to run migrations");

    let state = AppState { pool };

    let app = routes::create_router(state);

    let host = env::var("APP_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let bind_addr = format!("{}:{}", host, port);

    let listener = tokio::net::TcpListener::bind(&bind_addr)
        .await
        .unwrap();

    println!("Server sur http://{}", bind_addr);

    axum::serve(listener, app)
        .await
        .unwrap();
}
