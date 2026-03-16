mod db;
mod handlers;
mod models;
mod routes;
mod state;

use dotenv::dotenv;
use state::AppState;

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

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000")
        .await
        .unwrap();

    println!("Server sur http://localhost:3000");

    axum::serve(listener, app)
        .await
        .unwrap();
}
