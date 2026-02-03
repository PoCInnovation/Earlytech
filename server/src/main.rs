use axum::{routing::get, Router};

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(|| async { "Route principale" }))
        .route("/ping", get(|| async { "pong" }));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000")
        .await
        .unwrap();
    
    println!("Server sur http://localhost:3000");

    axum::serve(listener, app)
        .await
        .unwrap();
}
